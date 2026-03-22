# IO性能抖动图表多节点多设备支持实现报告

## 修复时间
2026-03-23

## 实现功能
为IO性能抖动图表增加了多节点、多设备选择功能，并实现了正确的数据聚合逻辑。

## 数据聚合策略

### 可叠加指标（Additive Metrics）- 求和
这些指标在多个节点或设备之间是独立的，可以直接相加：
- **读IOPS** - 多个设备的读操作次数可以相加
- **写IOPS** - 多个设备的写操作次数可以相加
- **总IOPS** - 读IOPS + 写IOPS
- **读吞吐量** (KB/s) - 多个设备的读吞吐量可以相加
- **写吞吐量** (KB/s) - 多个设备的写吞吐量可以相加
- **总吞吐量** (KB/s) - 读吞吐量 + 写吞吐量

### 不可叠加指标（Non-Additive Metrics）- 取最大值
这些指标表示延迟或利用率，取最大值更能反映系统瓶颈：
- **读延迟** (ms) - 取最大await_time
- **写延迟** (ms) - 取最大await_time
- **磁盘使用率** (%) - 取最大util
- **队列长度** - 取最大值
- **服务时间** (ms) - 取最大svctm

## 聚合层级

数据经过两层聚合：

### 第一层：节点聚合（processIOJitterMetrics）
对于相同设备、相同时间戳的多个节点数据：
- 可叠加指标：求和
- 不可叠加指标：取最大值

**示例**：
```
时间: 10:30:00, 设备: vdb
节点1: read_iops=100, write_iops=50, await_time=5ms, util=60%
节点2: read_iops=150, write_iops=80, await_time=8ms, util=70%

聚合后:
read_iops = 100 + 150 = 250 (求和)
write_iops = 50 + 80 = 130 (求和)
await_time = max(5, 8) = 8ms (最大值)
util = max(60, 70) = 70% (最大值)
```

### 第二层：设备聚合（updateAggregatedMetrics）
对于多个选中设备，在相同时间戳下：
- 可叠加指标：求和
- 不可叠加指标：取最大值

**示例**：
```
时间: 10:30:00
设备vdb: read_iops=250, await_time=8ms
设备vdc: read_iops=200, await_time=6ms

聚合后:
read_iops = 250 + 200 = 450 (求和)
await_time = max(8, 6) = 8ms (最大值)
```

## 修改的文件

### frontend/src/views/IOJitterChart.vue

#### 1. 模板修改（Template）

**节点选择器** - 改为多选：
```vue
<el-select
  v-model="selectedNodes"
  placeholder="选择节点（可多选）"
  multiple
  collapse-tags
  collapse-tags-tooltip
  style="width: 250px; margin-right: 10px"
  @change="loadIOJitterData"
>
  <el-option
    v-for="node in taskNodes"
    :key="node.id"
    :label="`${node.name} (${node.ip_address})`"
    :value="node.id"
  ></el-option>
</el-select>
```

**设备选择器** - 改为多选：
```vue
<el-select
  v-model="selectedDevices"
  placeholder="选择设备（可多选）"
  multiple
  collapse-tags
  collapse-tags-tooltip
  style="width: 250px; margin-right: 10px"
  @change="updateIOJitterChart"
>
  <el-option
    v-for="device in availableDevices"
    :key="device"
    :label="device"
    :value="device"
  ></el-option>
</el-select>
```

**聚合说明提示**：
```vue
<el-tooltip
  content="IOPS和吞吐量会叠加，延迟/使用率/服务时间取最大值"
  placement="top"
>
  <el-icon style="color: #909399; cursor: help; margin-right: 10px">
    <QuestionFilled />
  </el-icon>
</el-tooltip>
```

#### 2. Script修改

**新增导入**：
```javascript
import { QuestionFilled } from "@element-plus/icons-vue";
```

**状态变量更改**：
```javascript
// 从单选改为多选
const selectedNodes = ref([]);  // 原来是 selectedNode
const selectedDevices = ref([]);  // 原来是 selectedDevice
```

**loadTaskInfo函数** - 默认选择所有节点：
```javascript
const loadTaskInfo = async () => {
  try {
    const response = await getTask(taskId.value);
    if (response && response.data) {
      taskNodes.value = response.data.nodes;
      if (taskNodes.value.length > 0) {
        // 默认选择所有节点
        selectedNodes.value = taskNodes.value.map((node) => node.id);
        loadIOJitterData();
      }
    }
  } catch (error) {
    console.error("加载任务信息失败:", error);
  }
};
```

