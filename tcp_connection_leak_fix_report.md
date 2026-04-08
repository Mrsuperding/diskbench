# TCP 连接泄漏修复报告

## 问题描述

后端 5003 端口出现大量 TCP 连接处于 `TIME_WAIT` 状态，原因是数据库操作中频繁创建和释放连接。

## 问题根因

1. `collect_space_metrics` API：每个节点单独调用 `save_metrics()` 并执行 `db.session.commit()`
2. `collect_partition_metrics` API：每个节点单独调用 `save_partition_metrics()`，每次内部又对每个分区执行 `db.session.commit()`
3. `collect_all_metrics` 定时任务（每30秒）：对每个节点单独 commit
4. `save_partition_metrics` 方法：对每个分区单独 commit

---

## 修复详情

### 1. `backend/app/services/metric_collector.py`

#### 修复前代码

```python
@staticmethod
def save_partition_metrics(node_id, partition_metrics):
    """
    保存分区指标到SystemMetric表

    Args:
        node_id: 节点ID
        partition_metrics: 分区指标字典，键为分区名称，值为指标字典
    """
    for partition_name, metrics in partition_metrics.items():
        MetricCollector.save_metrics(node_id, metrics, partition_name=partition_name)
```

#### 修复后代码

```python
@staticmethod
def save_partition_metrics(node_id, partition_metrics):
    """
    保存分区指标到SystemMetric表（批量操作，减少数据库连接开销）

    Args:
        node_id: 节点ID
        partition_metrics: 分区指标字典，键为分区名称，值为指标字典
    """
    from app.models.system_metric import SystemMetric
    from app.models import db

    # 批量添加所有指标，最后一次性commit
    for partition_name, metrics in partition_metrics.items():
        for metric_name, value in metrics.items():
            unit = None
            if 'usage' in metric_name or 'utilization' in metric_name:
                unit = '%'
            elif 'throughput' in metric_name:
                unit = 'B/s'
            elif 'latency' in metric_name:
                unit = 'ms'
            elif 'iops' in metric_name:
                unit = 'ops'

            metric = SystemMetric(
                node_id=node_id,
                metric_type='partition',
                metric_name=metric_name,
                metric_value=float(value),
                metric_unit=unit,
                partition_name=partition_name,
                collection_time=datetime.utcnow()
            )
            db.session.add(metric)

    # 一次性提交所有分区指标
    db.session.commit()
```

---

### 2. `backend/application.py` - `collect_all_metrics` 定时任务

#### 修复前代码

```python
def collect_all_metrics():
    """定时任务：采集所有环境空间内节点的指标"""
    from app.models.environment_space import EnvironmentSpace
    from app.services.metric_collector import MetricCollector

    with app.app_context():
        try:
            spaces = EnvironmentSpace.get_all_active()
            app.logger.info(f'开始采集 {len(spaces)} 个环境空间的监控指标')

            total_nodes = 0
            for space in spaces:
                nodes = space.nodes
                total_nodes += len(nodes)

                for node in nodes:
                    try:
                        metrics = MetricCollector.collect_node_metrics(node.id)
                        MetricCollector.save_metrics(node.id, metrics)  # 每次单独commit

                        if not metrics.get('is_connected'):
                            node.status = 'inactive'
                        else:
                            node.status = 'active'
                        db.session.commit()  # 每个节点单独commit

                    except Exception as e:
                        app.logger.error(f'采集节点 {node.id} ({node.name}) 指标失败: {e}')

            app.logger.info(f'指标采集完成: {len(spaces)} 个环境空间, {total_nodes} 个节点')
        except Exception as e:
            app.logger.error(f'采集任务执行失败: {e}')
```

#### 修复后代码

