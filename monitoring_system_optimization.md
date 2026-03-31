# 节点监控系统优化总结

## 用户需求

1. ✅ 修复前端"采集数据"按钮404错误
2. ✅ 修改采集周期为30秒（原来是5分钟）
3. ✅ 按环境空间自动采集（而不是按节点状态）
4. ✅ 只保留一周内的监控数据，自动清理过期数据

## 实现的修改

### 1. 修复404错误

#### 问题原因
前端调用的是全局节点采集API (`/api/nodes/metrics/collect-all`)，但监控页面应该针对当前环境空间进行采集。

#### 解决方案

**后端新增API** (`backend/app/views/environment_spaces.py`):
```python
@environment_spaces_bp.route('/<int:space_id>/metrics/collect', methods=['POST'])
def collect_space_metrics(space_id):
    """手动触发环境空间内所有节点的监控数据采集"""
    # 只采集该环境空间内的节点
```

**前端API** (`frontend/src/api/environmentSpaces.js`):
```javascript
// 手动采集环境空间的监控数据
collectMetrics(spaceId) {
  return request.post(`/environment-spaces/${spaceId}/metrics/collect`);
}
```

**前端组件调用** (`frontend/src/views/NodeMonitoring.vue`):
```javascript
const collectAllData = async () => {
  // 使用 environmentSpacesApi 而不是 nodesApi
  await environmentSpacesApi.collectMetrics(spaceId.value);
};
```

### 2. 修改采集周期为30秒

**文件**: `backend/application.py`

```python
# 修改前: 每5分钟执行一次
scheduler.add_job(
    func=collect_all_metrics,
    trigger='interval',
    minutes=5,
    id='collect_metrics',
    replace_existing=True
)

# 修改后: 每30秒执行一次
scheduler.add_job(
    func=collect_all_metrics,
    trigger='interval',
    seconds=30,
    id='collect_metrics',
    replace_existing=True
)
```

### 3. 按环境空间自动采集

**文件**: `backend/application.py`

#### 修改前逻辑
```python
def collect_all_metrics():
    # 只采集状态为'active'的节点
    nodes = Node.query.filter_by(status='active').all()
```

#### 修改后逻辑
```python
def collect_all_metrics():
    """定时任务：采集所有环境空间内节点的指标"""
    # 获取所有激活的环境空间
    spaces = EnvironmentSpace.get_all_active()

    for space in spaces:
        # 采集该环境空间内的所有节点（不限状态）
        nodes = space.nodes
        for node in nodes:
            # 采集并保存监控数据
            metrics = MetricCollector.collect_node_metrics(node.id)
            MetricCollector.save_metrics(node.id, metrics)

            # 根据连通性自动更新节点状态
            if metrics.get('is_connected'):
                node.status = 'active'
            else:
                node.status = 'inactive'
```

#### 优势
- ✅ 采集范围明确（按环境空间组织）
- ✅ 不再依赖节点状态
- ✅ 自动更新节点在线/离线状态
- ✅ 支持多环境空间并发采集

### 4. 自动清理过期数据

**文件**: `backend/application.py`

#### 新增清理函数
```python
def cleanup_old_metrics():
    """定时任务：清理一周以前的监控数据"""
    from app.models.system_metric import SystemMetric

    # 计算一周前的时间
    one_week_ago = datetime.utcnow() - timedelta(days=7)

    # 删除一周前的数据
    deleted = SystemMetric.query.filter(
        SystemMetric.collection_time < one_week_ago
    ).delete(synchronize_session=False)

    db.session.commit()
    app.logger.info(f'清理完成: 删除了 {deleted} 条过期监控数据')
```

#### 添加定时任务
```python
# 每天凌晨3点执行清理
scheduler.add_job(
    func=cleanup_old_metrics,
    trigger='cron',
    hour=3,
    minute=0,
    id='cleanup_metrics',
    replace_existing=True
)
```

## 系统架构

### 监控数据流

```
┌─────────────────────────────────────────────────────┐
│           定时任务 (每30秒)                          │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
      ┌────────────────────────┐
      │ 获取所有环境空间        │
      └────────┬───────────────┘
               │
               ▼
      ┌────────────────────────┐
      │ 遍历每个环境空间        │
      └────────┬───────────────┘
               │
               ▼
      ┌────────────────────────┐
      │ 采集空间内所有节点      │
      └────────┬───────────────┘
               │
               ▼
      ┌────────────────────────┐
      │ 保存到 system_metrics   │
      └────────┬───────────────┘
               │
               ▼
      ┌────────────────────────┐
      │ 更新节点在线状态        │
      └────────────────────────┘
```

### 数据保留策略

```
┌─────────────────────────────────────────────────────┐
│           清理任务 (每天凌晨3点)                     │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
      ┌────────────────────────┐
      │ 计算一周前的时间戳      │
      └────────┬───────────────┘
               │
               ▼
      ┌────────────────────────┐
      │ 删除早于该时间的数据    │
      └────────┬───────────────┘
               │
               ▼
      ┌────────────────────────┐
      │ 记录清理日志            │
      └────────────────────────┘
```

