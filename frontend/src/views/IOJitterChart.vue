<template>
  <div class="io-jitter-chart-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>IO性能抖动图表</span>
          <el-button type="primary" size="small" @click="goBack"
            >返回任务详情</el-button
          >
        </div>
      </template>

      <div class="chart-controls">
        <el-select
          v-model="selectedNode"
          placeholder="选择节点"
          style="width: 200px; margin-right: 10px"
          @change="loadIOJitterData"
        >
          <el-option
            v-for="node in taskNodes"
            :key="node.id"
            :label="node.name"
            :value="node.id"
          ></el-option>
        </el-select>

        <el-select
          v-model="selectedDevice"
          placeholder="选择设备"
          style="width: 200px; margin-right: 10px"
          @change="updateIOJitterChart"
        >
          <el-option
            v-for="device in availableDevices"
            :key="device"
            :label="device"
            :value="device"
          ></el-option>
        </el-select>

        <el-select
          v-model="selectedYAxisMetrics"
          placeholder="选择Y轴指标"
          multiple
          style="width: 300px"
          @change="updateIOJitterChart"
        >
          <el-option label="读IOPS" value="读IOPS"></el-option>
          <el-option label="写IOPS" value="写IOPS"></el-option>
          <el-option label="总IOPS" value="总IOPS"></el-option>
          <el-option label="读延迟" value="读延迟"></el-option>
          <el-option label="写延迟" value="写延迟"></el-option>
          <el-option label="磁盘使用率" value="磁盘使用率"></el-option>
          <el-option label="读吞吐量" value="读吞吐量"></el-option>
          <el-option label="写吞吐量" value="写吞吐量"></el-option>
          <el-option label="总吞吐量" value="总吞吐量"></el-option>
          <el-option label="队列长度" value="队列长度"></el-option>
          <el-option label="服务时间" value="服务时间"></el-option>
        </el-select>
      </div>

      <div class="chart-container">
        <div ref="ioJitterChartRef" class="performance-chart"></div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, reactive } from "vue";
import { useRouter, useRoute } from "vue-router";
import * as echarts from "echarts";
import { getTask, getTaskLogs, getIOStatMetrics } from "@/api/tasks";

// 路由相关
const router = useRouter();
const route = useRoute();
const taskId = ref(route.params.id);

// 图表相关
const ioJitterChartRef = ref(null);
let ioJitterChart = null;
const selectedYAxisMetrics = ref(["读IOPS", "写IOPS", "总IOPS"]);

// 选择控件
const selectedNode = ref("");
const selectedDevice = ref("");

// 数据相关
const taskNodes = ref([]);
const availableDevices = ref([]);
const iostatMetrics = reactive({
  timestamps: [],
  devices: {},
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
});

// 返回任务详情
const goBack = () => {
  router.push(`/tasks/${taskId.value}`);
};

// 初始化IO抖动图表
const initIOJitterChart = () => {
  if (ioJitterChartRef.value) {
    ioJitterChart = echarts.init(ioJitterChartRef.value);

    // 初始配置
    ioJitterChart.setOption({
      title: {
        text: "IO性能抖动监控",
        left: "center",
      },
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "cross",
          label: {
            backgroundColor: "#6a7985",
          },
        },
      },
      legend: {
        data: selectedYAxisMetrics.value,
        bottom: 0,
      },
      grid: {
        left: "3%",
        right: "4%",
        bottom: "10%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: [],
      },
      yAxis: {
        type: "value",
        name: "IOPS",
      },
      series: selectedYAxisMetrics.value.map((metric) => ({
        name: metric,
        type: "line",
        data: [],
        smooth: true,
      })),
    });

    // 监听窗口大小变化
    window.addEventListener("resize", handleResize);
  }
};

// 处理窗口大小变化
const handleResize = () => {
  if (ioJitterChart) {
    ioJitterChart.resize();
  }
};

