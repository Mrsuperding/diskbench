# 节点监控图表视图优化 - 时间序列曲线图

## 用户需求

将图表视图从柱状图改为**时间序列曲线图**：
- ✅ X轴显示时间
- ✅ 不同节点用不同的线条表示
- ✅ 支持多个节点的性能对比
- ✅ 支持时间范围选择

## 实现方案

### 1. 数据源变更

#### 修改前（柱状图）
- 数据源：实时数据（最新一条）
- 展示方式：横向对比多个节点的当前值
- X轴：节点名称
- Y轴：指标值

#### 修改后（折线图）
- 数据源：历史数据（时间序列）
- 展示方式：展示多个节点的趋势变化
- X轴：时间点
- Y轴：指标值
- 多条线：每个节点一条线

### 2. 新增历史数据加载

**文件**: `frontend/src/views/NodeMonitoring.vue`

```javascript
// 新增状态
const historyMetrics = ref([]);
const timeRange = ref(1); // 默认1小时

// 加载历史数据
const loadHistoryMetrics = async () => {
  const response = await environmentSpacesApi.getHistoryMetrics(
    spaceId.value,
    { hours: timeRange.value }
  );
  historyMetrics.value = response.data;
};
```

### 3. 时间范围选择器

新增下拉选择器，支持以下时间范围：
- 最近1小时（默认）
- 最近6小时
- 最近12小时
- 最近24小时

### 4. 图表配置改造

#### 数据处理逻辑

```javascript
const getChartOption = (metric) => {
  // 1. 准备时间序列数据结构
  const timeSeriesData = {}; // { nodeId: { name, data: { time: value } } }

  // 2. 遍历历史数据，按节点和时间组织
  historyMetrics.value.forEach((nodeData) => {
    const nodeId = nodeData.node_id;
    const nodeName = nodeData.node_name;

    // 获取该节点的指定指标数据
    let metricData = nodeData.metrics[metric];

    // 处理特殊数据类型
    // - load_average: JSON字符串转数组
    // - network: 字节转MB/s

    // 按时间点存储
    metricData.forEach((point) => {
      timeSeriesData[nodeId].data[point.time] = point.value;
    });
  });

  // 3. 转换为ECharts系列数据
  const series = Object.entries(timeSeriesData).map(([nodeId, nodeInfo]) => ({
    name: nodeInfo.name,
    type: "line",
    smooth: true,
    data: sortedTimestamps.map(time => nodeInfo.data[time] || null)
  }));

  return { xAxis, yAxis, series, legend, tooltip };
};
```

#### 折线图特性

```javascript
series: [{
  name: "节点1",
  type: "line",
  smooth: true,          // 平滑曲线
  connectNulls: true,    // 连接空值
  symbol: "circle",      // 数据点样式
  symbolSize: 4,         // 数据点大小
  data: [...]
}]
```

#### 时间轴格式化

```javascript
// X轴显示格式: "MM-DD HH:mm"
xAxisData = sortedTimestamps.map((time) => {
  const date = new Date(time);
  const month = (date.getMonth() + 1).toString().padStart(2, "0");
  const day = date.getDate().toString().padStart(2, "0");
  const hours = date.getHours().toString().padStart(2, "0");
  const minutes = date.getMinutes().toString().padStart(2, "0");
  return `${month}-${day} ${hours}:${minutes}`;
});
```

#### 提示框优化

```javascript
tooltip: {
  trigger: "axis",
  axisPointer: {
    type: "cross",
    label: {
      backgroundColor: "#6a7985"
    }
  },
  formatter: (params) => {
    // 显示时间点
    // 显示所有节点在该时间点的值
    // 自动添加单位（%、MB/s等）
  }
}
```

### 5. 图例优化

```javascript
legend: {
  data: series.map(s => s.name),
  bottom: 0,
  type: "scroll",  // 节点过多时可滚动
}
```

### 6. 视图切换优化

```javascript
// 监听视图模式变化
const handleViewModeChange = async () => {
  if (viewMode.value === "chart") {
    await loadHistoryMetrics(); // 加载历史数据
  } else {
    await loadNodesMetrics();   // 加载实时数据
  }
};
```

## UI布局

### 指标选择卡片布局

```
┌─────────────────────────────────────────────────────────┐
│ 选择监控指标          [时间范围▼] [自动刷新选项...]     │
├─────────────────────────────────────────────────────────┤
│ ☑ CPU使用率  ☑ 内存使用率  □ 磁盘使用率                │
│ □ 网络上行   □ 网络下行    □ 系统负载                  │
└─────────────────────────────────────────────────────────┘
```

### 图表布局（2列）

```
┌─────────────────────┐  ┌─────────────────────┐
│   CPU使用率趋势图   │  │  内存使用率趋势图   │
│                     │  │                     │
│  节点1 ─────        │  │  节点1 ─────        │
│  节点2 - - -        │  │  节点2 - - -        │
│                     │  │                     │
└─────────────────────┘  └─────────────────────┘
```

## 数据格式

### 后端返回格式