**loadIOJitterData函数** - 支持多节点：
```javascript
const loadIOJitterData = async () => {
  if (selectedNodes.value.length === 0) return;

  try {
    resetIOJitterData();

    // 收集所有节点的数据
    const allMetricsData = [];
    const allDevices = new Set();
    let lastLogId = null;

    // 遍历所有选中的节点
    for (const nodeId of selectedNodes.value) {
      const logsResponse = await getTaskLogs(taskId.value, {
        node_id: nodeId,
      });

      if (logsResponse && logsResponse.data) {
        const iostatLogs = logsResponse.data.filter(
          (log) => log.log_type === "iostat",
        );

        if (iostatLogs.length > 0) {
          const logId = iostatLogs[0].id;
          lastLogId = logId;

          const metricsResponse = await getIOStatMetrics(logId);
          if (metricsResponse && metricsResponse.data) {
            // 为每条metric添加node_id标记
            const metricsWithNode = metricsResponse.data.map((metric) => ({
              ...metric,
              node_id: nodeId,
            }));
            allMetricsData.push(...metricsWithNode);

            // 收集所有设备
            metricsWithNode.forEach((metric) => {
              if (metric.device) allDevices.add(metric.device);
            });
          }
        }
      }
    }

    // 更新可用设备列表
    availableDevices.value = Array.from(allDevices);

    // 默认选择所有设备
    if (selectedDevices.value.length === 0 && availableDevices.value.length > 0) {
      selectedDevices.value = [...availableDevices.value];
    }

    // 处理合并后的数据
    if (allMetricsData.length > 0) {
      processIOJitterMetrics(allMetricsData);
      updateIOJitterChart();

      if (lastLogId) {
        currentLogId.value = lastLogId;
        await loadJitterData(lastLogId);

        if (selectedYAxisMetrics.value.length > 0) {
          await loadCurrentMetricJitter(lastLogId, selectedYAxisMetrics.value[0]);
        }
      }
    }
  } catch (error) {
    console.error("加载IO抖动数据失败:", error);
  }
};
```

**processIOJitterMetrics函数** - 实现节点级聚合：
```javascript
const processIOJitterMetrics = (metrics) => {
  // 按时间排序
  metrics.sort(
    (a, b) => new Date(a.collection_time) - new Date(b.collection_time),
  );

  // 按时间戳和设备分组
  const timeDeviceMap = {};
  metrics.forEach((metric) => {
    const timestamp = new Date(metric.collection_time).toLocaleTimeString();
    if (!timeDeviceMap[timestamp]) {
      timeDeviceMap[timestamp] = {};
    }
    if (!timeDeviceMap[timestamp][metric.device]) {
      timeDeviceMap[timestamp][metric.device] = [];
    }
    timeDeviceMap[timestamp][metric.device].push(metric);
  });

  const timestamps = Object.keys(timeDeviceMap).sort();
  const devices = new Set();
  metrics.forEach((m) => devices.add(m.device));
  availableDevices.value = Array.from(devices);

  // 按设备处理数据
  const deviceData = {};
  Array.from(devices).forEach((device) => {
    deviceData[device] = {
      timestamps: [],
      readIOPS: [],
      writeIOPS: [],
      totalIOPS: [],
      readLatency: [],
      writeLatency: [],
      diskUtilization: [],
      readThroughput: [],
      writeThroughput: [],
      totalThroughput: [],
      queueLength: [],
      serviceTime: [],
    };

    timestamps.forEach((timestamp) => {
      const metricsAtTime = timeDeviceMap[timestamp][device] || [];
      if (metricsAtTime.length === 0) return;

      // 可叠加指标：求和
      const readIOPS = metricsAtTime.reduce((sum, m) => sum + (m.read_iops || 0), 0);
      const writeIOPS = metricsAtTime.reduce((sum, m) => sum + (m.write_iops || 0), 0);
      const readKbps = metricsAtTime.reduce((sum, m) => sum + (m.read_kbps || 0), 0);
      const writeKbps = metricsAtTime.reduce((sum, m) => sum + (m.write_kbps || 0), 0);

      // 不可叠加指标：取最大值
      const awaitTime = Math.max(...metricsAtTime.map((m) => m.await_time || 0));
      const util = Math.max(...metricsAtTime.map((m) => m.util || 0));
      const svctm = Math.max(...metricsAtTime.map((m) => m.svctm || 0));

      deviceData[device].timestamps.push(timestamp);
      deviceData[device].readIOPS.push(readIOPS);
      deviceData[device].writeIOPS.push(writeIOPS);
      deviceData[device].totalIOPS.push(readIOPS + writeIOPS);
      deviceData[device].readLatency.push(awaitTime);
      deviceData[device].writeLatency.push(awaitTime);
      deviceData[device].diskUtilization.push(util);
      deviceData[device].readThroughput.push(readKbps);
      deviceData[device].writeThroughput.push(writeKbps);
      deviceData[device].totalThroughput.push(readKbps + writeKbps);
      deviceData[device].queueLength.push(svctm > 0 ? awaitTime / svctm : 0);
      deviceData[device].serviceTime.push(svctm);
    });
  });

  iostatMetrics.devices = deviceData;

  if (selectedDevices.value.length > 0) {
    updateAggregatedMetrics();
  } else if (Object.keys(deviceData).length > 0) {
    const firstDevice = Object.keys(deviceData)[0];
    Object.assign(iostatMetrics, deviceData[firstDevice]);
  }
};
```

