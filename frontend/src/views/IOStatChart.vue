<template>
  <div class="iostat-chart-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>IOSTAT性能图表</span>
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
          @change="loadIOStatData"
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
          @change="updateIOStatChart"
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
          @change="updateIOStatChart"
        >
          <el-option label="读IOPS" value="read_iops"></el-option>
          <el-option label="写IOPS" value="write_iops"></el-option>
          <el-option label="读吞吐量" value="read_kbps"></el-option>
          <el-option label="写吞吐量" value="write_kbps"></el-option>
          <el-option label="IO等待时间" value="await_time"></el-option>
          <el-option label="服务时间" value="svctm"></el-option>
          <el-option label="磁盘使用率" value="util"></el-option>
        </el-select>
      </div>

      <div class="chart-container">
        <div ref="iostatChartRef" class="performance-chart"></div>
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
const iostatChartRef = ref(null);
let iostatChart = null;

// 选择控件
const selectedNode = ref("");
const selectedDevice = ref("");
const selectedYAxisMetrics = ref(["read_iops", "write_iops"]);

// 数据相关
const taskNodes = ref([]);
const availableDevices = ref([]);
const iostatMetrics = reactive({
  timestamps: [],
  devices: {},
  read_iops: [],
  write_iops: [],
  read_kbps: [],
  write_kbps: [],
  await: [],
  svctm: [],
  util: [],
});

// 返回任务详情
const goBack = () => {
  router.push(`/tasks/${taskId.value}`);
};

// 加载任务信息
const loadTaskInfo = async () => {
  try {
    console.log("加载任务信息开始，taskId:", taskId.value);
    const response = await getTask(taskId.value);
    console.log("加载任务信息成功，response:", response);
    if (response && response.data) {
      taskNodes.value = response.data.nodes;
      console.log("任务节点信息:", taskNodes.value);
      if (taskNodes.value.length > 0) {
        selectedNode.value = taskNodes.value[0].id;
        loadIOStatData();
      }
    }
  } catch (error) {
    console.error("加载任务信息失败:", error);
  }
};

// 加载IOSTAT数据
const loadIOStatData = async () => {
  if (!selectedNode.value) return;

  try {
    console.log("加载IOSTAT数据开始，selectedNode:", selectedNode.value);
    // 重置数据
    resetIOStatData();

    // 获取任务的测试日志
    const logsResponse = await getTaskLogs(taskId.value, {
      node_id: selectedNode.value,
    });
    console.log("获取任务日志成功:", logsResponse);
    if (logsResponse && logsResponse.data) {
      const iostatLogs = logsResponse.data.filter(
        (log) => log.log_type === "iostat",
      );
      console.log("IOSTAT日志:", iostatLogs);

      if (iostatLogs.length > 0) {
        // 获取iostat日志的指标数据
        const logId = iostatLogs[0].id;
        const metricsResponse = await getIOStatMetrics(logId);
        console.log("获取IOSTAT指标成功:", metricsResponse);

        if (metricsResponse && metricsResponse.data) {
          processIOStatMetrics(metricsResponse.data);
          updateIOStatChart();
        }
      }
    }
  } catch (error) {
    console.error("加载IOSTAT数据失败:", error);
  }
};

// 处理IOSTAT指标数据
const processIOStatMetrics = (metrics) => {
  console.log("处理IOSTAT指标数据:", metrics);
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
        read_iops: [],
        write_iops: [],
        read_kbps: [],
        write_kbps: [],
        await_time: [],
        svctm: [],
        util: [],
      };
    }

    deviceData[metric.device].timestamps.push(timestamp);
    deviceData[metric.device].read_iops.push(metric.read_iops);
    deviceData[metric.device].write_iops.push(metric.write_iops);
    deviceData[metric.device].read_kbps.push(metric.read_kbps);
    deviceData[metric.device].write_kbps.push(metric.write_kbps);
    deviceData[metric.device].await_time.push(metric.await_time);
    deviceData[metric.device].svctm.push(metric.svctm);
    deviceData[metric.device].util.push(metric.util);
  });

  // 更新可用设备列表
  availableDevices.value = Array.from(devices);
  console.log("可用设备列表:", availableDevices.value);
  if (availableDevices.value.length > 0 && !selectedDevice.value) {
    selectedDevice.value = availableDevices.value[0];
  }

  // 更新iostatMetrics
  iostatMetrics.devices = deviceData;

  // 设置当前设备的数据
  if (selectedDevice.value && deviceData[selectedDevice.value]) {
    const deviceData = deviceData[selectedDevice.value];
    iostatMetrics.timestamps = deviceData.timestamps;
    iostatMetrics.read_iops = deviceData.read_iops;
    iostatMetrics.write_iops = deviceData.write_iops;
    iostatMetrics.read_kbps = deviceData.read_kbps;
    iostatMetrics.write_kbps = deviceData.write_kbps;
    iostatMetrics.await_time = deviceData.await_time;
    iostatMetrics.svctm = deviceData.svctm;
    iostatMetrics.util = deviceData.util;
  }
};

