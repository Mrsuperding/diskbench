# IOSTAT性能图表重命名为FIO性能图表报告

## 修改时间
2026-03-23

## 修改概述
将"IOSTAT性能图表"重命名为"FIO性能图表"，并修改数据源从FIO日志获取p99、p9999等延迟性能数据。

## 功能说明

### 原有功能（IOSTAT）
- 数据来源：IOSTAT日志（系统级IO统计）
- 主要指标：
  - 读/写IOPS
  - 读/写吞吐量（KB/s）
  - IO等待时间（await_time）
  - 服务时间（svctm）
  - 磁盘使用率（util）

### 新功能（FIO）
- 数据来源：FIO日志（应用级IO测试工具）
- 主要指标：
  - 读/写IOPS
  - 读/写吞吐量（KB/s）
  - **平均延迟（lat）**
  - **P99延迟（lat_p99）** ⭐
  - **P9999延迟（lat_p9999）** ⭐
  - **最大延迟（lat_max）**

## 修改的文件

### frontend/src/views/IOStatChart.vue

#### 1. 模板部分（Template）

**标题更改**：
```vue
<!-- 修改前 -->
<span>IOSTAT性能图表</span>

<!-- 修改后 -->
<span>FIO性能图表</span>
```

**CSS类名更改**：
```vue
<!-- 修改前 -->
<div class="iostat-chart-container">

<!-- 修改后 -->
<div class="fio-chart-container">
```

**指标选项更改**：
```vue
<!-- 修改前 -->
<el-option label="读IOPS" value="read_iops"></el-option>
<el-option label="写IOPS" value="write_iops"></el-option>
<el-option label="读吞吐量" value="read_kbps"></el-option>
<el-option label="写吞吐量" value="write_kbps"></el-option>
<el-option label="IO等待时间" value="await_time"></el-option>
<el-option label="服务时间" value="svctm"></el-option>
<el-option label="磁盘使用率" value="util"></el-option>

<!-- 修改后 -->
<el-option label="读IOPS" value="read_iops"></el-option>
<el-option label="写IOPS" value="write_iops"></el-option>
<el-option label="读吞吐量(KB/s)" value="read_bw"></el-option>
<el-option label="写吞吐量(KB/s)" value="write_bw"></el-option>
<el-option label="平均延迟(ms)" value="lat"></el-option>
<el-option label="P99延迟(ms)" value="lat_p99"></el-option>
<el-option label="P9999延迟(ms)" value="lat_p9999"></el-option>
<el-option label="最大延迟(ms)" value="lat_max"></el-option>
```

**事件处理函数更改**：
```vue
<!-- 修改前 -->
@change="loadIOStatData"
@change="updateIOStatChart"

<!-- 修改后 -->
@change="loadFIOData"
@change="updateFIOChart"
```

#### 2. Script部分

**导入更改**：
```javascript
// 修改前
import { getTaskLogs, getIOStatMetrics } from "@/api/logs";

// 修改后
import { getTaskLogs, getFIOResults } from "@/api/logs";
```

**变量名更改**：
```javascript
// 修改前
const iostatChartRef = ref(null);
let iostatChart = null;
const iostatMetrics = reactive({
  timestamps: [],
  devices: {},
  read_iops: [],
  write_iops: [],
  read_kbps: [],
  write_kbps: [],
  await_time: [],
  svctm: [],
  util: [],
});

// 修改后
const fioChartRef = ref(null);
let fioChart = null;
const fioMetrics = reactive({
  timestamps: [],
  devices: {},
  read_iops: [],
  write_iops: [],
  read_bw: [],
  write_bw: [],
  lat: [],
  lat_p99: [],
  lat_p9999: [],
  lat_max: [],
});
```

**默认选中指标更改**：
```javascript
// 修改前
const selectedYAxisMetrics = ref(["read_iops", "write_iops"]);

// 修改后 - 默认显示延迟指标
const selectedYAxisMetrics = ref(["lat_p99", "lat_p9999", "lat_max"]);
```

**loadFIOData函数（新）**：
```javascript
const loadFIOData = async () => {
  if (!selectedNode.value) return;

  try {
    console.log("加载FIO数据开始，selectedNode:", selectedNode.value);
    // 重置数据
    resetFIOData();

    // 获取任务的测试日志
    const logsResponse = await getTaskLogs(taskId.value, {
      node_id: selectedNode.value,
    });

    if (logsResponse && logsResponse.data) {
      let logsData = logsResponse.data;
      if (logsResponse.data.items) {
        logsData = logsResponse.data.items;
      }

      // 过滤FIO类型的日志
      const fioLogs = logsData.filter((log) => log.log_type === "fio");

      if (fioLogs.length > 0) {
        // 按设备分组FIO日志
        const deviceLogs = {};
        fioLogs.forEach((log) => {
          if (log.device_name) {
            if (!deviceLogs[log.device_name]) {
              deviceLogs[log.device_name] = [];
            }
            deviceLogs[log.device_name].push(log);
          }
        });

        // 收集所有设备
        const devices = Object.keys(deviceLogs);
        availableDevices.value = devices;
        if (devices.length > 0 && !selectedDevice.value) {
          selectedDevice.value = devices[0];
        }

        // 处理每个设备的FIO日志
        for (const device of devices) {
          const logs = deviceLogs[device];
          for (const log of logs) {
            // 调用FIO结果解析API
            const metricsResponse = await getFIOResults(log.id);

            if (metricsResponse && metricsResponse.data) {
              processFIOMetrics(metricsResponse.data, device, log.collection_time);
            }
          }
        }

        updateFIOChart();
      }
    }
  } catch (error) {
    console.error("加载FIO数据失败:", error);
  }
};
```