// 更新IO抖动图表
const updateIOJitterChart = () => {
  if (!ioJitterChart) return;

  // 获取当前选中设备的数据
  const deviceData = selectedDevice.value && iostatMetrics.devices[selectedDevice.value] 
    ? iostatMetrics.devices[selectedDevice.value] 
    : (Object.values(iostatMetrics.devices)[0] || { timestamps: [] });

  // 获取指标对应的颜色
  const getMetricColor = (metric) => {
    const colorMap = {
      读IOPS: "#36cbcb",
      写IOPS: "#f6bd16",
      总IOPS: "#52c41a",
      读延迟: "#87d068",
      写延迟: "#13c2c2",
      磁盘使用率: "#2f54eb",
      读吞吐量: "#722ed1",
      写吞吐量: "#eb2f96",
      总吞吐量: "#fa541c",
      队列长度: "#a0d911",
      服务时间: "#fa8c16",
    };
    return colorMap[metric] || "#888";
  };

  // 准备时间数据
  const timeData = deviceData.timestamps;

  // 如果没有iostat数据，显示空图表
  if (timeData.length === 0) {
    ioJitterChart.setOption({
      legend: {
        data: selectedYAxisMetrics.value,
        bottom: 0,
      },
      yAxis: {
        type: "value",
        name: "IOPS",
      },
      xAxis: {
        data: [],
      },
      series: selectedYAxisMetrics.value.map((metric) => ({
        name: metric,
        type: "line",
        data: [],
        smooth: true,
        lineStyle: {
          color: getMetricColor(metric),
        },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: `${getMetricColor(metric)}80` }, // 50% opacity
              { offset: 1, color: `${getMetricColor(metric)}10` }, // 10% opacity
            ],
          },
        },
      })),
    });
    return;
  }

  // 准备所有可能的系列数据
  const allSeries = {
    读IOPS: {
      name: "读IOPS",
      type: "line",
      data: deviceData.readIOPS || [],
      smooth: true,
      lineStyle: { color: getMetricColor("读IOPS") },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: `${getMetricColor("读IOPS")}80` },
            { offset: 1, color: `${getMetricColor("读IOPS")}10` },
          ],
        },
      },
    },
    写IOPS: {
      name: "写IOPS",
      type: "line",
      data: deviceData.writeIOPS || [],
      smooth: true,
      lineStyle: { color: getMetricColor("写IOPS") },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: `${getMetricColor("写IOPS")}80` },
            { offset: 1, color: `${getMetricColor("写IOPS")}10` },
          ],
        },
      },
    },
    总IOPS: {
      name: "总IOPS",
      type: "line",
      data: deviceData.totalIOPS || [],
      smooth: true,
      lineStyle: { color: getMetricColor("总IOPS") },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: `${getMetricColor("总IOPS")}80` },
            { offset: 1, color: `${getMetricColor("总IOPS")}10` },
          ],
        },
      },
    },
    读延迟: {
      name: "读延迟",
      type: "line",
      data: deviceData.readLatency || [],
      smooth: true,
      lineStyle: { color: getMetricColor("读延迟") },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: `${getMetricColor("读延迟")}80` },
            { offset: 1, color: `${getMetricColor("读延迟")}10` },
          ],
        },
      },
    },
    写延迟: {
      name: "写延迟",
      type: "line",
      data: deviceData.writeLatency || [],
      smooth: true,
      lineStyle: { color: getMetricColor("写延迟") },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: `${getMetricColor("写延迟")}80` },
            { offset: 1, color: `${getMetricColor("写延迟")}10` },
          ],
        },
      },
    },
    磁盘使用率: {
      name: "磁盘使用率",
      type: "line",
      data: deviceData.diskUtilization || [],
      smooth: true,
      lineStyle: { color: getMetricColor("磁盘使用率") },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: `${getMetricColor("磁盘使用率")}80` },
            { offset: 1, color: `${getMetricColor("磁盘使用率")}10` },
          ],
        },
      },
    },
    读吞吐量: {
      name: "读吞吐量",
      type: "line",
      data: deviceData.readThroughput || [],
      smooth: true,
      lineStyle: { color: getMetricColor("读吞吐量") },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: `${getMetricColor("读吞吐量")}80` },
            { offset: 1, color: `${getMetricColor("读吞吐量")}10` },
          ],
        },
      },
    },
    写吞吐量: {
      name: "写吞吐量",
      type: "line",
      data: deviceData.writeThroughput || [],
      smooth: true,
      lineStyle: { color: getMetricColor("写吞吐量") },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: `${getMetricColor("写吞吐量")}80` },
            { offset: 1, color: `${getMetricColor("写吞吐量")}10` },
          ],
        },
      },
    },
    总吞吐量: {
      name: "总吞吐量",
      type: "line",
      data: deviceData.totalThroughput || [],
      smooth: true,
      lineStyle: { color: getMetricColor("总吞吐量") },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: `${getMetricColor("总吞吐量")}80` },
            { offset: 1, color: `${getMetricColor("总吞吐量")}10` },
          ],
        },
      },
    },
    队列长度: {
      name: "队列长度",
      type: "line",
      data: deviceData.queueLength || [],
      smooth: true,
      lineStyle: { color: getMetricColor("队列长度") },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: `${getMetricColor("队列长度")}80` },
            { offset: 1, color: `${getMetricColor("队列长度")}10` },
          ],
        },
      },
    },
    服务时间: {
      name: "服务时间",
      type: "line",
      data: deviceData.serviceTime || [],
      smooth: true,
      lineStyle: { color: getMetricColor("服务时间") },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: `${getMetricColor("服务时间")}80` },
            { offset: 1, color: `${getMetricColor("服务时间")}10` },
          ],
        },
      },
    },
  };

  // 根据选择的指标生成系列数据
  const selectedSeries = selectedYAxisMetrics.value.map(
    (metric) => allSeries[metric],
  );

  // 更新图表配置
  ioJitterChart.setOption({
    legend: {
      data: selectedYAxisMetrics.value,
    },
    yAxis: {
      type: "value",
      name:
        selectedYAxisMetrics.value.length > 0
          ? getYAxisName(selectedYAxisMetrics.value[0])
          : "IOPS",
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: timeData,
    },
    series: selectedSeries,
  });
};

