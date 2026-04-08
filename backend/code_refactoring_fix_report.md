# 代码优化与修复报告

## 修复日期
2026-04-04

## 修复内容概览

| 问题 | 修复文件 | 状态 |
|------|----------|------|
| datetime.utcnow() 废弃警告 | 多个文件 | ✅ 已修复 |
| 代码重复（批量插入逻辑） | SystemMetric 模型 | ✅ 已修复 |
| 定时任务超时控制 | application.py | ✅ 已修复 |
| 任务并发数限制 | tasks.py | ✅ 已修复 |
| 失败节点处理 | environment_spaces.py | ✅ 已修复 |

---

## 1. datetime.utcnow() 废弃问题

### 问题描述

Python 3.12+ 已废弃 `datetime.utcnow()`，使用会收到警告：
```
DeprecationWarning: datetime.datetime.utcnow() is deprecated.
Use datetime.datetime.now(datetime.UTC) instead.
```

### 修复方案

创建统一时间工具模块 `app/utils/datetime_utils.py`：

```python
# app/utils/datetime_utils.py
from datetime import datetime, timezone

def utc_now():
    """获取当前 UTC 时间（timezone-aware）"""
    return datetime.now(timezone.utc)
```

### 修复的文件

| 文件 | 修改内容 |
|------|----------|
| `app/models/system_metric.py` | `default=datetime.utcnow` → `default=utc_now` |
| `app/views/environment_spaces.py` | `datetime.utcnow()` → `datetime.now(timezone.utc)` |
| `application.py` | `datetime.utcnow()` → `datetime.now(timezone.utc)` |

---

## 2. 批量插入逻辑封装

### 问题描述

API 和定时任务中重复编写批量插入逻辑：

```python
# 重复的代码
for metric_name, value in metrics.items():
    if metric_name == 'is_connected':
        value = 1.0 if value else 0.0
    # ... 更多重复逻辑
    all_metrics_batch.append({...})
```

### 修复方案

在 `SystemMetric` 模型中添加批量插入方法：

```python
# app/models/system_metric.py

@classmethod
def bulk_insert_system_metrics(cls, node_id, metrics, collection_time=None):
    """批量插入单个节点的系统指标"""
    if collection_time is None:
        collection_time = utc_now()

    mappings = []
    for metric_name, value in metrics.items():
        if metric_name == 'is_connected':
            value = 1.0 if value else 0.0

        if metric_name == 'load_average' and isinstance(value, list):
            for i, load_val in enumerate(value[:3]):
                mappings.append({
                    'node_id': node_id,
                    'metric_type': 'system',
                    'metric_name': f'load_average_{["1min", "5min", "15min"][i]}',
                    'metric_value': float(load_val),
                    'metric_unit': None,
                    'collection_time': collection_time
                })
        else:
            # ... 处理其他指标
            mappings.append({...})

    if mappings:
        db.session.bulk_insert_mappings(cls, mappings)

    return len(mappings)

@classmethod
def bulk_insert_partition_metrics(cls, node_id, partition_metrics, collection_time=None):
    """批量插入节点分区指标"""
    # ... 类似实现

@classmethod
def bulk_insert_metrics_batch(cls, metrics_list):
    """批量插入任意指标数据列表"""
    if not metrics_list:
        return 0
    db.session.bulk_insert_mappings(cls, metrics_list)
    return len(metrics_list)
```

### 修复后的 API 代码

```python
# app/views/environment_spaces.py

@environment_spaces_bp.route('/<int:space_id>/metrics/collect', methods=['POST'])
def collect_space_metrics(space_id):
    # ... 简化后的代码
    for node in nodes:
        try:
            metrics = MetricCollector.collect_node_metrics(node.id)
            inserted = SystemMetric.bulk_insert_system_metrics(node.id, metrics)
            success_count += 1
        except Exception as e:
            failed_count += 1
            failed_nodes.append({'node_id': node.id, 'node_name': node.name, 'error': str(e)})

    db.session.commit()
```

