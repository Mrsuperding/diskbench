<template>
  <div class="log-visualization-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>测试日志可视化</span>
        </div>
      </template>

      <div class="chart-controls">
        <el-select
          v-model="selectedNode"
          placeholder="选择节点"
          style="width: 200px; margin-right: 10px"
          @change="loadTestLogs"
        >
          <el-option
            v-for="node in nodes"
            :key="node.id"
            :label="node.name"
            :value="node.id"
          ></el-option>
        </el-select>

        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          style="width: 400px; margin-right: 10px"
          @change="loadTestLogs"
        ></el-date-picker>

        <el-button type="primary" size="small" @click="loadTestLogs">
          <el-icon><RefreshRight /></el-icon>
          刷新数据
        </el-button>
      </div>

      <div class="charts-container">
        <!-- 测试日志列表 -->
        <el-card shadow="hover" style="margin-bottom: 20px">
          <template #header>
            <div class="card-header">
              <span>测试日志记录</span>
            </div>
          </template>

          <el-table v-loading="loading" :data="testLogs" style="width: 100%">
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column prop="node.name" label="节点" width="150" />
            <el-table-column prop="log_type" label="日志类型" width="120" />
            <el-table-column
              prop="log_content"
              label="日志内容"
              show-overflow-tooltip
            />
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="scope">
                <el-button
                  type="primary"
                  size="small"
                  @click="viewIOStatMetrics(scope.row)"
                  :disabled="scope.row.log_type !== 'iostat'"
                >
                  查看IOSTAT
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-if="testLogs.length > 0"
            class="pagination"
            layout="total, sizes, prev, pager, next, jumper"
            :total="totalLogs"
            :page-size="pageSize"
            :current-page="currentPage"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </el-card>

        <!-- IOSTAT指标图表 -->
        <el-card v-if="showIOStatChart" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>IOSTAT性能指标</span>
              <el-button type="info" size="small" @click="hideIOStatChart"
                >关闭</el-button
              >
            </div>
          </template>

          <div class="chart-controls">
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
              v-model="selectedMetrics"
              placeholder="选择性能指标"
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
            <v-chart
              ref="iostatChartRef"
              :options="chartOptions"
              :autoresize="true"
            />
          </div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from "vue";
import { useRouter, useRoute } from "vue-router";
import { VChart } from "vue-echarts";
import * as echarts from "echarts";
import { RefreshRight } from "@element-plus/icons-vue";
import taskApi from "@/api/tasks";
import nodeApi from "@/api/nodes";

// 路由相关
const router = useRouter();
const route = useRoute();
const taskId = ref(route.params.id || 0);

// 图表相关
const iostatChartRef = ref(null);
const chartOptions = ref({
  title: {
    text: "IOSTAT性能指标",
    left: "center",
  },
  tooltip: {
    trigger: "axis",
    axisPointer: {
      type: "cross",
    },
  },
  legend: {
    data: [],
    top: 30,
  },
  grid: {
    left: "3%",
    right: "4%",
    bottom: "3%",
    containLabel: true,
  },
  toolbox: {
    feature: {
      saveAsImage: {},
    },
  },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: [],
  },
  yAxis: {
    type: "value",
  },
  series: [],
});

// 选择控件
const selectedNode = ref("");
const dateRange = ref([]);
const selectedDevice = ref("");
const selectedMetrics = ref(["read_iops", "write_iops"]);
const showIOStatChart = ref(false);
const currentLog = ref(null);

// 数据相关
const loading = ref(false);
const nodes = ref([]);
const testLogs = ref([]);
const totalLogs = ref(0);
const pageSize = ref(10);
const currentPage = ref(1);
const availableDevices = ref([]);
const iostatMetrics = reactive({
  timestamps: [],
  devices: {},
});