// 获取Y轴名称
const getYAxisName = (metric) => {
  if (metric.includes("IOPS")) return "IOPS";
  if (metric.includes("延迟")) return "延迟 (ms)";
  if (metric.includes("使用率")) return "使用率 (%)";
  if (metric.includes("吞吐量")) return "吞吐量 (KB/s)";
  if (metric.includes("队列长度")) return "队列长度";
  if (metric.includes("服务时间")) return "服务时间 (ms)";
  return "值";
};



// 加载任务信息
const loadTaskInfo = async () => {
  try {
    const response = await getTask(taskId.value);
    if (response && response.data) {
      taskNodes.value = response.data.nodes;
      if (taskNodes.value.length > 0) {
        selectedNode.value = taskNodes.value[0].id;
        loadIOJitterData();
      }
    }
  } catch (error) {
    console.error("加载任务信息失败:", error);
  }
};

// 加载IO抖动数据
const loadIOJitterData = async () => {
  if (!selectedNode.value) return;

  try {
    // 重置数据
    resetIOJitterData();

    // 获取任务的测试日志
    const logsResponse = await getTaskLogs(taskId.value, {
      node_id: selectedNode.value,
    });
    if (logsResponse && logsResponse.data) {
      const iostatLogs = logsResponse.data.filter(
        (log) => log.log_type === "iostat",
      );

      if (iostatLogs.length > 0) {
        // 获取iostat日志的指标数据
        const logId = iostatLogs[0].id;
        const metricsResponse = await getIOStatMetrics(logId);

        if (metricsResponse && metricsResponse.data) {
          processIOJitterMetrics(metricsResponse.data);
          updateIOJitterChart();
        }
      }
    }
  } catch (error) {
    console.error("加载IO抖动数据失败:", error);
  }
};

// 处理IO抖动指标数据
const processIOJitterMetrics = (metrics) => {
  // 按时间排序
  metrics.sort(
    (a, b) => new Date(a.collection_time) - new Date(b.collection_time),
  );

  // 设备集合
  const devices = new Set();

  // 按设备分组数据
  const deviceData = {};

  metrics.forEach((metric) => {
    const timestamp = new Date(metric.collection_time).toLocaleTimeString();
    devices.add(metric.device);

    if (!deviceData[metric.device]) {
      deviceData[metric.device] = {
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
    }

    deviceData[metric.device].timestamps.push(timestamp);
    deviceData[metric.device].readIOPS.push(metric.read_iops);
    deviceData[metric.device].writeIOPS.push(metric.write_iops);
    deviceData[metric.device].totalIOPS.push(metric.read_iops + metric.write_iops);
    deviceData[metric.device].readLatency.push(metric.await_time); // 假设await_time是读延迟
    deviceData[metric.device].writeLatency.push(metric.await_time); // 假设await_time是写延迟
    deviceData[metric.device].diskUtilization.push(metric.util);
    deviceData[metric.device].readThroughput.push(metric.read_kbps);
    deviceData[metric.device].writeThroughput.push(metric.write_kbps);
    deviceData[metric.device].totalThroughput.push(metric.read_kbps + metric.write_kbps);
    deviceData[metric.device].queueLength.push(metric.await_time / metric.svctm); // 简化计算队列长度
    deviceData[metric.device].serviceTime.push(metric.svctm);
  });

  // 更新可用设备列表
  availableDevices.value = Array.from(devices);
  if (availableDevices.value.length > 0 && !selectedDevice.value) {
    selectedDevice.value = availableDevices.value[0];
  }

  // 更新iostatMetrics
  iostatMetrics.devices = deviceData;
};

// 重置IO抖动数据
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
  selectedDevice.value = "";
};

// 组件挂载时
onMounted(() => {
  // 初始化图表
  initIOJitterChart();
  // 加载任务信息
  loadTaskInfo();
});

// 组件卸载时
onUnmounted(() => {
  // 销毁图表实例
  if (ioJitterChart) {
    ioJitterChart.dispose();
  }
  // 移除窗口大小变化监听
  window.removeEventListener("resize", handleResize);
});
</script>

<style scoped>
.io-jitter-chart-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-controls {
  margin: 20px 0;
}

.chart-container {
  height: 500px;
}

.performance-chart {
  width: 100%;
  height: 100%;
}
</style>
