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

      <!-- 抖动统计信息 -->
      <div class="jitter-stats" v-if="jitterStats.available">
        <el-card shadow="hover" class="stats-card">
          <template #header>
            <span>性能抖动统计信息</span>
          </template>
          <div class="stats-grid">
            <el-statistic title="均值" :value="jitterStats.mean" :precision="2">
              <template #suffix>{{ jitterStats.unit }}</template>
            </el-statistic>
            <el-statistic
              title="标准差"
              :value="jitterStats.std_dev"
              :precision="2"
            >
              <template #suffix>{{ jitterStats.unit }}</template>
            </el-statistic>
            <el-statistic
              title="抖动百分比"
              :value="jitterStats.jitter_percent"
              :precision="2"
            >
              <template #suffix>%</template>
            </el-statistic>
            <el-statistic
              title="最小值"
              :value="jitterStats.min"
              :precision="2"
            >
              <template #suffix>{{ jitterStats.unit }}</template>
            </el-statistic>
            <el-statistic
              title="最大值"
              :value="jitterStats.max"
              :precision="2"
            >
              <template #suffix>{{ jitterStats.unit }}</template>
            </el-statistic>
            <el-statistic
              title="50%分位值"
              :value="jitterStats.p50"
              :precision="2"
            >
              <template #suffix>{{ jitterStats.unit }}</template>
            </el-statistic>
            <el-statistic
              title="90%分位值"
              :value="jitterStats.p90"
              :precision="2"
            >
              <template #suffix>{{ jitterStats.unit }}</template>
            </el-statistic>
            <el-statistic
              title="99%分位值"
              :value="jitterStats.p99"
              :precision="2"
            >
              <template #suffix>{{ jitterStats.unit }}</template>
            </el-statistic>
          </div>
        </el-card>
      </div>

      <!-- 指标抖动概览 -->
      <div class="jitter-overview" v-if="jitterOverview.length > 0">
        <el-card shadow="hover" class="overview-card">
          <template #header>
            <span>各指标抖动概览</span>
          </template>
          <div class="overview-grid">
            <div
              v-for="item in jitterOverview"
              :key="item.metric"
              class="overview-item"
            >
              <div class="overview-metric">{{ item.metric }}</div>
              <div class="overview-value">
                <el-progress
                  :percentage="Math.min(item.jitter_percent, 100)"
                  :color="getJitterColor(item.jitter_percent)"
                  :format="(percentage) => `${item.jitter_percent.toFixed(2)}%`"
                ></el-progress>
              </div>
              <div class="overview-label">
                {{ getJitterLevel(item.jitter_percent) }}
              </div>
            </div>
          </div>
        </el-card>
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
import { io } from "socket.io-client";
import { getTask } from "@/api/tasks";
import {
  getTaskLogs,
  getIOStatMetrics,
  getJitterData,
  getIOStatJitter,
} from "@/api/logs";

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

// 抖动统计数据
const jitterStats = reactive({
  available: false,
  mean: 0,
  std_dev: 0,
  jitter_percent: 0,
  min: 0,
  max: 0,
  p50: 0,
  p90: 0,
  p99: 0,
  unit: "",
});

// 各指标抖动概览
const jitterOverview = ref([]);

// 当前日志ID
const currentLogId = ref("");

// WebSocket相关
const socket = ref(null);

// 返回任务详情
const goBack = () => {
  router.push(`/tasks/${taskId.value}`);
};