**新增updateAggregatedMetrics函数** - 设备级聚合：
```javascript
const updateAggregatedMetrics = () => {
  if (selectedDevices.value.length === 0) return;

  const selectedDeviceData = selectedDevices.value
    .map((device) => iostatMetrics.devices[device])
    .filter((data) => data && data.timestamps.length > 0);

  if (selectedDeviceData.length === 0) return;

  // 获取所有时间戳的并集
  const allTimestamps = new Set();
  selectedDeviceData.forEach((deviceData) => {
    deviceData.timestamps.forEach((ts) => allTimestamps.add(ts));
  });

  const sortedTimestamps = Array.from(allTimestamps).sort();

  const aggregated = {
    timestamps: sortedTimestamps,
    readIOPS: [],
    writeIOPS: [],
    totalIOPS: [],
    readLatency: [],
    writeLatency: [],
    diskUtilization: [],
    readThroughput: [],
    writeThroughput: [],
    totalThroughput: [],
    queueLength: [],
    serviceTime: [],
  };

  sortedTimestamps.forEach((timestamp) => {
    let readIOPS = 0,
      writeIOPS = 0,
      readKbps = 0,
      writeKbps = 0;
    let maxAwaitTime = 0,
      maxUtil = 0,
      maxSvctm = 0,
      maxQueueLength = 0;

    selectedDeviceData.forEach((deviceData) => {
      const idx = deviceData.timestamps.indexOf(timestamp);
      if (idx !== -1) {
        // 可叠加指标：求和
        readIOPS += deviceData.readIOPS[idx] || 0;
        writeIOPS += deviceData.writeIOPS[idx] || 0;
        readKbps += deviceData.readThroughput[idx] || 0;
        writeKbps += deviceData.writeThroughput[idx] || 0;

        // 不可叠加指标：取最大值
        maxAwaitTime = Math.max(maxAwaitTime, deviceData.readLatency[idx] || 0);
        maxUtil = Math.max(maxUtil, deviceData.diskUtilization[idx] || 0);
        maxSvctm = Math.max(maxSvctm, deviceData.serviceTime[idx] || 0);
        maxQueueLength = Math.max(
          maxQueueLength,
          deviceData.queueLength[idx] || 0,
        );
      }
    });

    aggregated.readIOPS.push(readIOPS);
    aggregated.writeIOPS.push(writeIOPS);
    aggregated.totalIOPS.push(readIOPS + writeIOPS);
    aggregated.readLatency.push(maxAwaitTime);
    aggregated.writeLatency.push(maxAwaitTime);
    aggregated.diskUtilization.push(maxUtil);
    aggregated.readThroughput.push(readKbps);
    aggregated.writeThroughput.push(writeKbps);
    aggregated.totalThroughput.push(readKbps + writeKbps);
    aggregated.queueLength.push(maxQueueLength);
    aggregated.serviceTime.push(maxSvctm);
  });

  Object.assign(iostatMetrics, aggregated);
};
```

**updateIOJitterChart函数** - 使用聚合数据：
```javascript
const updateIOJitterChart = async () => {
  if (!ioJitterChart) return;

  // 更新聚合指标
  if (selectedDevices.value.length > 0) {
    updateAggregatedMetrics();
  }

  // ... 其他代码 ...

  // 使用聚合后的数据
  const timeData = iostatMetrics.timestamps;

  // 所有系列数据使用iostatMetrics而不是deviceData
  const allSeries = {
    读IOPS: {
      name: "读IOPS",
      type: "line",
      data: iostatMetrics.readIOPS || [],
      // ...
    },
    // ... 其他指标
  };
};
```