// 加载节点列表
const loadNodes = async () => {
  try {
    const response = await nodeApi.getNodes();
    if (response && response.data) {
      nodes.value = response.data;
      if (nodes.value.length > 0) {
        selectedNode.value = nodes.value[0].id;
        loadTestLogs();
      }
    }
  } catch (error) {
    console.error("加载节点列表失败:", error);
  }
};

// 加载测试日志
const loadTestLogs = async () => {
  if (!selectedNode.value) return;

  loading.value = true;

  try {
    const params = {
      node_id: selectedNode.value,
      page: currentPage.value,
      page_size: pageSize.value,
    };

    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dateRange.value[0];
      params.end_time = dateRange.value[1];
    }

    // 这里假设API路径为 /logs/test-logs
    const response = await taskApi.getTaskLogs(taskId.value, params);

    if (response && response.data) {
      if (response.data.items) {
        testLogs.value = response.data.items;
        totalLogs.value = response.data.total;
      } else {
        testLogs.value = response.data;
        totalLogs.value = response.data.length;
      }
    }
  } catch (error) {
    console.error("加载测试日志失败:", error);
  } finally {
    loading.value = false;
  }
};

// 查看IOSTAT指标
const viewIOStatMetrics = async (log) => {
  if (!log || log.log_type !== "iostat") return;

  currentLog.value = log;
  showIOStatChart.value = true;

  try {
    const response = await taskApi.getIOStatMetrics(log.id);
    if (response && response.data) {
      processIOStatMetrics(response.data);
      updateIOStatChart();
    }
  } catch (error) {
    console.error("加载IOSTAT指标失败:", error);
  }
};

// 隐藏IOSTAT图表
const hideIOStatChart = () => {
  showIOStatChart.value = false;
  currentLog.value = null;
};

// 处理IOSTAT指标数据
const processIOStatMetrics = (metrics) => {
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
  if (availableDevices.value.length > 0 && !selectedDevice.value) {
    selectedDevice.value = availableDevices.value[0];
  }

  // 更新iostatMetrics
  iostatMetrics.devices = deviceData;
  if (selectedDevice.value && deviceData[selectedDevice.value]) {
    iostatMetrics.timestamps = deviceData[selectedDevice.value].timestamps;
  }
};

// 更新IOSTAT图表
const updateIOStatChart = () => {
  if (!selectedDevice.value || !iostatMetrics.devices[selectedDevice.value])
    return;

  const deviceData = iostatMetrics.devices[selectedDevice.value];

  // 更新图表选项
  chartOptions.value.xAxis.data = deviceData.timestamps;

  // 定义指标配置
  const metricConfig = {
    read_iops: { name: "读IOPS", color: "#5470c6" },
    write_iops: { name: "写IOPS", color: "#91cc75" },
    read_kbps: { name: "读吞吐量", color: "#fac858" },
    write_kbps: { name: "写吞吐量", color: "#ee6666" },
    await_time: { name: "IO等待时间", color: "#73c0de" },
    svctm: { name: "服务时间", color: "#3ba272" },
    util: { name: "磁盘使用率", color: "#fc8452" },
  };

  // 更新系列数据
  chartOptions.value.series = selectedMetrics.value.map((metric) => {
    return {
      name: metricConfig[metric].name,
      type: "line",
      stack: "总量",
      areaStyle: {},
      emphasis: {
        focus: "series",
      },
      data: deviceData[metric],
    };
  });

  // 更新图例
  chartOptions.value.legend.data = selectedMetrics.value.map(
    (metric) => metricConfig[metric].name,
  );
};

// 分页处理
const handleSizeChange = (size) => {
  pageSize.value = size;
  loadTestLogs();
};

const handleCurrentChange = (current) => {
  currentPage.value = current;
  loadTestLogs();
};

// 组件挂载时加载数据
onMounted(() => {
  loadNodes();
});
</script>

<style scoped>
.log-visualization-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-controls {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.charts-container {
  display: flex;
  flex-direction: column;
}

.chart-container {
  height: 400px;
  margin-top: 20px;
}

.pagination {
  margin-top: 15px;
  text-align: right;
}
</style>