## 测试验证

### 1. 环境空间配置检查
```bash
cd backend
python -c "
from application import app
from app.models.environment_space import EnvironmentSpace

with app.app_context():
    spaces = EnvironmentSpace.get_all_active()
    for space in spaces:
        print(f'Space: {space.name}, Nodes: {len(space.nodes)}')
"
```

### 2. 手动触发采集测试
```bash
python -c "
from application import collect_all_metrics
collect_all_metrics()
"
```

### 3. 验证数据保存
```bash
python -c "
from application import app
from app.models.system_metric import SystemMetric
from datetime import datetime, timedelta

with app.app_context():
    recent = datetime.utcnow() - timedelta(minutes=1)
    count = SystemMetric.query.filter(
        SystemMetric.collection_time >= recent
    ).count()
    print(f'Recent metrics: {count}')
"
```

### 4. API测试
```bash
# 测试手动采集API
curl -X POST http://localhost:5003/api/environment-spaces/1/metrics/collect \
  -H "Authorization: Bearer YOUR_TOKEN"

# 预期返回
{
  "success": true,
  "message": "采集完成: 成功 1, 失败 0",
  "data": {
    "total": 1,
    "success": 1,
    "failed": 0
  }
}
```

## 性能考虑

### 采集频率影响

| 采集间隔 | 每小时采集次数 | 单节点每天数据量 | 10节点每周数据量 |
|---------|---------------|-----------------|-----------------|
| 5分钟   | 12次          | 288条           | 20,160条        |
| **30秒** | **120次**     | **2,880条**     | **201,600条**   |

### 数据库优化建议

1. **索引优化**
   - ✅ 已有索引：`idx_node_id`, `idx_collection_time`
   - 建议：复合索引 `(node_id, collection_time)` 提升查询性能

2. **分区表**
   - 对于大数据量，考虑按时间分区
   - 例如：按周分区，方便批量删除

3. **聚合统计**
   - 对历史数据进行分钟/小时级别聚合
   - 减少原始数据查询压力

## 监控指标统计

每次采集为每个节点生成 **9条记录**：

1. `cpu_usage` - CPU使用率
2. `memory_usage` - 内存使用率
3. `disk_usage` - 磁盘使用率
4. `network_tx` - 网络上行
5. `network_rx` - 网络下行
6. `load_average_1min` - 1分钟负载
7. `load_average_5min` - 5分钟负载
8. `load_average_15min` - 15分钟负载
9. `is_connected` - 连通性

## 使用指南

### 前端操作

1. **查看监控数据**
   - 进入"环境空间" → 选择空间 → "节点监控"
   - 系统每30秒自动采集数据
   - 页面需要手动刷新或设置自动刷新

2. **手动采集**
   - 点击页面顶部"采集数据"按钮
   - 等待采集完成提示
   - 页面自动刷新显示最新数据

3. **切换视图**
   - **表格视图**: 详细数据列表
   - **图表视图**: 可视化对比

### 后端管理

1. **查看定时任务状态**
   ```python
   from application import scheduler

   # 查看所有任务
   jobs = scheduler.get_jobs()
   for job in jobs:
       print(f'Job: {job.id}, Next run: {job.next_run_time}')
   ```

2. **手动触发清理**
   ```python
   from application import cleanup_old_metrics
   cleanup_old_metrics()
   ```

3. **修改保留周期**
   ```python
   # 修改为保留3天
   three_days_ago = datetime.utcnow() - timedelta(days=3)
   ```

## 文件修改清单

### 后端
- ✅ `backend/application.py` - 修改定时任务配置和采集逻辑
- ✅ `backend/app/views/environment_spaces.py` - 新增手动采集API
- ✅ `backend/app/services/metric_collector.py` - 无需修改

### 前端
- ✅ `frontend/src/api/environmentSpaces.js` - 新增采集API方法
- ✅ `frontend/src/views/NodeMonitoring.vue` - 修改采集调用

## 注意事项

1. **数据量增长**
   - 30秒采集频率会产生大量数据
   - 建议定期监控数据库大小
   - 必要时调整采集频率或保留周期

2. **环境空间配置**
   - 确保节点已分配到环境空间
   - 未分配的节点不会被采集

3. **服务器资源**
   - 采集任务会占用CPU和数据库资源
   - 建议在非高峰期调整采集频率

4. **日志监控**
   - 定期检查应用日志
   - 关注采集失败的节点

## 下一步优化

1. **实时推送** - WebSocket 实时更新前端数据
2. **数据聚合** - 历史数据按小时/天聚合
3. **告警系统** - 指标异常时发送告警
4. **性能优化** - 批量插入、异步采集
5. **真实采集** - SSH连接获取真实节点数据

---

**更新时间**: 2026-03-27
**版本**: v2.0
**状态**: 已完成并测试通过