```python
def collect_all_metrics():
    """定时任务：采集所有环境空间内节点的指标"""
    from app.models.environment_space import EnvironmentSpace
    from app.models.node import Node
    from app.services.metric_collector import MetricCollector
    from app.models.system_metric import SystemMetric

    with app.app_context():
        try:
            spaces = EnvironmentSpace.get_all_active()
            app.logger.info(f'开始采集 {len(spaces)} 个环境空间的监控指标')

            total_nodes = 0
            metrics_batch = []  # 批量收集指标
            node_status_updates = []  # 收集节点状态更新

            for space in spaces:
                nodes = space.nodes
                total_nodes += len(nodes)

                for node in nodes:
                    try:
                        metrics = MetricCollector.collect_node_metrics(node.id)

                        # 收集指标数据用于批量保存
                        for metric_name, value in metrics.items():
                            if metric_name == 'is_connected':
                                value = 1.0 if value else 0.0

                            if metric_name == 'load_average' and isinstance(value, list):
                                for i, load_val in enumerate(value[:3]):
                                    metrics_batch.append({
                                        'node_id': node.id,
                                        'metric_type': 'system',
                                        'metric_name': f'load_average_{["1min", "5min", "15min"][i]}',
                                        'metric_value': float(load_val),
                                        'metric_unit': None,
                                        'collection_time': datetime.utcnow()
                                    })
                            else:
                                unit = None
                                if 'usage' in metric_name:
                                    unit = '%'
                                elif metric_name in ['network_tx', 'network_rx']:
                                    unit = 'B/s'

                                metrics_batch.append({
                                    'node_id': node.id,
                                    'metric_type': 'system',
                                    'metric_name': metric_name,
                                    'metric_value': float(value) if metric_name != 'is_connected' else value,
                                    'metric_unit': unit,
                                    'collection_time': datetime.utcnow()
                                })

                        node_status = 'active' if metrics.get('is_connected') else 'inactive'
                        node_status_updates.append((node.id, node_status))

                    except Exception as e:
                        app.logger.error(f'采集节点 {node.id} ({node.name}) 指标失败: {e}')

            # 批量保存所有指标（一次性commit）
            if metrics_batch:
                db.session.bulk_insert_mappings(SystemMetric, metrics_batch)

            # 批量更新节点状态
            for node_id, status in node_status_updates:
                db.session.query(Node).filter_by(id=node_id).update({'status': status})

            # 一次性提交
            db.session.commit()

            app.logger.info(f'指标采集完成: {len(spaces)} 个环境空间, {total_nodes} 个节点')
        except Exception as e:
            app.logger.error(f'采集任务执行失败: {e}')
            db.session.rollback()
```

---

### 3. `backend/app/views/environment_spaces.py` - `collect_space_metrics` API

#### 修复前代码

```python
@environment_spaces_bp.route('/<int:space_id>/metrics/collect', methods=['POST'])
@jwt_required()
def collect_space_metrics(space_id):
    """手动触发环境空间内所有节点的监控数据采集"""
    try:
        space = EnvironmentSpace.query.get(space_id)
        if not space:
            return error_response('环境空间不存在', 404)

        from app.services.metric_collector import MetricCollector

        success_count = 0
        failed_count = 0
        nodes = space.nodes

        for node in nodes:
            try:
                metrics = MetricCollector.collect_node_metrics(node.id)
                MetricCollector.save_metrics(node.id, metrics)  # 每次单独commit
                success_count += 1
            except Exception as e:
                failed_count += 1
                print(f'采集节点 {node.id} 指标失败: {e}')

        return success_response({
            'total': len(nodes),
            'success': success_count,
            'failed': failed_count
        }, f'采集完成: 成功 {success_count}, 失败 {failed_count}')
    except Exception as e:
        db.session.rollback()
        return error_response(f'采集监控数据失败: {str(e)}', 500)
```

#### 修复后代码

```python
@environment_spaces_bp.route('/<int:space_id>/metrics/collect', methods=['POST'])
@jwt_required()
def collect_space_metrics(space_id):
    """手动触发环境空间内所有节点的监控数据采集"""
    try:
        space = EnvironmentSpace.query.get(space_id)
        if not space:
            return error_response('环境空间不存在', 404)

        from app.services.metric_collector import MetricCollector
        from app.models.system_metric import SystemMetric

        success_count = 0
        failed_count = 0
        nodes = space.nodes
        all_metrics_batch = []  # 批量收集所有指标

        for node in nodes:
            try:
                metrics = MetricCollector.collect_node_metrics(node.id)

                # 收集指标数据用于批量保存
                for metric_name, value in metrics.items():
                    if metric_name == 'is_connected':
                        value = 1.0 if value else 0.0

                    if metric_name == 'load_average' and isinstance(value, list):
                        for i, load_val in enumerate(value[:3]):
                            all_metrics_batch.append({
                                'node_id': node.id,
                                'metric_type': 'system',
                                'metric_name': f'load_average_{["1min", "5min", "15min"][i]}',
                                'metric_value': float(load_val),
                                'metric_unit': None,
                                'collection_time': datetime.utcnow()
                            })
                    else:
                        unit = None
                        if 'usage' in metric_name:
                            unit = '%'
                        elif metric_name in ['network_tx', 'network_rx']:
                            unit = 'B/s'

                        all_metrics_batch.append({
                            'node_id': node.id,
                            'metric_type': 'system',
                            'metric_name': metric_name,
                            'metric_value': float(value) if metric_name != 'is_connected' else value,
                            'metric_unit': unit,
                            'collection_time': datetime.utcnow()
                        })

                success_count += 1
            except Exception as e:
                failed_count += 1
                print(f'采集节点 {node.id} 指标失败: {e}')

        # 批量保存所有指标（一次性commit）
        if all_metrics_batch:
            db.session.bulk_insert_mappings(SystemMetric, all_metrics_batch)
            db.session.commit()

        return success_response({
            'total': len(nodes),
            'success': success_count,
            'failed': failed_count
        }, f'采集完成: 成功 {success_count}, 失败 {failed_count}')
    except Exception as e:
        db.session.rollback()
        return error_response(f'采集监控数据失败: {str(e)}', 500)
```

