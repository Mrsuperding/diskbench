<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">仪表盘</h1>
      <p class="page-subtitle">系统概览和实时状态监控</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :xs="24" :sm="12" :lg="6" v-for="stat in stats" :key="stat.title">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <el-icon :size="24" color="white">
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-title">{{ stat.title }}</div>
              <div class="stat-trend" :class="stat.trend > 0 ? 'up' : 'down'">
                <el-icon :size="12">
                  <CaretTop v-if="stat.trend > 0" />
                  <CaretBottom v-else />
                </el-icon>
                {{ Math.abs(stat.trend) }}%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-section">
      <!-- 实时性能图表 -->
      <el-col :xs="24" :lg="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>实时性能监控</span>
              <el-button-group>
                <el-button
                  size="small"
                  :type="timeRange === '1h' ? 'primary' : ''"
                  @click="changeTimeRange('1h')"
                >
                  1小时
                </el-button>
                <el-button
                  size="small"
                  :type="timeRange === '6h' ? 'primary' : ''"
                  @click="changeTimeRange('6h')"
                >
                  6小时
                </el-button>
                <el-button
                  size="small"
                  :type="timeRange === '24h' ? 'primary' : ''"
                  @click="changeTimeRange('24h')"
                >
                  24小时
                </el-button>
              </el-button-group>
            </div>
          </template>
          <div class="chart-container">
            <v-chart
              :option="performanceChartOption"
              autoresize
              style="height: 300px"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 任务状态分布 -->
      <el-col :xs="24" :lg="8">
        <el-card class="chart-card">
          <template #header>
            <span>任务状态分布</span>
          </template>
          <div class="chart-container">
            <v-chart
              :option="taskStatusChartOption"
              autoresize
              style="height: 300px"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近任务和节点状态 -->
    <el-row :gutter="20" class="bottom-section">
      <!-- 最近任务 -->
      <el-col :xs="24" :lg="12">
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>最近任务</span>
              <el-button type="primary" text @click="$router.push('/tasks')">
                查看全部
              </el-button>
            </div>
          </template>
          <el-table :data="recentTasks" style="width: 100%" size="small">
            <el-table-column
              prop="name"
              label="任务名称"
              show-overflow-tooltip
            />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="progress" label="进度" width="80">
              <template #default="{ row }">
                <el-progress :percentage="row.progress" :stroke-width="4" />
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="140">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 节点状态 -->
      <el-col :xs="24" :lg="12">
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>节点状态</span>
              <el-button type="primary" text @click="$router.push('/nodes')">
                查看全部
              </el-button>
            </div>
          </template>
          <div class="node-status-list">
            <div v-for="node in nodeStatus" :key="node.id" class="node-item">
              <div class="node-info">
                <div class="node-name">{{ node.name }}</div>
                <div class="node-ip">{{ node.ip }}</div>
              </div>
              <div class="node-status">
                <el-tag :type="getNodeStatusType(node.status)" size="small">
                  {{ getNodeStatusText(node.status) }}
                </el-tag>
              </div>
              <div class="node-metrics">
                <div class="metric">
                  <span class="metric-label">CPU:</span>
                  <el-progress :percentage="node.cpu_usage" :stroke-width="3" />
                </div>
                <div class="metric">
                  <span class="metric-label">内存:</span>
                  <el-progress
                    :percentage="node.memory_usage"
                    :stroke-width="3"
                  />
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from "vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart, PieChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from "echarts/components";
import VChart from "vue-echarts";
import {
  Odometer,
  List,
  Monitor,
  User,
  CaretTop,
  CaretBottom,
} from "@element-plus/icons-vue";
import { formatTime } from "@/utils/format";
import dashboardApi from "../api/dashboard";
import nodesApi from "../api/nodes";

use([
  CanvasRenderer,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
]);

// 统计数据
const stats = ref([
  {
    title: "总任务数",
    value: "0",
    icon: "List",
    color: "#409eff",
    trend: 0,
  },
  {
    title: "运行中任务",
    value: "0",
    icon: "Monitor",
    color: "#67c23a",
    trend: 0,
  },
  {
    title: "在线节点",
    value: "0",
    icon: "Odometer",
    color: "#e6a23c",
    trend: 0,
  },
  {
    title: "注册用户",
    value: "0",
    icon: "User",
    color: "#f56c6c",
    trend: 0,
  },
]);

const timeRange = ref("1h");

// 性能图表配置
const performanceChartOption = reactive({
  title: {
    text: "IOPS 性能趋势",
    left: "center",
    textStyle: {
      fontSize: 14,
      fontWeight: "normal",
    },
  },
  tooltip: {
    trigger: "axis",
    axisPointer: {
      type: "cross",
    },
  },
  legend: {
    data: ["读IOPS", "写IOPS", "总IOPS"],
    bottom: 0,
  },
  grid: {
    left: "3%",
    right: "4%",
    bottom: "15%",
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
  series: [
    {
      name: "读IOPS",
      type: "line",
      smooth: true,
      data: [],
      itemStyle: { color: "#409eff" },
    },
    {
      name: "写IOPS",
      type: "line",
      smooth: true,
      data: [],
      itemStyle: { color: "#67c23a" },
    },
    {
      name: "总IOPS",
      type: "line",
      smooth: true,
      data: [],
      itemStyle: { color: "#e6a23c" },
    },
  ],
});

// 任务状态图表配置
const taskStatusChartOption = reactive({
  tooltip: {
    trigger: "item",
    formatter: "{a} <br/>{b}: {c} ({d}%)",
  },
  legend: {
    orient: "vertical",
    left: "left",
    data: ["运行中", "已完成", "失败", "已停止", "待执行"],
  },
  series: [
    {
      name: "任务状态",
      type: "pie",
      radius: ["40%", "70%"],
      center: ["60%", "50%"],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 4,
        borderColor: "#fff",
        borderWidth: 2,
      },
      label: {
        show: false,
        position: "center",
      },
      emphasis: {
        label: {
          show: true,
          fontSize: "18",
          fontWeight: "bold",
        },
      },
      labelLine: {
        show: false,
      },
      data: [
        { value: 8, name: "运行中", itemStyle: { color: "#409eff" } },
        { value: 45, name: "已完成", itemStyle: { color: "#67c23a" } },
        { value: 3, name: "失败", itemStyle: { color: "#f56c6c" } },
        { value: 2, name: "已停止", itemStyle: { color: "#909399" } },
        { value: 12, name: "待执行", itemStyle: { color: "#e6a23c" } },
      ],
    },
  ],
});

