<template>
  <div class="node-monitoring-container">
    <!-- 顶部导航栏 -->
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/environment-spaces' }">
          环境空间
        </el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: `/environment-spaces/${spaceId}` }">
          {{ environmentSpace?.name || '加载中...' }}
        </el-breadcrumb-item>
        <el-breadcrumb-item>节点监控</el-breadcrumb-item>
      </el-breadcrumb>
      <div class="header-actions">
        <el-button @click="goBack">
          <el-icon><Back /></el-icon> 返回
        </el-button>
        <el-button type="success" @click="collectAllData" :loading="collecting">
          <el-icon><Collection /></el-icon> 采集数据
        </el-button>
        <el-button v-if="monitorType === 'partition'" type="warning" @click="collectPartitionData" :loading="collectingPartition">
          <el-icon><Collection /></el-icon> 采集分区数据
        </el-button>
        <el-button type="primary" @click="refreshData">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <!-- 查看模式切换 -->
    <el-card shadow="hover" class="view-mode-card">
      <div class="mode-controls">
        <el-radio-group v-model="viewMode" size="large" @change="handleViewModeChange">
          <el-radio-button label="table">
            <el-icon><List /></el-icon> 表格视图
          </el-radio-button>
          <el-radio-button label="chart">
            <el-icon><TrendCharts /></el-icon> 图表视图
          </el-radio-button>
        </el-radio-group>
        <el-radio-group v-model="monitorType" size="default" @change="handleMonitorTypeChange">
          <el-radio-button label="system">
            <el-icon><Monitor /></el-icon> 系统监控
          </el-radio-button>
          <el-radio-button label="partition">
            <el-icon><Folder /></el-icon> 分区监控
          </el-radio-button>
        </el-radio-group>
      </div>
    </el-card>

    <!-- 监控概览 -->
    <el-row :gutter="20" class="overview-row">
      <el-col :span="6">
        <el-card shadow="hover" class="overview-card">
          <div class="overview-content">
            <el-icon class="overview-icon" color="#409EFF"><Monitor /></el-icon>
            <div class="overview-text">
              <div class="overview-label">总节点数</div>
              <div class="overview-value">{{ nodes.length }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="overview-card">
          <div class="overview-content">
            <el-icon class="overview-icon" color="#67C23A"><CircleCheck /></el-icon>
            <div class="overview-text">
              <div class="overview-label">活跃节点</div>
              <div class="overview-value">{{ activeNodesCount }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="overview-card">
          <div class="overview-content">
            <el-icon class="overview-icon" color="#909399"><CircleClose /></el-icon>
            <div class="overview-text">
              <div class="overview-label">离线节点</div>
              <div class="overview-value">{{ inactiveNodesCount }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="overview-card">
          <div class="overview-content">
            <el-icon class="overview-icon" color="#F56C6C"><Warning /></el-icon>
            <div class="overview-text">
              <div class="overview-label">异常节点</div>
              <div class="overview-value">{{ errorNodesCount }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表视图 -->
    <div v-if="viewMode === 'chart'">
      <!-- 系统监控图表 -->
      <div v-if="monitorType === 'system'">
        <el-card shadow="hover" class="metric-selector-card">
          <template #header>
            <div class="card-header">
              <span>选择监控指标</span>
              <div class="header-controls">
                <el-select
                  v-model="timeRange"
                  size="small"
                  style="width: 120px; margin-right: 12px"
                  @change="loadHistoryMetrics"
                >
                  <el-option label="最近1小时" :value="1" />
                  <el-option label="最近6小时" :value="6" />
                  <el-option label="最近12小时" :value="12" />
                  <el-option label="最近24小时" :value="24" />
                </el-select>
                <el-radio-group
                  v-model="refreshInterval"
                  size="small"
                  @change="changeRefreshInterval"
                >
                  <el-radio-button :label="0">手动</el-radio-button>
                  <el-radio-button :label="10">10秒</el-radio-button>
                  <el-radio-button :label="30">30秒</el-radio-button>
                  <el-radio-button :label="60">1分钟</el-radio-button>
                  <el-radio-button :label="300">5分钟</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <el-checkbox-group v-model="selectedMetrics" @change="loadHistoryMetrics">
            <el-checkbox label="cpu_usage">CPU使用率</el-checkbox>
            <el-checkbox label="memory_usage">内存使用率</el-checkbox>
            <el-checkbox label="disk_usage">磁盘使用率</el-checkbox>
            <el-checkbox label="network_tx">网络上行</el-checkbox>
            <el-checkbox label="network_rx">网络下行</el-checkbox>
            <el-checkbox label="load_average">系统负载</el-checkbox>
          </el-checkbox-group>
        </el-card>

        <!-- 图表显示 -->
        <el-row :gutter="20" v-loading="loading">
          <el-col
            v-for="metric in selectedMetrics"
            :key="metric"
            :span="12"
            class="chart-col"
          >
            <el-card shadow="hover" class="chart-card">
              <template #header>
                <div class="card-header">
                  <span>{{ getMetricLabel(metric) }}</span>
                </div>
              </template>
              <v-chart
                :option="getChartOption(metric)"
                :style="{ height: '350px' }"
                autoresize
              />
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 分区监控图表 -->
      <div v-else>
        <el-card shadow="hover" class="metric-selector-card">
          <template #header>
            <div class="card-header">
              <span>选择分区监控指标</span>
              <div class="header-controls">
                <el-select
                  v-model="selectedPartition"
                  size="small"
                  style="width: 180px; margin-right: 12px"
                  placeholder="选择分区"
                  @change="loadPartitionHistoryMetrics"
                >
                  <el-option
                    v-for="partition in allPartitions"
                    :key="partition"
                    :label="partition"
                    :value="partition"
                  />
                </el-select>
                <el-select
                  v-model="timeRange"
                  size="small"
                  style="width: 120px; margin-right: 12px"
                  @change="loadPartitionHistoryMetrics"
                >
                  <el-option label="最近1小时" :value="1" />
                  <el-option label="最近6小时" :value="6" />
                  <el-option label="最近12小时" :value="12" />
                  <el-option label="最近24小时" :value="24" />
                </el-select>
                <el-radio-group
                  v-model="refreshInterval"
                  size="small"
                  @change="changeRefreshInterval"
                >
                  <el-radio-button :label="0">手动</el-radio-button>
                  <el-radio-button :label="10">10秒</el-radio-button>
                  <el-radio-button :label="30">30秒</el-radio-button>
                  <el-radio-button :label="60">1分钟</el-radio-button>
                  <el-radio-button :label="300">5分钟</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <el-checkbox-group v-model="selectedPartitionMetrics" @change="loadPartitionHistoryMetrics">
            <el-checkbox label="read_iops">读取IOPS</el-checkbox>
            <el-checkbox label="write_iops">写入IOPS</el-checkbox>
            <el-checkbox label="read_throughput">读取吞吐量</el-checkbox>
            <el-checkbox label="write_throughput">写入吞吐量</el-checkbox>
            <el-checkbox label="read_latency">读取延迟</el-checkbox>
            <el-checkbox label="write_latency">写入延迟</el-checkbox>
            <el-checkbox label="utilization">分区利用率</el-checkbox>
          </el-checkbox-group>
        </el-card>

        <!-- 分区图表显示 -->
        <el-row :gutter="20" v-loading="loading">
          <el-col
            v-for="metric in selectedPartitionMetrics"
            :key="metric"
            :span="12"
            class="chart-col"
          >
            <el-card shadow="hover" class="chart-card">
              <template #header>
                <div class="card-header">
                  <span>{{ getPartitionMetricLabel(metric) }}</span>
                </div>
              </template>
              <v-chart
                :option="getPartitionChartOption(metric)"
                :style="{ height: '350px' }"
                autoresize
              />
            </el-card>
          </el-col>
        </el-row>

        <!-- 无指标提示 -->
        <div v-if="selectedPartitionMetrics.length === 0" style="text-align: center; padding: 40px; color: #909399;">
          请选择至少一个分区监控指标以查看图表
        </div>
      </div>

      <!-- 如果没有选择指标，显示提示 -->
      <div v-if="selectedMetrics.length === 0" style="text-align: center; padding: 40px; color: #909399;">
        请选择至少一个监控指标以查看图表
      </div>
    </div>

    <!-- 表格视图 -->
    <el-card v-else shadow="hover" class="monitoring-card">
      <template #header>
        <div class="card-header">
          <span>{{ monitorType === 'system' ? '节点监控数据' : '节点分区监控数据' }}</span>
          <el-radio-group v-model="refreshInterval" size="small" @change="changeRefreshInterval">
            <el-radio-button :label="0">手动</el-radio-button>
            <el-radio-button :label="10">10秒</el-radio-button>
            <el-radio-button :label="30">30秒</el-radio-button>
            <el-radio-button :label="60">1分钟</el-radio-button>
            <el-radio-button :label="300">5分钟</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <!-- 系统监控表格 -->
      <el-table
        v-if="monitorType === 'system'"
        :data="nodesWithMetrics"
        style="width: 100%"
        border
        stripe
        v-loading="loading"
      >
        <el-table-column prop="name" label="节点名称" width="150" fixed="left" />
        <el-table-column prop="ip_address" label="IP地址" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="CPU使用率" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="row.metrics?.cpu_usage || 0"
              :color="getProgressColor(row.metrics?.cpu_usage || 0)"
            />
          </template>
        </el-table-column>
        <el-table-column label="内存使用率" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="row.metrics?.memory_usage || 0"
              :color="getProgressColor(row.metrics?.memory_usage || 0)"
            />
          </template>
        </el-table-column>
        <el-table-column label="磁盘使用率" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="row.metrics?.disk_usage || 0"
              :color="getProgressColor(row.metrics?.disk_usage || 0)"
            />
          </template>
        </el-table-column>
        <el-table-column label="网络(上行/下行)" width="180">
          <template #default="{ row }">
            <div v-if="row.metrics">
              <div>↑ {{ formatBytes(row.metrics.network_tx || 0) }}/s</div>
              <div>↓ {{ formatBytes(row.metrics.network_rx || 0) }}/s</div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="负载(1/5/15)" width="150">
          <template #default="{ row }">
            <span v-if="row.metrics?.load_average">
              {{ row.metrics.load_average.join(' / ') }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">
            {{ row.metrics?.updated_at || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewNodeDetail(row)">
              <el-icon><View /></el-icon> 详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分区监控表格 -->
      <div v-else>
        <el-table
          :data="nodesWithPartitionMetrics"
          style="width: 100%"
          border
          stripe
          v-loading="loading"
        >
          <el-table-column prop="node_name" label="节点名称" width="150" fixed="left" />
          <el-table-column label="分区" width="180">
            <template #default="{ row }">
              <el-tag size="small">{{ row.partition_name || '-' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="读取IOPS" width="120">
            <template #default="{ row }">
              {{ row.metrics && row.metrics.read_iops != null ? row.metrics.read_iops.toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="写入IOPS" width="120">
            <template #default="{ row }">
              {{ row.metrics && row.metrics.write_iops != null ? row.metrics.write_iops.toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="读取吞吐" width="130">
            <template #default="{ row }">
              {{ formatThroughput(row.metrics?.read_throughput || 0) }}
            </template>
          </el-table-column>
          <el-table-column label="写入吞吐" width="130">
            <template #default="{ row }">
              {{ formatThroughput(row.metrics?.write_throughput || 0) }}
            </template>
          </el-table-column>
          <el-table-column label="读取延迟" width="100">
            <template #default="{ row }">
              {{ row.metrics && row.metrics.read_latency != null ? row.metrics.read_latency.toFixed(3) + ' ms' : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="写入延迟" width="100">
            <template #default="{ row }">
              {{ row.metrics && row.metrics.write_latency != null ? row.metrics.write_latency.toFixed(3) + ' ms' : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="利用率" width="120">
            <template #default="{ row }">
              <el-progress
                v-if="row.metrics && row.metrics.utilization != null"
                :percentage="row.metrics.utilization"
                :color="getProgressColor(row.metrics.utilization)"
              />
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="更新时间" width="180">
            <template #default="{ row }">
              {{ row.updated_at || '-' }}
            </template>
          </el-table-column>
        </el-table>

        <!-- 无分区数据提示 -->
        <div v-if="nodesWithPartitionMetrics.length === 0" style="text-align: center; padding: 40px; color: #909399;">
          暂无分区监控数据，请先采集分区数据
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import {
  Back,
  Refresh,
  Monitor,
  CircleCheck,
  CircleClose,
  Warning,
  View,
  List,
  TrendCharts,
  Collection,
  Folder,
} from "@element-plus/icons-vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart, BarChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from "echarts/components";
import environmentSpacesApi from "@/api/environmentSpaces";
import nodesApi from "@/api/nodes";

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
]);

const router = useRouter();
const route = useRoute();

// 获取环境空间ID
const spaceId = computed(() => parseInt(route.params.id));

// 数据
const environmentSpace = ref(null);
const nodes = ref([]);
const nodesMetrics = ref({});
const historyMetrics = ref([]);
const loading = ref(false);
const collecting = ref(false);

// 分区监控数据
const collectingPartition = ref(false);
const partitionRealtimeData = ref([]);  // 分区实时数据列表
const partitionHistoryMetrics = ref([]);  // 分区历史指标数据
const allPartitions = ref([]);  // 所有分区列表

// 视图模式
const viewMode = ref("table"); // 'table' 或 'chart'

// 监控类型
const monitorType = ref("system"); // 'system' 或 'partition'

// 选中的指标
const selectedMetrics = ref(["cpu_usage", "memory_usage"]);
const selectedPartitionMetrics = ref(["read_iops", "write_iops"]);

// 选中的分区（图表用）
const selectedPartition = ref(null);

// 时间范围（小时）
const timeRange = ref(1);

// 刷新间隔
const refreshInterval = ref(0);
let refreshTimer = null;

// 计算属性：活跃节点数
const activeNodesCount = computed(() => {
  return nodes.value.filter((n) => n.status === "active").length;
});

// 计算属性：离线节点数
const inactiveNodesCount = computed(() => {
  return nodes.value.filter((n) => n.status === "inactive").length;
});

// 计算属性：异常节点数
const errorNodesCount = computed(() => {
  return nodes.value.filter((n) => n.status === "error").length;
});

// 计算属性：节点及其监控数据
const nodesWithMetrics = computed(() => {
  return nodes.value.map((node) => ({
    ...node,
    metrics: nodesMetrics.value[node.id],
  }));
});

// 计算属性：节点分区监控数据（表格用）
const nodesWithPartitionMetrics = computed(() => {
  const result = [];
  for (const nodeData of partitionRealtimeData.value) {
    if (nodeData && nodeData.partitions) {
      for (const [partitionName, metrics] of Object.entries(nodeData.partitions)) {
        result.push({
          node_id: nodeData.node_id,
          node_name: nodeData.node_name,
          partition_name: partitionName,
          metrics: metrics,
          updated_at: metrics.read_iops?.time || null,
        });
      }
    }
  }
  return result;
});

// 方法：加载分区实时指标
const loadPartitionRealtimeMetrics = async () => {
  loading.value = true;
  try {
    const response = await environmentSpacesApi.getPartitionRealtimeMetrics(spaceId.value);
    partitionRealtimeData.value = response.data || [];

    // 提取所有分区名称
    const partitionsSet = new Set();
    for (const nodeData of partitionRealtimeData.value) {
      if (nodeData && nodeData.partitions) {
        for (const partitionName of Object.keys(nodeData.partitions)) {
          partitionsSet.add(partitionName);
        }
      }
    }
    allPartitions.value = Array.from(partitionsSet);
    if (allPartitions.value.length > 0 && !selectedPartition.value) {
      selectedPartition.value = allPartitions.value[0];
    }
  } catch (error) {
    ElMessage.error("加载分区实时指标失败: " + error.message);
  } finally {
    loading.value = false;
  }
};

// 方法：加载分区历史指标
const loadPartitionHistoryMetrics = async () => {
  if (!selectedPartition.value) return;
  loading.value = true;
  try {
    const response = await environmentSpacesApi.getPartitionHistoryMetrics(spaceId.value, {
      hours: timeRange.value,
      partition: selectedPartition.value,
    });
    partitionHistoryMetrics.value = response.data || [];
  } catch (error) {
    ElMessage.error("加载分区历史指标失败: " + error.message);
  } finally {
    loading.value = false;
  }
};

// 方法：采集分区数据
const collectPartitionData = async () => {
  collectingPartition.value = true;
  try {
    const response = await environmentSpacesApi.collectPartitionMetrics(spaceId.value);
    ElMessage.success(response.message || "分区监控数据采集成功");
    await loadPartitionRealtimeMetrics();
  } catch (error) {
    ElMessage.error("采集分区监控数据失败: " + error.message);
  } finally {
    collectingPartition.value = false;
  }
};

// 方法：监控类型切换
const handleMonitorTypeChange = async () => {
  if (monitorType.value === "partition") {
    await loadPartitionRealtimeMetrics();
  }
};

// 方法：加载环境空间详情
const loadEnvironmentSpace = async () => {
  try {
    const response = await environmentSpacesApi.getEnvironmentSpace(
      spaceId.value
    );
    environmentSpace.value = response.data;
  } catch (error) {
    ElMessage.error("加载环境空间详情失败: " + error.message);
  }
};

// 方法：加载节点列表
const loadNodes = async () => {
  try {
    const response = await environmentSpacesApi.getEnvironmentSpaceNodes(
      spaceId.value
    );
    nodes.value = response.data;
  } catch (error) {
    ElMessage.error("加载节点列表失败: " + error.message);
  }
};

// 方法：加载节点监控数据
const loadNodesMetrics = async () => {
  loading.value = true;
  try {
    const metricsPromises = nodes.value.map(async (node) => {
      try {
        const response = await nodesApi.getNodeMetrics(node.id);
        return { nodeId: node.id, metrics: response.data };
      } catch (error) {
        console.error(`加载节点 ${node.id} 监控数据失败:`, error);
        return { nodeId: node.id, metrics: null };
      }
    });

    const results = await Promise.all(metricsPromises);
    const metricsMap = {};
    results.forEach(({ nodeId, metrics }) => {
      metricsMap[nodeId] = metrics;
    });
    nodesMetrics.value = metricsMap;
  } catch (error) {
    ElMessage.error("加载监控数据失败: " + error.message);
  } finally {
    loading.value = false;
  }
};

// 方法：加载历史监控数据
const loadHistoryMetrics = async () => {
  loading.value = true;
  try {
    const response = await environmentSpacesApi.getHistoryMetrics(
      spaceId.value,
      { hours: timeRange.value }
    );
    historyMetrics.value = response.data;
  } catch (error) {
    ElMessage.error("加载历史监控数据失败: " + error.message);
  } finally {
    loading.value = false;
  }
};

// 方法：刷新数据
const refreshData = async () => {
  await loadNodes();
  if (monitorType.value === "partition") {
    if (viewMode.value === "chart") {
      await loadPartitionHistoryMetrics();
    } else {
      await loadPartitionRealtimeMetrics();
    }
  } else {
    if (viewMode.value === "chart") {
      await loadHistoryMetrics();
    } else {
      await loadNodesMetrics();
    }
  }
};

// 方法：采集所有节点数据
const collectAllData = async () => {
  collecting.value = true;
  try {
    const response = await environmentSpacesApi.collectMetrics(spaceId.value);
    ElMessage.success(response.message || "监控数据采集成功");
    // 采集后立即刷新数据
    await refreshData();
  } catch (error) {
    ElMessage.error("采集监控数据失败: " + error.message);
  } finally {
    collecting.value = false;
  }
};

// 方法：改变刷新间隔
const changeRefreshInterval = (interval) => {
  // 清除旧的定时器
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }

  // 如果间隔不为0，设置新的定时器
  if (interval > 0) {
    refreshTimer = setInterval(() => {
      if (monitorType.value === "partition") {
        if (viewMode.value === "chart") {
          loadPartitionHistoryMetrics();
        } else {
          loadPartitionRealtimeMetrics();
        }
      } else {
        if (viewMode.value === "chart") {
          loadHistoryMetrics();
        } else {
          loadNodesMetrics();
        }
      }
    }, interval * 1000);
    ElMessage.success(`已设置自动刷新间隔为 ${interval} 秒`);
  }
};

// 方法：获取状态类型
const getStatusType = (status) => {
  const statusMap = {
    active: "success",
    inactive: "info",
    error: "danger",
  };
  return statusMap[status] || "info";
};

// 方法：获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    active: "活跃",
    inactive: "离线",
    error: "错误",
  };
  return statusMap[status] || status;
};

// 方法：获取进度条颜色
const getProgressColor = (percentage) => {
  if (percentage >= 90) return "#F56C6C";
  if (percentage >= 70) return "#E6A23C";
  return "#67C23A";
};

// 方法：格式化字节
const formatBytes = (bytes) => {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return (bytes / Math.pow(k, i)).toFixed(2) + " " + sizes[i];
};

// 方法：格式化吞吐量（直接是速度值，不需要/s后缀）
const formatThroughput = (bytes) => {
  if (bytes === 0) return "0 B/s";
  const k = 1024;
  const sizes = ["B/s", "KB/s", "MB/s", "GB/s", "TB/s"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return (bytes / Math.pow(k, i)).toFixed(2) + " " + sizes[i];
};

// 方法：查看节点详情
const viewNodeDetail = (node) => {
  // 这里可以弹出一个对话框显示更详细的节点信息
  // 或者跳转到节点详情页
  ElMessage.info(`查看节点 ${node.name} 的详情功能待实现`);
};

// 方法：获取指标标签
const getMetricLabel = (metric) => {
  const labels = {
    cpu_usage: "CPU使用率",
    memory_usage: "内存使用率",
    disk_usage: "磁盘使用率",
    network_tx: "网络上行速率",
    network_rx: "网络下行速率",
    load_average: "系统负载",
  };
  return labels[metric] || metric;
};

// 方法：获取图表配置
const getChartOption = (metric) => {
  // 准备时间序列数据
  const timeSeriesData = {};
  const allTimestamps = new Set();

  // 遍历历史数据，按节点和时间组织
  historyMetrics.value.forEach((nodeData) => {
    const nodeId = nodeData.node_id;
    const nodeName = nodeData.node_name;

    if (!timeSeriesData[nodeId]) {
      timeSeriesData[nodeId] = {
        name: nodeName,
        data: {},
      };
    }

    // 根据指标类型获取数据
    let metricData = nodeData.metrics[metric];

    if (metricData && Array.isArray(metricData)) {
      metricData.forEach((point) => {
        const time = point.time;
        let value = point.value;

        // 处理 load_average 数据
        if (metric === "load_average" && typeof value === "string") {
          try {
            const loadArray = JSON.parse(value);
            value = loadArray[0]; // 使用1分钟负载
          } catch (e) {
            value = 0;
          }
        }

        // 网络速率转换为 MB/s
        if (metric === "network_tx" || metric === "network_rx") {
          value = (value / 1024 / 1024).toFixed(2);
        }

        allTimestamps.add(time);
        timeSeriesData[nodeId].data[time] = value;
      });
    }
  });

  // 转换为 ECharts 所需格式
  const sortedTimestamps = Array.from(allTimestamps).sort();
  const series = [];

  Object.entries(timeSeriesData).forEach(([nodeId, nodeInfo]) => {
    const data = sortedTimestamps.map((time) => {
      const value = nodeInfo.data[time];
      return value !== undefined ? Number(value) : null;
    });

    series.push({
      name: nodeInfo.name,
      type: "line",
      smooth: true,
      data: data,
      connectNulls: true,
      symbol: "circle",
      symbolSize: 4,
    });
  });

  // 格式化时间轴
  const xAxisData = sortedTimestamps.map((time) => {
    const date = new Date(time);
    const month = (date.getMonth() + 1).toString().padStart(2, "0");
    const day = date.getDate().toString().padStart(2, "0");
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
    return `${month}-${day} ${hours}:${minutes}`;
  });

  // 确定 Y 轴格式
  let yAxisFormatter = "{value}";
  let tooltipFormatter = (params) => {
    if (!params || params.length === 0) return "";
    let result = params[0].axisValue + "<br/>";
    params.forEach((param) => {
      if (param.value !== null && param.value !== undefined) {
        result += `${param.marker} ${param.seriesName}: ${param.value}`;
        if (metric.includes("usage")) {
          result += "%";
        } else if (metric === "network_tx" || metric === "network_rx") {
          result += " MB/s";
        }
        result += "<br/>";
      }
    });
    return result;
  };

  if (metric.includes("usage")) {
    yAxisFormatter = "{value}%";
  } else if (metric === "network_tx" || metric === "network_rx") {
    yAxisFormatter = "{value} MB/s";
  }

  return {
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross",
        label: {
          backgroundColor: "#6a7985",
        },
      },
      formatter: tooltipFormatter,
    },
    legend: {
      data: series.map((s) => s.name),
      bottom: 0,
      type: "scroll",
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "12%",
      top: "5%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: xAxisData,
      axisLabel: {
        rotate: 45,
        interval: Math.floor(xAxisData.length / 10) || 0,
      },
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: yAxisFormatter,
      },
    },
    series: series,
  };
};

// 方法：获取分区指标标签
const getPartitionMetricLabel = (metric) => {
  const labels = {
    read_iops: "读取IOPS",
    write_iops: "写入IOPS",
    read_throughput: "读取吞吐量",
    write_throughput: "写入吞吐量",
    read_latency: "读取延迟",
    write_latency: "写入延迟",
    utilization: "分区利用率",
  };
  return labels[metric] || metric;
};

// 方法：获取分区图表配置
const getPartitionChartOption = (metric) => {
  // 准备时间序列数据
  const timeSeriesData = {};
  const allTimestamps = new Set();

  // 遍历历史数据，按节点和分区组织
  partitionHistoryMetrics.value.forEach((nodeData) => {
    const nodeId = nodeData.node_id;
    const nodeName = nodeData.node_name;

    if (!timeSeriesData[nodeId]) {
      timeSeriesData[nodeId] = {
        name: nodeName,
        data: {},
      };
    }

    // 根据指标类型获取数据
    const partitions = nodeData.partitions || {};
    for (const [partitionName, metricsData] of Object.entries(partitions)) {
      const metricData = metricsData[metric];
      if (metricData && Array.isArray(metricData)) {
        metricData.forEach((point) => {
          const time = point.time;
          let value = point.value;

          // 格式化键
          const key = `${nodeName}-${partitionName}`;
          if (!timeSeriesData[key]) {
            timeSeriesData[key] = {
              name: `${nodeName} (${partitionName})`,
              data: {},
            };
          }

          allTimestamps.add(time);
          timeSeriesData[key].data[time] = value;
        });
      }
    }
  });

  // 转换为 ECharts 所需格式
  const sortedTimestamps = Array.from(allTimestamps).sort();
  const series = [];

  Object.entries(timeSeriesData).forEach(([key, nodeInfo]) => {
    const data = sortedTimestamps.map((time) => {
      const value = nodeInfo.data[time];
      return value !== undefined ? Number(value) : null;
    });

    series.push({
      name: nodeInfo.name,
      type: "line",
      smooth: true,
      data: data,
      connectNulls: true,
      symbol: "circle",
      symbolSize: 4,
    });
  });

  // 格式化时间轴
  const xAxisData = sortedTimestamps.map((time) => {
    const date = new Date(time);
    const month = (date.getMonth() + 1).toString().padStart(2, "0");
    const day = date.getDate().toString().padStart(2, "0");
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
    const seconds = date.getSeconds().toString().padStart(2, "0");
    return `${month}-${day} ${hours}:${minutes}:${seconds}`;
  });

  // 确定 Y 轴格式和提示框格式
  let yAxisFormatter = "{value}";
  if (metric.includes("throughput")) {
    yAxisFormatter = "{value} MB/s";
  } else if (metric.includes("latency")) {
    yAxisFormatter = "{value} ms";
  } else if (metric.includes("iops")) {
    yAxisFormatter = "{value}";
  } else if (metric.includes("utilization")) {
    yAxisFormatter = "{value}%";
  }

  return {
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross",
        label: {
          backgroundColor: "#6a7985",
        },
      },
      formatter: (params) => {
        if (!params || params.length === 0) return "";
        let result = params[0].axisValue + "<br/>";
        params.forEach((param) => {
          if (param.value !== null && param.value !== undefined) {
            result += `${param.marker} ${param.seriesName}: ${param.value}`;
            if (metric.includes("throughput")) {
              result += " MB/s";
            } else if (metric.includes("latency")) {
              result += " ms";
            } else if (metric.includes("utilization")) {
              result += "%";
            }
            result += "<br/>";
          }
        });
        return result;
      },
    },
    legend: {
      data: series.map((s) => s.name),
      bottom: 0,
      type: "scroll",
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "12%",
      top: "5%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: xAxisData,
      axisLabel: {
        rotate: 45,
        interval: Math.floor(xAxisData.length / 10) || 0,
      },
    },
    yAxis: {
      type: "value",
      axisLabel: {
        formatter: yAxisFormatter,
      },
    },
    series: series,
  };
};

// 方法：返回
const goBack = () => {
  router.back();
};

// 监听视图模式变化
const handleViewModeChange = async () => {
  if (viewMode.value === "chart") {
    if (monitorType.value === "partition") {
      await loadPartitionHistoryMetrics();
    } else {
      await loadHistoryMetrics();
    }
  } else {
    if (monitorType.value === "partition") {
      await loadPartitionRealtimeMetrics();
    } else {
      await loadNodesMetrics();
    }
  }
};

// 初始化加载
onMounted(async () => {
  await loadEnvironmentSpace();
  await loadNodes();
  await loadNodesMetrics();
});

// 组件卸载时清除定时器
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
});
</script>

<style scoped>
.node-monitoring-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.overview-row {
  margin-bottom: 24px;
}

.overview-card {
  height: 100%;
}

.overview-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.overview-icon {
  font-size: 48px;
}

.overview-text {
  flex: 1;
}

.overview-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.overview-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.view-mode-card {
  margin-bottom: 24px;
}

.mode-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-selector-card {
  margin-bottom: 24px;
}

.metric-selector-card .el-checkbox {
  margin-right: 20px;
  margin-bottom: 12px;
}

.chart-col {
  margin-bottom: 24px;
}

.chart-card {
  height: 100%;
}

.monitoring-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  align-items: center;
}
</style>