**processFIOMetrics函数（新）**：
```javascript
const processFIOMetrics = (fioResults, device, collectionTime) => {
  console.log("处理FIO指标数据:", fioResults, "设备:", device);

  // 初始化设备数据
  if (!fioMetrics.devices[device]) {
    fioMetrics.devices[device] = {
      timestamps: [],
      read_iops: [],
      write_iops: [],
      read_bw: [],
      write_bw: [],
      lat: [],
      lat_p99: [],
      lat_p9999: [],
      lat_max: [],
    };
  }

  const timestamp = new Date(collectionTime).toLocaleTimeString();
  const deviceData = fioMetrics.devices[device];

  // 从FIO结果中提取指标
  if (fioResults.jobs && fioResults.jobs.length > 0) {
    const job = fioResults.jobs[0]; // 使用第一个job的数据

    deviceData.timestamps.push(timestamp);
    deviceData.read_iops.push(job.read_iops || 0);
    deviceData.write_iops.push(job.write_iops || 0);
    deviceData.read_bw.push(job.read_bw || 0);
    deviceData.write_bw.push(job.write_bw || 0);
    deviceData.lat.push(job.lat || 0);
    deviceData.lat_p99.push(job.lat_p99 || 0);
    deviceData.lat_p9999.push(job.lat_p9999 || 0);
    deviceData.lat_max.push(job.lat_max || 0);
  }

  // 更新当前选中设备的数据
  if (selectedDevice.value === device) {
    fioMetrics.timestamps = deviceData.timestamps;
    fioMetrics.read_iops = deviceData.read_iops;
    fioMetrics.write_iops = deviceData.write_iops;
    fioMetrics.read_bw = deviceData.read_bw;
    fioMetrics.write_bw = deviceData.write_bw;
    fioMetrics.lat = deviceData.lat;
    fioMetrics.lat_p99 = deviceData.lat_p99;
    fioMetrics.lat_p9999 = deviceData.lat_p9999;
    fioMetrics.lat_max = deviceData.lat_max;
  }
};
```

**updateFIOChart函数指标颜色映射**：
```javascript
const getMetricColor = (metric) => {
  const colorMap = {
    read_iops: "#36cbcb",
    write_iops: "#f6bd16",
    read_bw: "#1890ff",      // 改为read_bw
    write_bw: "#722ed1",     // 改为write_bw
    lat: "#52c41a",          // 新增
    lat_p99: "#eb2f96",      // 新增
    lat_p9999: "#fa8c16",    // 新增
    lat_max: "#f5222d",      // 新增
  };
  return colorMap[metric] || "#ccc";
};
```

**updateFIOChart函数指标标签映射**：
```javascript
const getMetricLabel = (metric) => {
  const labelMap = {
    read_iops: "读IOPS",
    write_iops: "写IOPS",
    read_bw: "读吞吐量 (KB/s)",      // 改为read_bw
    write_bw: "写吞吐量 (KB/s)",     // 改为write_bw
    lat: "平均延迟 (ms)",            // 新增
    lat_p99: "P99延迟 (ms)",         // 新增
    lat_p9999: "P9999延迟 (ms)",     // 新增
    lat_max: "最大延迟 (ms)",        // 新增
  };
  return labelMap[metric] || metric;
};
```

**getYAxisName函数**：
```javascript
// 修改前
const getYAxisName = (metric) => {
  if (metric.includes("iops")) return "IOPS";
  if (metric.includes("kbps")) return "吞吐量 (KB/s)";
  if (metric.includes("await") || metric.includes("svctm")) return "时间 (ms)";
  if (metric.includes("util")) return "使用率 (%)";
  return "值";
};

// 修改后
const getYAxisName = (metric) => {
  if (metric.includes("iops")) return "IOPS";
  if (metric.includes("_bw")) return "吞吐量 (KB/s)";
  if (metric.includes("lat")) return "延迟 (ms)";
  return "值";
};
```

**其他函数名更改**：
- `resetIOStatData()` → `resetFIOData()`
- `initIOStatChart()` → `initFIOChart()`
- `updateIOStatChart()` → `updateFIOChart()`
- `processIOStatMetrics()` → `processFIOMetrics()`

#### 3. CSS部分

```css
/* 修改前 */
.iostat-chart-container {
  padding: 20px;
}

/* 修改后 */
.fio-chart-container {
  padding: 20px;
}
```

## 数据流程对比

### 原IOSTAT数据流程
```
1. 选择节点 → loadIOStatData()
2. 获取任务日志（log_type="iostat"）
3. 调用getIOStatMetrics(logId) → 获取iostat指标
4. processIOStatMetrics() → 处理并按设备分组
5. updateIOStatChart() → 更新图表
```