```json
[
  {
    "node_id": 4,
    "node_name": "dy节点",
    "metrics": {
      "cpu_usage": [
        {"value": 27.3, "unit": "%", "time": "2026-03-27T10:30:00"},
        {"value": 32.5, "unit": "%", "time": "2026-03-27T10:30:30"},
        {"value": 28.1, "unit": "%", "time": "2026-03-27T10:31:00"}
      ],
      "memory_usage": [
        {"value": 65.2, "unit": "%", "time": "2026-03-27T10:30:00"},
        {"value": 66.8, "unit": "%", "time": "2026-03-27T10:30:30"}
      ]
    }
  }
]
```

### 前端处理后

```javascript
// 时间序列数据
{
  "4": {
    "name": "dy节点",
    "data": {
      "2026-03-27T10:30:00": 27.3,
      "2026-03-27T10:30:30": 32.5,
      "2026-03-27T10:31:00": 28.1
    }
  }
}

// ECharts系列
series: [{
  name: "dy节点",
  type: "line",
  data: [27.3, 32.5, 28.1]
}]
```

## 特殊数据处理

### 1. 网络速率（字节 → MB/s）

```javascript
if (metric === "network_tx" || metric === "network_rx") {
  value = (value / 1024 / 1024).toFixed(2);
}
```

### 2. Load Average（JSON字符串 → 数组）

```javascript
if (metric === "load_average" && typeof value === "string") {
  try {
    const loadArray = JSON.parse(value);
    value = loadArray[0]; // 使用1分钟负载
  } catch (e) {
    value = 0;
  }
}
```

### 3. 空值处理

```javascript
series: [{
  connectNulls: true,  // 自动连接空值点
  data: [10, null, 20, 30]  // null值会被跳过
}]
```

## 使用流程

### 用户操作流程

1. **进入监控页面**
   - 默认显示表格视图

2. **切换到图表视图**
   - 点击"图表视图"按钮
   - 系统自动加载最近1小时的历史数据

3. **选择监控指标**
   - 勾选要查看的指标（默认：CPU、内存）
   - 最多可选6个指标

4. **调整时间范围**
   - 下拉选择：1小时/6小时/12小时/24小时
   - 图表自动刷新

5. **设置自动刷新**
   - 可选：手动/30秒/1分钟/5分钟
   - 图表会自动更新数据

### 数据刷新机制

```
用户切换视图
    ↓
加载历史数据 (1小时)
    ↓
渲染折线图
    ↓
定时刷新 (如果启用)
    ↓
更新图表数据
```

## 性能优化

### 1. 数据抽样

对于大时间范围（24小时），可能有上千个数据点：
- 当前：显示所有点
- 优化：可以考虑按分钟聚合

### 2. X轴标签优化

```javascript
axisLabel: {
  rotate: 45,
  interval: Math.floor(xAxisData.length / 10) || 0  // 最多显示10个标签
}
```

### 3. 按需加载

只在图表视图时加载历史数据，表格视图仅加载实时数据。

## 测试验证

### 1. 数据采集测试

```bash
cd backend
python -c "
from application import collect_all_metrics
import time

# 采集3次数据
for i in range(3):
    collect_all_metrics()
    time.sleep(2)
"
```

### 2. 历史数据查询测试

```bash
python -c "
from application import app
from app.models.system_metric import SystemMetric
from datetime import datetime, timedelta

with app.app_context():
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)

    metrics = SystemMetric.get_metrics_by_environment(1, start_time, end_time)
    print(f'Total metrics: {len(metrics)}')
"
```

### 3. 前端图表渲染测试

1. 切换到图表视图
2. 检查是否显示折线图
3. 验证多节点线条是否正确显示
4. 测试时间范围切换
5. 验证Tooltip显示

## 对比总结

| 特性 | 柱状图（旧） | 折线图（新） |
|-----|------------|------------|
| X轴 | 节点名称 | 时间点 |
| Y轴 | 指标值 | 指标值 |
| 数据 | 实时单点 | 历史时间序列 |
| 用途 | 横向对比 | 趋势分析 |
| 数据量 | N个节点 | N×M个时间点 |
| 适用场景 | 快速查看当前状态 | 分析历史趋势 |

## 技术栈

- **图表库**: ECharts 5.4.3
- **Vue组件**: vue-echarts 6.6.1
- **图表类型**: LineChart（折线图）
- **数据请求**: Axios
- **状态管理**: Vue 3 Composition API

## 文件修改清单

### 前端
- ✅ `frontend/src/views/NodeMonitoring.vue`
  - 新增历史数据加载方法
  - 修改图表配置为折线图
  - 添加时间范围选择器
  - 优化视图切换逻辑

### 后端
- ✅ 无需修改（历史数据API已存在）

## 下一步优化

1. **数据聚合** - 对长时间范围数据进行聚合
2. **缩放功能** - 支持时间轴缩放和拖拽
3. **数据导出** - 导出图表为图片或CSV
4. **对比模式** - 同一图表对比多个指标
5. **告警标记** - 在图表上标注告警时间点

---

**更新时间**: 2026-03-27
**版本**: v3.0
**状态**: 已完成