// 重置IOSTAT数据
const resetIOStatData = () => {
  iostatMetrics.timestamps = [];
  iostatMetrics.devices = {};
  iostatMetrics.read_iops = [];
  iostatMetrics.write_iops = [];
  iostatMetrics.read_kbps = [];
  iostatMetrics.write_kbps = [];
  iostatMetrics.await = [];
  iostatMetrics.svctm = [];
  iostatMetrics.util = [];
  availableDevices.value = [];
  selectedDevice.value = "";
};

// 初始化IOSTAT图表
const initIOStatChart = () => {
  if (iostatChartRef.value) {
    iostatChart = echarts.init(iostatChartRef.value);

    // 初始配置
    iostatChart.setOption({
      title: {
        text: "IOSTAT性能监控",
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
        data: [],
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
      series: [],
    });

    // 监听窗口大小变化
    window.addEventListener("resize", handleResize);
  }
};

// 处理窗口大小变化
const handleResize = () => {
  if (iostatChart) {
    iostatChart.resize();
  }
};

// 更新IOSTAT图表
const updateIOStatChart = () => {
  if (!iostatChart || !selectedDevice.value) return;

  // 获取指标对应的颜色
  const getMetricColor = (metric) => {
    const colorMap = {
      read_iops: "#36cbcb",
      write_iops: "#f6bd16",
      read_kbps: "#1890ff",
      write_kbps: "#722ed1",
      await: "#eb2f96",
      svctm: "#fa8c16",
      util: "#f5222d",
    };
    return colorMap[metric] || "#ccc";
  };

  // 获取指标显示名称
  const getMetricLabel = (metric) => {
    const labelMap = {
      read_iops: "读IOPS",
      write_iops: "写IOPS",
      read_kbps: "读吞吐量 (KB/s)",
      write_kbps: "写吞吐量 (KB/s)",
      await: "IO等待时间 (ms)",
      svctm: "服务时间 (ms)",
      util: "磁盘使用率 (%)",
    };
    return labelMap[metric] || metric;
  };

  // 使用当前设备的iostat数据
  const timeData = iostatMetrics.timestamps;

  // 如果没有iostat数据，显示空图表
  if (timeData.length === 0) {
    iostatChart.setOption({
      legend: {
        data: [],
        bottom: 0,
      },
      yAxis: {
        type: "value",
        name: "IOPS",
      },
      xAxis: {
        data: [],
      },
      series: [],
    });
    return;
  }

  // 根据选择的指标生成系列数据
  const selectedSeries = selectedYAxisMetrics.value.map((metric) => ({
    name: getMetricLabel(metric),
    type: "line",
    data: iostatMetrics[metric],
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
  }));

  // 更新图表配置
  iostatChart.setOption({
    legend: {
      data: selectedYAxisMetrics.value.map(getMetricLabel),
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
  if (metric.includes("iops")) return "IOPS";
  if (metric.includes("kbps")) return "吞吐量 (KB/s)";
  if (metric.includes("await") || metric.includes("svctm")) return "时间 (ms)";
  if (metric.includes("util")) return "使用率 (%)";
  return "值";
};

// 组件挂载时
onMounted(() => {
  // 初始化图表
  initIOStatChart();
  // 加载任务信息
  loadTaskInfo();
});

// 组件卸载时
onUnmounted(() => {
  // 销毁图表实例
  if (iostatChart) {
    iostatChart.dispose();
  }
  // 移除窗口大小变化监听
  window.removeEventListener("resize", handleResize);
});
</script>

<style scoped>
.iostat-chart-container {
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