// 初始化WebSocket连接
  const initWebSocket = () => {
    console.log("初始化WebSocket连接，任务ID:", taskId.value);
    // 创建WebSocket连接
    socket.value = io("http://localhost:5002", {
      transports: ["websocket"],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

  // 连接成功
  socket.value.on("connect", () => {
    console.log("WebSocket连接成功");
    // 加入任务日志房间
    socket.value.emit("join_task_room", { task_id: taskId.value });
  });

  // 接收任务日志
  socket.value.on("task_log", (data) => {
    console.log("收到任务日志:", data);
    let logContent = "";

    // 处理不同格式的日志数据
    if (data && typeof data === "object") {
      if (data.log) {
        logContent = data.log;
      } else if (data.type === "iostat") {
        // 如果是直接的iostat数据对象，立即更新图表
        processIOJitterMetrics([data.metrics]);
        updateIOJitterChart();
        return;
      } else {
        logContent = JSON.stringify(data);
      }
    } else if (typeof data === "string") {
      logContent = data;
    }

    // 尝试解析iostat日志行
    if (typeof logContent === "string") {
      // 如果是iostat日志，重新加载数据
      if (
        logContent.includes("Device:") ||
        logContent.includes("await") ||
        logContent.includes("util")
      ) {
        // 延迟重新加载数据，确保日志文件已写入
        setTimeout(() => {
          loadIOJitterData();
        }, 1000);
      }
    }
  });

  // 接收连接响应
  socket.value.on("connect_response", (data) => {
    console.log("连接响应:", data);
  });

  // 接收加入房间响应
  socket.value.on("join_room_response", (data) => {
    console.log("加入房间响应:", data);
  });

  // 接收错误
  socket.value.on("error", (error) => {
    console.error("WebSocket错误:", error);
  });

  // 接收连接断开
  socket.value.on("disconnect", (reason) => {
    console.log("WebSocket连接断开:", reason);
  });

  // 接收重连尝试
  socket.value.on("reconnect_attempt", (attempt) => {
    console.log(`WebSocket重连尝试 ${attempt}`);
  });

  // 接收重连成功
  socket.value.on("reconnect", (attempt) => {
    console.log(`WebSocket重连成功，尝试次数: ${attempt}`);
    // 重新加入任务日志房间
    socket.value.emit("join_task_room", { task_id: taskId.value });
  });

  // 接收重连失败
  socket.value.on("reconnect_failed", () => {
    console.error("WebSocket重连失败");
  });
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
const updateIOJitterChart = async () => {
  if (!ioJitterChart) return;

  // 获取当前选中设备的数据
  const deviceData =
    selectedDevice.value && iostatMetrics.devices[selectedDevice.value]
      ? iostatMetrics.devices[selectedDevice.value]
      : Object.values(iostatMetrics.devices)[0] || { timestamps: [] };

  // 如果切换了指标，更新抖动统计信息
  if (selectedYAxisMetrics.value.length > 0 && currentLogId.value) {
    await loadCurrentMetricJitter(
      currentLogId.value,
      selectedYAxisMetrics.value[0],
    );
  }

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

// 获取抖动水平
const getJitterLevel = (jitterPercent) => {
  if (jitterPercent < 5) return "低";
  if (jitterPercent < 20) return "中";
  return "高";
};

// 获取抖动颜色
const getJitterColor = (jitterPercent) => {
  if (jitterPercent < 5) return "#52c41a"; // 绿色
  if (jitterPercent < 20) return "#faad14"; // 黄色
  return "#f5222d"; // 红色
};

// 获取抖动数据
const loadJitterData = async (logId) => {
  try {
    // 获取IOSTAT指标的抖动计算结果
    const response = await getIOStatJitter(logId);
    if (response && response.data) {
      // 构建各指标抖动概览
      const overview = [];
      if (response.data.iops) {
        overview.push({
          metric: "IOPS",
          jitter_percent: response.data.iops.jitter_percent,
        });
      }
      if (response.data.bandwidth) {
        overview.push({
          metric: "带宽",
          jitter_percent: response.data.bandwidth.jitter_percent,
        });
      }
      if (response.data.latency) {
        overview.push({
          metric: "延迟",
          jitter_percent: response.data.latency.jitter_percent,
        });
      }
      jitterOverview.value = overview;
    }
  } catch (error) {
    console.error("加载抖动数据失败:", error);
  }
};

// 获取当前选中指标的抖动数据
const loadCurrentMetricJitter = async (logId, metricType) => {
  try {
    // 计算metricType对应的后端指标类型
    let backendMetricType = "iops";
    if (metricType.includes("吞吐量")) {
      backendMetricType = "bandwidth";
    } else if (metricType.includes("延迟") || metricType.includes("服务时间")) {
      backendMetricType = "latency";
    }

    const response = await getJitterData(logId, {
      metric_type: backendMetricType,
    });
    if (response && response.data) {
      const jitter = response.data.jitter;

      // 更新抖动统计信息
      jitterStats.available = true;
      jitterStats.mean = jitter.mean;
      jitterStats.std_dev = jitter.std_dev;
      jitterStats.jitter_percent = jitter.jitter_percent;
      jitterStats.min = jitter.min;
      jitterStats.max = jitter.max;
      jitterStats.p50 = jitter.p50;
      jitterStats.p90 = jitter.p90;
      jitterStats.p99 = jitter.p99;

      // 设置单位
      if (backendMetricType === "iops") {
        jitterStats.unit = "IOPS";
      } else if (backendMetricType === "bandwidth") {
        jitterStats.unit = "KB/s";
      } else if (backendMetricType === "latency") {
        jitterStats.unit = "ms";
      }
    }
  } catch (error) {
    console.error("加载当前指标抖动数据失败:", error);
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
        currentLogId.value = logId;

        // 获取IOSTAT指标数据
        const metricsResponse = await getIOStatMetrics(logId);
        if (metricsResponse && metricsResponse.data) {
          processIOJitterMetrics(metricsResponse.data);
          updateIOJitterChart();
        }

        // 获取抖动数据
        await loadJitterData(logId);

        // 获取当前选中指标的抖动数据
        if (selectedYAxisMetrics.value.length > 0) {
          await loadCurrentMetricJitter(logId, selectedYAxisMetrics.value[0]);
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

  // 如果是单个指标对象，直接添加到现有数据中
  if (metrics.length === 1 && typeof metrics[0] === 'object') {
    const metric = metrics[0];
    const timestamp = new Date(metric.collection_time).toLocaleTimeString();
    devices.add(metric.device);

    if (!iostatMetrics.devices[metric.device]) {
      iostatMetrics.devices[metric.device] = {
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

    // 限制数据点数量，避免图表过于拥挤
    const maxDataPoints = 100;
    if (iostatMetrics.devices[metric.device].timestamps.length >= maxDataPoints) {
      iostatMetrics.devices[metric.device].timestamps.shift();
      iostatMetrics.devices[metric.device].readIOPS.shift();
      iostatMetrics.devices[metric.device].writeIOPS.shift();
      iostatMetrics.devices[metric.device].totalIOPS.shift();
      iostatMetrics.devices[metric.device].readLatency.shift();
      iostatMetrics.devices[metric.device].writeLatency.shift();
      iostatMetrics.devices[metric.device].diskUtilization.shift();
      iostatMetrics.devices[metric.device].readThroughput.shift();
      iostatMetrics.devices[metric.device].writeThroughput.shift();
      iostatMetrics.devices[metric.device].totalThroughput.shift();
      iostatMetrics.devices[metric.device].queueLength.shift();
      iostatMetrics.devices[metric.device].serviceTime.shift();
    }

    iostatMetrics.devices[metric.device].timestamps.push(timestamp);
    iostatMetrics.devices[metric.device].readIOPS.push(metric.read_iops);
    iostatMetrics.devices[metric.device].writeIOPS.push(metric.write_iops);
    iostatMetrics.devices[metric.device].totalIOPS.push(
      metric.read_iops + metric.write_iops,
    );
    iostatMetrics.devices[metric.device].readLatency.push(metric.await_time);
    iostatMetrics.devices[metric.device].writeLatency.push(metric.await_time);
    iostatMetrics.devices[metric.device].diskUtilization.push(metric.util);
    iostatMetrics.devices[metric.device].readThroughput.push(metric.read_kbps);
    iostatMetrics.devices[metric.device].writeThroughput.push(metric.write_kbps);
    iostatMetrics.devices[metric.device].totalThroughput.push(
      metric.read_kbps + metric.write_kbps,
    );
    iostatMetrics.devices[metric.device].queueLength.push(
      metric.await_time / metric.svctm,
    );
    iostatMetrics.devices[metric.device].serviceTime.push(metric.svctm);
  } else {
    // 处理完整的指标数组
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
      deviceData[metric.device].totalIOPS.push(
        metric.read_iops + metric.write_iops,
      );
      deviceData[metric.device].readLatency.push(metric.await_time);
      deviceData[metric.device].writeLatency.push(metric.await_time);
      deviceData[metric.device].diskUtilization.push(metric.util);
      deviceData[metric.device].readThroughput.push(metric.read_kbps);
      deviceData[metric.device].writeThroughput.push(metric.write_kbps);
      deviceData[metric.device].totalThroughput.push(
        metric.read_kbps + metric.write_kbps,
      );
      deviceData[metric.device].queueLength.push(
        metric.await_time / metric.svctm,
      );
      deviceData[metric.device].serviceTime.push(metric.svctm);
    });

    // 更新iostatMetrics
    iostatMetrics.devices = deviceData;
  }

  // 更新可用设备列表
  availableDevices.value = Array.from(new Set([...availableDevices.value, ...devices]));
  if (availableDevices.value.length > 0 && !selectedDevice.value) {
    selectedDevice.value = availableDevices.value[0];
  }
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
  // 初始化WebSocket连接
  initWebSocket();
});

// 组件卸载时
onUnmounted(() => {
  // 销毁图表实例
  if (ioJitterChart) {
    ioJitterChart.dispose();
  }
  // 移除窗口大小变化监听
  window.removeEventListener("resize", handleResize);
  // 清理WebSocket连接
  if (socket.value) {
    socket.value.emit("leave_task_room", { task_id: taskId.value });
    socket.value.disconnect();
  }
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
  margin-top: 20px;
}

.performance-chart {
  width: 100%;
  height: 100%;
}

/* 抖动统计信息样式 */
.jitter-stats {
  margin: 20px 0;
}

.stats-card {
  margin-bottom: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

/* 指标抖动概览样式 */
.jitter-overview {
  margin: 20px 0;
}

.overview-card {
  margin-bottom: 20px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.overview-item {
  padding: 15px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  background-color: #fafafa;
}

.overview-metric {
  font-weight: bold;
  margin-bottom: 10px;
}

.overview-value {
  margin-bottom: 5px;
}

.overview-label {
  text-align: center;
  font-weight: bold;
}
</style>
