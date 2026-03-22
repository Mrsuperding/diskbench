<template>
  <div class="fio-chart-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>FIO性能图表</span>
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
          @change="loadFIOData"
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
          @change="updateFIOChart"
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
          @change="updateFIOChart"
        >
          <el-option label="读IOPS" value="read_iops"></el-option>
          <el-option label="写IOPS" value="write_iops"></el-option>
          <el-option label="读吞吐量(KB/s)" value="read_bw"></el-option>
          <el-option label="写吞吐量(KB/s)" value="write_bw"></el-option>
          <el-option label="平均延迟(ms)" value="lat"></el-option>
          <el-option label="P99延迟(ms)" value="lat_p99"></el-option>
          <el-option label="P9999延迟(ms)" value="lat_p9999"></el-option>
          <el-option label="最大延迟(ms)" value="lat_max"></el-option>
        </el-select>
      </div>

      <div class="chart-container">
        <div ref="fioChartRef" class="performance-chart"></div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, reactive } from "vue";
import { useRouter, useRoute } from "vue-router";
import * as echarts from "echarts";
import tasksApi from "@/api/tasks";
import { getTaskLogs, getFIOResults } from "@/api/logs";

// 路由相关
const router = useRouter();
const route = useRoute();
const taskId = ref(route.params.id);

// 图表相关
const fioChartRef = ref(null);
let fioChart = null;

// 选择控件
const selectedNode = ref("");
const selectedDevice = ref("");
const selectedYAxisMetrics = ref(["lat_p99", "lat_p9999", "lat_max"]);

// 数据相关
const taskNodes = ref([]);
const availableDevices = ref([]);
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

// 返回任务详情
const goBack = () => {
  router.push(`/tasks/${taskId.value}`);
};

// 加载任务信息
const loadTaskInfo = async () => {
  try {
    console.log("加载任务信息开始，taskId:", taskId.value);
    const response = await tasksApi.getTask(taskId.value);
    console.log("加载任务信息成功，response:", response);
    if (response && response.data) {
      taskNodes.value = response.data.nodes;
      console.log("任务节点信息:", taskNodes.value);
      if (taskNodes.value.length > 0) {
        selectedNode.value = taskNodes.value[0].id;
        loadFIOData();
      }
    }
  } catch (error) {
    console.error("加载任务信息失败:", error);
  }
};

// 加载FIO数据
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
    console.log("获取任务日志成功:", logsResponse);
    if (logsResponse && logsResponse.data) {
      let logsData = logsResponse.data;
      if (logsResponse.data.items) {
        logsData = logsResponse.data.items;
      }
      const fioLogs = logsData.filter((log) => log.log_type === "fio");
      console.log("FIO日志:", fioLogs);

      if (fioLogs.length > 0) {
        // 按设备分组FIO日志 - 从文件名中提取设备信息
        const deviceLogs = {};
        fioLogs.forEach((log) => {
          // 尝试从log_filename中提取设备名
          // 例如: fio_vdb_20260323_123456.log -> vdb
          let device = "unknown";
          if (log.log_filename) {
            const match = log.log_filename.match(/fio_(\w+)_/);
            if (match && match[1]) {
              device = match[1];
            } else {
              // 尝试其他模式: vdb.log, vdb_fio.log等
              const match2 = log.log_filename.match(/(\w+)\.log/);
              if (match2 && match2[1] && match2[1] !== 'fio') {
                device = match2[1];
              }
            }
          }

          if (!deviceLogs[device]) {
            deviceLogs[device] = [];
          }
          deviceLogs[device].push(log);
        });

        console.log("FIO日志按设备分组:", deviceLogs);

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
            const metricsResponse = await getFIOResults(log.id);
            console.log(`获取FIO指标成功 (设备: ${device}):`, metricsResponse);

            if (metricsResponse && metricsResponse.data) {
              processFIOMetrics(metricsResponse.data, device, log.collection_time);
            }
          }
        }

        updateFIOChart();
      } else {
        console.error("没有找到FIO类型的日志");
      }
    } else {
      console.error("任务日志数据为空");
    }
  } catch (error) {
    console.error("加载FIO数据失败:", error);
  }
};

// 处理FIO指标数据
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

// 重置FIO数据
const resetFIOData = () => {
  fioMetrics.timestamps = [];
  fioMetrics.devices = {};
  fioMetrics.read_iops = [];
  fioMetrics.write_iops = [];
  fioMetrics.read_bw = [];
  fioMetrics.write_bw = [];
  fioMetrics.lat = [];
  fioMetrics.lat_p99 = [];
  fioMetrics.lat_p9999 = [];
  fioMetrics.lat_max = [];
  availableDevices.value = [];
  selectedDevice.value = "";
};

// 初始化FIO图表
const initFIOChart = () => {
  if (fioChartRef.value) {
    fioChart = echarts.init(fioChartRef.value);

    // 初始配置
    fioChart.setOption({
      title: {
        text: "FIO性能监控",
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
  if (fioChart) {
    fioChart.resize();
  }
};

// 更新IOSTAT图表
const updateFIOChart = () => {
  if (!fioChart || !selectedDevice.value) return;

  // 获取指标对应的颜色
  const getMetricColor = (metric) => {
    const colorMap = {
      read_iops: "#36cbcb",
      write_iops: "#f6bd16",
      read_bw: "#1890ff",
      write_bw: "#722ed1",
      lat: "#52c41a",
      lat_p99: "#eb2f96",
      lat_p9999: "#fa8c16",
      lat_max: "#f5222d",
    };
    return colorMap[metric] || "#ccc";
  };

  // 获取指标显示名称
  const getMetricLabel = (metric) => {
    const labelMap = {
      read_iops: "读IOPS",
      write_iops: "写IOPS",
      read_bw: "读吞吐量 (KB/s)",
      write_bw: "写吞吐量 (KB/s)",
      lat: "平均延迟 (ms)",
      lat_p99: "P99延迟 (ms)",
      lat_p9999: "P9999延迟 (ms)",
      lat_max: "最大延迟 (ms)",
    };
    return labelMap[metric] || metric;
  };

  // 使用当前设备的FIO数据
  const timeData = fioMetrics.timestamps;

  // 如果没有FIO数据，显示空图表
  if (timeData.length === 0) {
    fioChart.setOption({
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
    data: fioMetrics[metric],
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
  fioChart.setOption({
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
  if (metric.includes("_bw")) return "吞吐量 (KB/s)";
  if (metric.includes("lat")) return "延迟 (ms)";
  return "值";
};

// 组件挂载时
onMounted(() => {
  // 初始化图表
  initFIOChart();
  // 加载任务信息
  loadTaskInfo();
});

// 组件卸载时
onUnmounted(() => {
  // 销毁图表实例
  if (fioChart) {
    fioChart.dispose();
  }
  // 移除窗口大小变化监听
  window.removeEventListener("resize", handleResize);
});
</script>

<style scoped>
.fio-chart-container {
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