---

## 3. 定时任务超时控制

### 问题描述

`collect_all_metrics` 定时任务没有超时控制，可能导致：
- 任务卡死时无法自动恢复
- 与下一次任务重叠执行

### 修复方案

```python
# application.py

def collect_all_metrics():
    import signal

    # 超时控制：25秒后强制终止
    def timeout_handler(signum, frame):
        raise TimeoutError("采集任务超时（超过25秒）")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(25)  # 25秒超时

    with app.app_context():
        try:
            # ... 采集逻辑
        except TimeoutError:
            app.logger.error('采集任务执行超时')
            db.session.rollback()
        finally:
            signal.alarm(0)  # 取消超时信号
```

---

## 4. 任务并发数限制优化

### 问题描述

原代码写死 `max_workers = 3`，无法充分利用数据库连接池资源。

### 修复方案

根据连接池配置动态计算最大并发数：

```python
# app/views/tasks.py

# 根据连接池配置计算最大并发数
# pool_size(30) + max_overflow(30) = 60 最大连接
# 每个节点约需 3-4 个连接，安全值 = 60 / 4 = 15
max_workers = min(15, len(nodes))
```

### 连接池配置

```python
# config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 30,        # 预建连接数（原来10）
    'max_overflow': 30,     # 额外连接数（原来20）
    'pool_recycle': 1800,   # 30分钟回收
    'pool_pre_ping': True,   # 连接可用性检测
}
```

---

## 5. 失败节点处理改进

### 问题描述

原代码只记录失败数量，不记录失败详情。

### 修复方案

```python
# 返回详细的失败信息
result = {
    'total': len(nodes),
    'success': success_count,
    'failed': failed_count,
    'failed_nodes': [
        {'node_id': 1, 'node_name': 'node-1', 'error': 'connection failed'},
        {'node_id': 2, 'node_name': 'node-2', 'error': 'timeout'},
    ]
}
```

---

## 修改文件清单

| 文件 | 修改类型 | 修改内容 |
|------|----------|----------|
| `app/utils/datetime_utils.py` | 新增 | 统一时间工具模块 |
| `app/models/system_metric.py` | 修改 | 添加批量插入方法，修复 datetime |
| `app/services/metric_collector.py` | 修改 | 简化代码，仅保留采集方法 |
| `app/views/environment_spaces.py` | 修改 | 使用封装的批量方法，修复 datetime |
| `application.py` | 修改 | 添加超时控制，修复 datetime |
| `app/views/tasks.py` | 修改 | 优化并发数配置 |
| `config.py` | 修改 | 优化连接池配置 |

---

## 验证方法

### 1. datetime.utcnow() 检查

```bash
# 搜索是否还有遗漏
grep -r "datetime.utcnow" backend/app --include="*.py"
```

预期结果：无输出（已全部修复）

### 2. 批量插入方法测试

```python
# 测试 SystemMetric.bulk_insert_system_metrics
from app.models.system_metric import SystemMetric

metrics = {
    'cpu_usage': 45.5,
    'memory_usage': 60.0,
    'load_average': [1.5, 1.2, 1.0]
}

inserted = SystemMetric.bulk_insert_system_metrics(node_id=1, metrics=metrics)
print(f"Inserted {inserted} records")
```

### 3. 超时控制测试

```python
import signal

def test_timeout():
    def handler(signum, frame):
        raise TimeoutError()

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(1)  # 1秒后超时

    try:
        import time
        time.sleep(5)  # 模拟长任务
    except TimeoutError:
        print("Timeout works!")
    finally:
        signal.alarm(0)

test_timeout()
```

### 4. 并发数配置验证

```python
# 连接池配置
print(f"Pool size: {30}")
print(f"Max overflow: {30}")
print(f"Max concurrent workers: {30 // 4}")  # = 15
```