### 新FIO数据流程
```
1. 选择节点 → loadFIOData()
2. 获取任务日志（log_type="fio"）
3. 按设备分组FIO日志
4. 对每个日志调用getFIOResults(logId) → 解析FIO输出
5. processFIOMetrics() → 提取jobs[0]的指标数据
6. updateFIOChart() → 更新图表
```

## 后端API支持

### 已有的FIO API
```
GET /api/logs/<log_id>/fio-results
```

**返回数据结构**：
```json
{
  "code": 200,
  "data": {
    "global": { ... },
    "jobs": [
      {
        "name": "diskbench_test",
        "rw_type": "randwrite",
        "read_iops": 1234.56,
        "read_bw": 5678.9,
        "write_iops": 2345.67,
        "write_bw": 6789.0,
        "lat": 12.34,
        "lat_p99": 45.67,
        "lat_p9999": 89.01,
        "lat_max": 123.45
      }
    ]
  },
  "message": "获取FIO日志解析结果成功"
}
```

## FIO指标说明

### P99延迟（lat_p99）
- **含义**：99%的IO请求延迟低于此值
- **重要性**：衡量大部分IO请求的性能
- **单位**：毫秒（ms）

### P9999延迟（lat_p9999）
- **含义**：99.99%的IO请求延迟低于此值
- **重要性**：识别极端情况下的IO延迟
- **单位**：毫秒（ms）
- **应用场景**：对延迟敏感的应用（数据库、金融系统）

### 最大延迟（lat_max）
- **含义**：测试期间观察到的最大IO延迟
- **重要性**：发现IO性能的最坏情况
- **单位**：毫秒（ms）

### 平均延迟（lat）
- **含义**：所有IO请求延迟的算术平均值
- **重要性**：衡量整体IO性能
- **单位**：毫秒（ms）

## 构建状态
✅ 前端成功构建
- Build Hash: 6d3f5399437303b4
- Build Time: 67700ms
- 无错误

## 测试建议

### 1. 基础功能测试
- [ ] 访问任务详情页面
- [ ] 点击"查看FIO性能图表"（原IOSTAT性能图表）
- [ ] 验证页面标题显示"FIO性能图表"
- [ ] 验证指标选项包含P99、P9999、最大延迟

### 2. 数据加载测试
- [ ] 选择节点，验证设备下拉框显示正确
- [ ] 选择设备，验证图表加载
- [ ] 默认应显示：lat_p99, lat_p9999, lat_max三个指标
- [ ] 切换不同指标，验证图表更新

### 3. 数据正确性测试
- [ ] 检查P99延迟数值合理（通常几ms到几十ms）
- [ ] 检查P9999延迟 > P99延迟
- [ ] 检查最大延迟 >= P9999延迟
- [ ] 对比FIO原始日志，验证数据准确性

### 4. 控制台检查
应该看到：
```
加载FIO数据开始，selectedNode: <节点ID>
获取任务日志成功: {...}
FIO日志: [...]
处理FIO指标数据: {...} 设备: vdb
```

不应该看到：
```
❌ 没有找到FIO类型的日志
❌ 加载FIO数据失败
```

## 与IO性能抖动图表的区别

### IO性能抖动图表（IOJitterChart.vue）
- 数据来源：**IOSTAT日志**
- 实时性：实时收集系统级IO统计
- 更新频率：高（每秒或每几秒）
- 主要用途：监控IO抖动和波动

### FIO性能图表（IOStatChart.vue -> 现在）
- 数据来源：**FIO日志**
- 实时性：测试完成后解析
- 更新频率：低（每次测试一个数据点）
- 主要用途：分析测试结果和延迟分布

## 注意事项

1. **数据来源不同**：
   - IOSTAT：系统级监控，实时采集
   - FIO：应用级测试，测试后解析

2. **时间粒度不同**：
   - IOSTAT：连续时间序列
   - FIO：离散测试点

3. **指标侧重不同**：
   - IOSTAT：关注系统资源使用（utilization, await_time）
   - FIO：关注应用层延迟（p99, p9999）

4. **适用场景**：
   - 实时监控 → 使用IO性能抖动图表（IOSTAT）
   - 性能测试分析 → 使用FIO性能图表

## 后续优化建议

1. **支持多设备聚合**：
   类似IOJitterChart，支持多节点多设备数据聚合

2. **添加延迟分布图**：
   - 使用柱状图显示延迟分布
   - 突出显示p50, p95, p99, p9999分位点

3. **对比功能**：
   - 支持多次测试结果对比
   - 显示性能提升或下降趋势

4. **告警阈值**：
   - 设置P99延迟阈值
   - 超过阈值时高亮显示

## 相关文档
- IO图表API修复：`io_charts_api_fix_report.md`
- IOSTAT变量初始化修复：`iostat_chart_variable_initialization_fix.md`
- 多节点多设备功能：`multi_node_multi_device_jitter_chart_report.md`
- 会话总结：`session_summary_report.md`

## 修复状态
✅ 已完成并构建成功