---

### 4. `backend/app/views/environment_spaces.py` - `collect_partition_metrics` API

#### 修复前代码

```python
@environment_spaces_bp.route('/<int:space_id>/metrics/partition/collect', methods=['POST'])
@jwt_required()
def collect_partition_metrics(space_id):
    """手动触发环境空间内所有节点分区监控数据采集（秒级粒度）"""
    try:
        space = EnvironmentSpace.query.get(space_id)
        if not space:
            return error_response('环境空间不存在', 404)

        from app.services.metric_collector import MetricCollector

        success_count = 0
        failed_count = 0
        skipped_count = 0
        nodes = space.nodes

        for node in nodes:
            try:
                if not node.io_partitions or len(node.io_partitions) == 0:
                    skipped_count += 1
                    continue

                # 采集分区指标
                partition_metrics = MetricCollector.collect_partition_metrics(node.id, node.io_partitions)
                MetricCollector.save_partition_metrics(node.id, partition_metrics)  # 内部每个分区单独commit
                success_count += 1
            except Exception as e:
                failed_count += 1
                print(f'采集节点 {node.id} 分区指标失败: {e}')

        return success_response({
            'total': len(nodes),
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count
        }, f'分区指标采集完成: 成功 {success_count}, 失败 {failed_count}, 跳过 {skipped_count}')
    except Exception as e:
        db.session.rollback()
        return error_response(f'采集分区监控数据失败: {str(e)}', 500)
```

#### 修复后代码

```python
@environment_spaces_bp.route('/<int:space_id>/metrics/partition/collect', methods=['POST'])
@jwt_required()
def collect_partition_metrics(space_id):
    """手动触发环境空间内所有节点分区监控数据采集（秒级粒度）"""
    try:
        space = EnvironmentSpace.query.get(space_id)
        if not space:
            return error_response('环境空间不存在', 404)

        from app.services.metric_collector import MetricCollector
        from app.models.system_metric import SystemMetric

        success_count = 0
        failed_count = 0
        skipped_count = 0
        nodes = space.nodes
        all_metrics_batch = []  # 批量收集所有指标

        for node in nodes:
            try:
                if not node.io_partitions or len(node.io_partitions) == 0:
                    skipped_count += 1
                    continue

                partition_metrics = MetricCollector.collect_partition_metrics(node.id, node.io_partitions)

                # 收集指标数据用于批量保存
                for partition_name, metrics in partition_metrics.items():
                    for metric_name, value in metrics.items():
                        unit = None
                        if 'usage' in metric_name or 'utilization' in metric_name:
                            unit = '%'
                        elif 'throughput' in metric_name:
                            unit = 'B/s'
                        elif 'latency' in metric_name:
                            unit = 'ms'
                        elif 'iops' in metric_name:
                            unit = 'ops'

                        all_metrics_batch.append({
                            'node_id': node.id,
                            'metric_type': 'partition',
                            'metric_name': metric_name,
                            'metric_value': float(value),
                            'metric_unit': unit,
                            'partition_name': partition_name,
                            'collection_time': datetime.utcnow()
                        })

                success_count += 1
            except Exception as e:
                failed_count += 1
                print(f'采集节点 {node.id} 分区指标失败: {e}')

        # 批量保存所有指标（一次性commit）
        if all_metrics_batch:
            db.session.bulk_insert_mappings(SystemMetric, all_metrics_batch)
            db.session.commit()

        return success_response({
            'total': len(nodes),
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count
        }, f'分区指标采集完成: 成功 {success_count}, 失败 {failed_count}, 跳过 {skipped_count}')
    except Exception as e:
        db.session.rollback()
        return error_response(f'采集分区监控数据失败: {str(e)}', 500)
```

---

## 修复效果

| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| 10节点系统指标采集 | 10+ 次 commit | 1 次 commit |
| 10节点分区采集(各3分区) | 30+ 次 commit | 1 次 commit |
| 定时任务(每30秒, N个节点) | N×10 次 commit | 1 次 commit |

## 验证方法

```bash
# 查看 TIME_WAIT 连接数
netstat -an | grep TIME_WAIT | grep 3306 | wc -l

# 或查看 MySQL 连接数
mysql -u root -p123456 -e "SHOW STATUS LIKE 'Threads_connected';"

# 重启后观察连接数是否稳定
```

## 修改文件清单

1. `backend/app/services/metric_collector.py` - `save_partition_metrics` 方法
2. `backend/application.py` - `collect_all_metrics` 定时任务
3. `backend/app/views/environment_spaces.py` - `collect_space_metrics` API
4. `backend/app/views/environment_spaces.py` - `collect_partition_metrics` API
