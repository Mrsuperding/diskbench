# 节点监控数据采集功能修复

## 问题分析

### 主要问题
节点监控页面显示"没有任何数据监控"，经排查发现以下问题：

1. **数据库中没有监控数据** - system_metrics 表为空
2. **定时采集任务限制** - 只采集状态为 'active' 的节点，但所有节点状态都是 'inactive'
3. **缺少手动触发采集的功能** - 用户无法主动触发数据采集
4. **load_average 数据类型不匹配** - 尝试将数组存入 Float 类型字段导致失败

## 解决方案

### 1. 增强监控数据采集服务

**文件**: `backend/app/services/metric_collector.py`

#### 扩展采集的指标类型
```python
def collect_node_metrics(node_id):
    return {
        'cpu_usage': round(random.uniform(10, 90), 2),           # CPU使用率
        'memory_usage': round(random.uniform(20, 85), 2),        # 内存使用率
        'disk_usage': round(random.uniform(30, 80), 2),          # 磁盘使用率
        'network_tx': round(random.uniform(...), 2),             # 网络上行
        'network_rx': round(random.uniform(...), 2),             # 网络下行
        'load_average': [1min, 5min, 15min],                     # 系统负载
        'is_connected': True/False                                # 连通性
    }
```

#### 修复 load_average 存储问题
将 load_average 数组拆分为3个独立指标：
- `load_average_1min`
- `load_average_5min`
- `load_average_15min`

这样避免了数据类型不匹配的问题（metric_value 是 Float 类型）。

### 2. 新增手动采集 API

**文件**: `backend/app/views/nodes.py`

#### 单节点采集
```python
POST /api/nodes/{node_id}/metrics/collect
```
手动触发单个节点的监控数据采集

#### 批量采集
```python
POST /api/nodes/metrics/collect-all
```
手动触发所有节点的监控数据采集，返回统计信息：
```json
{
  "total": 10,
  "success": 10,
  "failed": 0
}
```

### 3. 优化指标获取 API

**文件**: `backend/app/views/nodes.py`

#### 自动组装 load_average
```python
GET /api/nodes/{node_id}/metrics
```
返回数据时自动将 load_average 的3个独立指标组装成数组：
```json
{
  "cpu_usage": 27.3,
  "memory_usage": 35.6,
  "load_average": [3.75, 1.08, 2.32],  // 自动组装
  "updated_at": "2026-03-26 22:30:00"
}
```

### 4. 前端增强

**文件**: `frontend/src/api/nodes.js`

新增API方法：
```javascript
// 手动触发节点监控数据采集
collectNodeMetrics(nodeId)

// 批量采集所有节点监控数据
collectAllMetrics()
```

**文件**: `frontend/src/views/NodeMonitoring.vue`

#### 添加"采集数据"按钮
- 位置：页面头部操作区
- 图标：Collection
- 功能：一键采集所有节点监控数据
- 状态：显示 loading 状态

#### 实现采集功能
```javascript
const collectAllData = async () => {
  collecting.value = true;
  try {
    await nodesApi.collectAllMetrics();
    ElMessage.success("监控数据采集成功");
    await refreshData(); // 采集后立即刷新
  } catch (error) {
    ElMessage.error("采集监控数据失败");
  } finally {
    collecting.value = false;
  }
};
```

## 数据采集流程

### 自动采集（后台定时任务）
```
每5分钟 → 查询 active 节点 → 采集指标 → 保存到数据库
```

### 手动采集（用户触发）
```
用户点击按钮 → 调用 /nodes/metrics/collect-all
              → 采集所有节点（不限状态）
              → 保存到数据库
              → 返回统计信息
              → 前端刷新显示
```

## 测试验证

### 后端测试
```bash
cd backend
python -c "
from application import app, db
from app.models.node import Node
from app.services.metric_collector import MetricCollector

with app.app_context():
    nodes = Node.query.all()[:3]
    for node in nodes:
        metrics = MetricCollector.collect_node_metrics(node.id)
        MetricCollector.save_metrics(node.id, metrics)
    print('Success!')
"
```

### 预期结果
```
Collecting metrics for 3 nodes...

Node: 节点1 (ID: 1)
  Saved 9 total metrics
Node: local (ID: 2)
  Saved 9 total metrics
Node: dhq2 (ID: 3)
  Saved 9 total metrics

Success! All metrics collected and saved.
```

## 监控指标说明

| 指标名称 | 类型 | 单位 | 说明 |
|---------|------|-----|------|
| cpu_usage | Float | % | CPU使用率 (0-100) |
| memory_usage | Float | % | 内存使用率 (0-100) |
| disk_usage | Float | % | 磁盘使用率 (0-100) |
| network_tx | Float | B/s | 网络上行速率（字节/秒）|
| network_rx | Float | B/s | 网络下行速率（字节/秒）|
| load_average_1min | Float | - | 1分钟平均负载 |
| load_average_5min | Float | - | 5分钟平均负载 |
| load_average_15min | Float | - | 15分钟平均负载 |
| is_connected | Float | - | 连通性 (1.0=在线, 0.0=离线) |

## 使用方法

### 方法1：手动采集（推荐）
1. 进入"节点监控"页面
2. 点击顶部的 **"采集数据"** 按钮
3. 等待采集完成（显示成功提示）
4. 页面自动刷新显示最新数据

### 方法2：等待自动采集
- 系统每5分钟自动采集一次
- 仅采集状态为 'active' 的节点
- 需要节点状态正常

### 方法3：API调用
```bash
# 采集单个节点
curl -X POST http://localhost:5003/api/nodes/1/metrics/collect \
  -H "Authorization: Bearer YOUR_TOKEN"

# 批量采集所有节点
curl -X POST http://localhost:5003/api/nodes/metrics/collect-all \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 注意事项

1. **当前使用模拟数据** - Phase 1 版本使用随机数模拟监控数据
2. **后续真实采集** - Phase 2 将实现通过 SSH 连接节点采集真实数据
3. **数据存储** - 所有监控数据存储在 `system_metrics` 表中
4. **性能考虑** - 批量采集时会并发处理所有节点

## 修改文件列表

### 后端
- ✅ `backend/app/services/metric_collector.py` - 增强监控数据采集
- ✅ `backend/app/views/nodes.py` - 新增手动采集API
- ✅ `backend/app/models/environment_space.py` - 无需修改
- ✅ `backend/app/models/system_metric.py` - 无需修改

### 前端
- ✅ `frontend/src/api/nodes.js` - 新增采集API方法
- ✅ `frontend/src/views/NodeMonitoring.vue` - 添加采集按钮和功能

## 下一步优化

1. **真实数据采集** - 实现通过 SSH 采集真实节点监控数据
2. **历史数据清理** - 定期清理过期的监控数据
3. **数据聚合** - 对历史数据进行聚合以提高查询性能
4. **告警功能** - 当指标超过阈值时发送告警
5. **实时推送** - 使用 WebSocket 实时推送监控数据更新

---

**创建时间**: 2026-03-27
**修复人**: Claude
**版本**: v1.0