// 最近任务数据
const recentTasks = ref([]);

// 节点状态数据
const nodeStatus = ref([]);

// 方法
const changeTimeRange = (range) => {
  timeRange.value = range;
  // 更新图表数据
  updateChartData();
};

const updateChartData = () => {
  // 生成模拟数据
  const hours =
    timeRange.value === "1h" ? 1 : timeRange.value === "6h" ? 6 : 24;
  const points = hours * 6; // 每10分钟一个点
  const now = new Date();

  const xData = [];
  const readData = [];
  const writeData = [];
  const totalData = [];

  for (let i = points - 1; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 10 * 60 * 1000);
    xData.push(
      time.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
    );

    const read = Math.floor(Math.random() * 50000) + 30000;
    const write = Math.floor(Math.random() * 30000) + 10000;
    readData.push(read);
    writeData.push(write);
    totalData.push(read + write);
  }

  performanceChartOption.xAxis.data = xData;
  performanceChartOption.series[0].data = readData;
  performanceChartOption.series[1].data = writeData;
  performanceChartOption.series[2].data = totalData;
};

const getStatusType = (status) => {
  const types = {
    running: "primary",
    completed: "success",
    failed: "danger",
    stopped: "info",
    pending: "warning",
  };
  return types[status] || "info";
};

const getStatusText = (status) => {
  const texts = {
    running: "运行中",
    completed: "已完成",
    failed: "失败",
    stopped: "已停止",
    pending: "待执行",
  };
  return texts[status] || status;
};

const getNodeStatusType = (status) => {
  const types = {
    online: "success",
    offline: "danger",
    maintenance: "warning",
  };
  return types[status] || "info";
};

const getNodeStatusText = (status) => {
  const texts = {
    online: "在线",
    offline: "离线",
    maintenance: "维护中",
  };
  return texts[status] || status;
};

let refreshTimer = null;

// 加载仪表盘数据
const loadDashboardData = async () => {
  try {
    // 获取仪表盘统计数据
    const statsResponse = await dashboardApi.getStats();
    const dashboardStats = statsResponse.data;

    // 更新统计卡片数据
    stats.value[0].value = dashboardStats.tasks.total.toString();
    stats.value[1].value = dashboardStats.tasks.running.toString();
    stats.value[2].value = dashboardStats.nodes.online.toString();
    stats.value[3].value = dashboardStats.users.total.toString();

    // 获取最近任务
    const tasksResponse = await dashboardApi.getRecentTasks();
    recentTasks.value = tasksResponse.data.map((task) => ({
      ...task,
      progress:
        task.status === "completed" ? 100 : task.status === "running" ? 50 : 0,
    }));

    // 获取节点状态
    const nodeStatusResponse = await dashboardApi.getNodeStatus();
    // 获取节点列表
    const nodesResponse = await nodesApi.getNodes();
    nodeStatus.value = nodesResponse.data.map((node) => ({
      id: node.id,
      name: node.name,
      ip: node.ip_address,
      status: node.status,
      cpu_usage: Math.floor(Math.random() * 100), // 模拟CPU使用率
      memory_usage: Math.floor(Math.random() * 100), // 模拟内存使用率
    }));
  } catch (error) {
    console.error("加载仪表盘数据失败:", error);
  }
};

onMounted(() => {
  loadDashboardData();
  updateChartData();

  // 定时刷新数据
  refreshTimer = setInterval(() => {
    loadDashboardData();
    updateChartData();
  }, 30000); // 每30秒刷新一次
});

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
});
</script>

<style scoped>
.dashboard {
  min-height: calc(100vh - 120px);
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.stats-cards {
  margin-bottom: 24px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-trend {
  font-size: 12px;
  display: flex;
  align-items: center;
}

.stat-trend.up {
  color: #67c23a;
}

.stat-trend.down {
  color: #f56c6c;
}

.chart-section {
  margin-bottom: 24px;
}

.chart-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.bottom-section {
  margin-bottom: 24px;
}

.info-card {
  margin-bottom: 20px;
}

.node-status-list {
  max-height: 400px;
  overflow-y: auto;
}

.node-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.node-item:last-child {
  border-bottom: none;
}

.node-info {
  flex: 1;
  margin-right: 16px;
}

.node-name {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.node-ip {
  font-size: 12px;
  color: #909399;
}

.node-status {
  margin-right: 16px;
}

.node-metrics {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric {
  display: flex;
  align-items: center;
  gap: 8px;
}

.metric-label {
  font-size: 12px;
  color: #606266;
  width: 30px;
}

@media (max-width: 768px) {
  .page-title {
    font-size: 20px;
  }

  .stat-value {
    font-size: 20px;
  }

  .chart-container {
    height: 250px;
  }
}
</style>