**resetIOJitterData函数** - 重置多选状态：
```javascript
const resetIOJitterData = () => {
  iostatMetrics.timestamps = [];
  iostatMetrics.devices = {};
  iostatMetrics.readIOPS = [];
  iostatMetrics.writeIOPS = [];
  iostatMetrics.totalIOPS = [];
  iostatMetrics.readLatency = [];
  iostatMetrics.writeLatency = [];
  iostatMetrics.diskUtilization = [];
  iostatMetrics.readThroughput = [];
  iostatMetrics.writeThroughput = [];
  iostatMetrics.totalThroughput = [];
  iostatMetrics.queueLength = [];
  iostatMetrics.serviceTime = [];
  availableDevices.value = [];
  selectedDevices.value = [];  // 原来是 selectedDevice.value = ""
};
```

## UI改进

1. **多选下拉框**
   - 使用`multiple`属性启用多选
   - 使用`collapse-tags`属性折叠标签，节省空间
   - 使用`collapse-tags-tooltip`属性在hover时显示所有选中项

2. **信息提示**
   - 添加了问号图标，鼠标悬停显示聚合规则说明
   - 帮助用户理解数据聚合逻辑

3. **默认行为**
   - 默认选择所有节点
   - 默认选择所有设备
   - 用户可以自由调整选择

## 构建状态
✅ 前端成功构建
⚠️ 8个prettier格式警告（不影响功能）

## 测试建议

### 1. 基础功能测试
- [ ] 访问任务详情页面，点击"查看性能抖动图表"
- [ ] 验证节点下拉框显示所有节点，默认全选
- [ ] 验证设备下拉框显示所有设备，默认全选
- [ ] 验证问号图标提示正确显示聚合说明

### 2. 多节点测试
- [ ] 选择单个节点，验证图表显示正确
- [ ] 选择多个节点，验证IOPS和吞吐量值增加（叠加）
- [ ] 选择多个节点，验证延迟和使用率显示合理（最大值）
- [ ] 取消选择所有节点，验证图表清空

### 3. 多设备测试
- [ ] 选择单个设备，验证图表显示正确
- [ ] 选择多个设备，验证IOPS和吞吐量值增加（叠加）
- [ ] 选择多个设备，验证延迟和使用率显示合理（最大值）
- [ ] 取消选择所有设备，验证图表清空

### 4. 组合测试
- [ ] 选择2个节点 + 2个设备，验证数据聚合正确
- [ ] 切换不同的Y轴指标，验证图表更新
- [ ] 验证折叠标签功能，选择多项时标签折叠
- [ ] 鼠标悬停折叠标签，验证tooltip显示所有选项

### 5. 边界情况测试
- [ ] 只有一个节点的任务，验证功能正常
- [ ] 只有一个设备的节点，验证功能正常
- [ ] 节点没有iostat日志，验证错误处理
- [ ] 数据较多时，验证图表性能

## 预期数据示例

假设有以下数据：
- 节点1，设备vdb：read_iops=1000, write_iops=500, latency=10ms, util=60%
- 节点2，设备vdb：read_iops=1200, write_iops=600, latency=15ms, util=70%

选择两个节点后，聚合结果：
- read_iops = 1000 + 1200 = **2200** (求和)
- write_iops = 500 + 600 = **1100** (求和)
- latency = max(10, 15) = **15ms** (最大值)
- util = max(60, 70) = **70%** (最大值)

## 技术亮点

1. **两层聚合架构**
   - 第一层：相同设备不同节点的数据聚合
   - 第二层：不同设备的数据聚合
   - 清晰的职责分离

2. **正确的聚合策略**
   - 区分可叠加指标和不可叠加指标
   - IOPS/吞吐量求和：反映总体性能
   - 延迟/利用率取最大值：反映系统瓶颈

3. **响应式更新**
   - 节点选择变化 → 重新加载数据
   - 设备选择变化 → 重新聚合数据
   - 指标选择变化 → 更新图表显示

4. **良好的用户体验**
   - 默认全选，方便查看整体性能
   - 折叠标签，界面简洁
   - 提示说明，帮助理解

## 修复时间
2026-03-23

## 修复状态
✅ 已完成并构建成功
