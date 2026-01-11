<template>
  <div class="results-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>测试结果详细信息</span>
          <el-upload
            class="upload-demo"
            action="#"
            :on-change="handleFileUpload"
            :auto-upload="false"
            accept=".zip,.log,.txt"
            :show-file-list="false"
          >
            <el-button type="primary" size="small">上传本地日志</el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持上传 .zip、.log、.txt 格式的日志文件
              </div>
            </template>
          </el-upload>
        </div>
      </template>

      <div class="result-tabs">
        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <!-- 测试概览 -->
          <el-tab-pane label="测试概览" name="overview">
            <div class="overview-section">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="任务名称">{{
                  taskInfo.name
                }}</el-descriptions-item>
                <el-descriptions-item label="任务ID">{{
                  taskInfo.id
                }}</el-descriptions-item>
                <el-descriptions-item label="创建时间">{{
                  formatDate(taskInfo.created_at)
                }}</el-descriptions-item>
                <el-descriptions-item label="完成时间">{{
                  formatDate(taskInfo.completed_at)
                }}</el-descriptions-item>
                <el-descriptions-item label="状态">{{
                  getStatusLabel(taskInfo.status)
                }}</el-descriptions-item>
                <el-descriptions-item label="总耗时">{{
                  taskInfo.total_duration || "-"
                }}</el-descriptions-item>
                <el-descriptions-item label="节点数量">{{
                  taskInfo.node_count || 0
                }}</el-descriptions-item>
                <el-descriptions-item label="测试用例">{{
                  taskInfo.test_case_count || 0
                }}</el-descriptions-item>
              </el-descriptions>
            </div>
          </el-tab-pane>

          <!-- 日志列表 -->
          <el-tab-pane label="日志列表" name="logs">
            <div class="logs-section">
              <el-select
                v-model="selectedNode"
                placeholder="选择节点"
                style="width: 200px; margin-bottom: 20px"
                @change="loadTaskLogs"
              >
                <el-option
                  v-for="node in taskNodes"
                  :key="node.id"
                  :label="node.name"
                  :value="node.id"
                ></el-option>
              </el-select>

              <el-table :data="taskLogs" stripe border>
                <el-table-column
                  prop="id"
                  label="日志ID"
                  width="80"
                ></el-table-column>
                <el-table-column prop="log_type" label="日志类型" width="120">
                  <template #default="scope">
                    <el-tag
                      :type="
                        scope.row.log_type === 'iostat' ? 'success' : 'primary'
                      "
                    >
                      {{ scope.row.log_type === "iostat" ? "IOSTAT" : "FIO" }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column
                  prop="node_id"
                  label="节点ID"
                  width="100"
                ></el-table-column>
                <el-table-column
                  prop="log_filename"
                  label="文件名"
                  width="300"
                ></el-table-column>
                <el-table-column
                  prop="collection_time"
                  label="收集时间"
                  width="180"
                >
                  <template #default="scope">
                    {{ formatDate(scope.row.collection_time) }}
                  </template>
                </el-table-column>
                <el-table-column prop="file_size" label="文件大小" width="120">
                  <template #default="scope">
                    {{ formatFileSize(scope.row.file_size) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="200" fixed="right">
                  <template #default="scope">
                    <el-button
                      type="primary"
                      size="small"
                      @click="viewLogDetails(scope.row.id)"
                    >
                      查看详情
                    </el-button>
                    <el-button
                      type="success"
                      size="small"
                      @click="downloadLog(scope.row.id)"
                      style="margin-left: 10px"
                    >
                      下载
                    </el-button>
                    <el-button
                      v-if="scope.row.log_type === 'iostat'"
                      type="warning"
                      size="small"
                      @click="viewJitterChart(scope.row.id)"
                      style="margin-left: 10px"
                    >
                      抖动分析
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>

          <!-- 详细数据表格 -->
          <el-tab-pane label="详细数据" name="data-table">
            <div class="data-table-section">
              <div class="data-controls">
                <el-select
                v-model="selectedNodes"
                placeholder="选择节点"
                multiple
                style="width: 200px; margin-right: 20px"
                @change="loadFioMetricsFromLogs"
              >
                <el-option
                  v-for="node in taskNodes"
                  :key="node.id"
                  :label="node.name"
                  :value="node.id"
                ></el-option>
              </el-select>

              <el-select
                v-model="selectedDevices"
                placeholder="选择分区"
                multiple
                style="width: 200px; margin-right: 20px"
                @change="loadFioMetricsFromLogs"
              >
                <el-option
                  v-for="device in availableDevices"
                  :key="device"
                  :label="device"
                  :value="device"
                ></el-option>
              </el-select>

                <el-button type="primary" size="small" @click="loadFioMetricsFromLogs">
                  刷新数据
                </el-button>
                <el-button type="primary" size="small" @click="exportData" style="margin-left: 10px">
                  导出数据
                </el-button>
              </div>

              <el-table
                :data="displayedData"
                stripe
                border
                height="500"
                v-loading="loading"
                element-loading-text="加载中..."
              >
                <el-table-column
                  prop="io_model_name"
                  label="IO模型名称"
                  width="200"
                ></el-table-column>
                <el-table-column
                  prop="io_start_time"
                  label="IO模型开始时间"
                  width="180"
                ></el-table-column>
                <el-table-column
                  prop="io_end_time"
                  label="IO模型结束时间"
                  width="180"
                ></el-table-column>
                <el-table-column
                  prop="device"
                  label="分区"
                  width="100"
                ></el-table-column>
                <el-table-column
                  prop="total_iops"
                  label="总IOPS"
                  width="120"
                ></el-table-column>
                <el-table-column
                  prop="total_kbps"
                  label="总吞吐量(KB/s)"
                  width="160"
                ></el-table-column>
                <el-table-column
                  prop="await_time"
                  label="平均时延(ms)"
                  width="140"
                ></el-table-column>
                <el-table-column
                  prop="read_iops"
                  label="读IOPS"
                  width="120"
                ></el-table-column>
                <el-table-column
                  prop="write_iops"
                  label="写IOPS"
                  width="120"
                ></el-table-column>
                <el-table-column
                  prop="read_kbps"
                  label="读吞吐量(KB/s)"
                  width="160"
                ></el-table-column>
                <el-table-column
                  prop="write_kbps"
                  label="写吞吐量(KB/s)"
                  width="160"
                ></el-table-column>
                <el-table-column
                  prop="lat_p99"
                  label="p99时延(ms)"
                  width="140"
                ></el-table-column>
                <el-table-column
                  prop="lat_max"
                  label="最大时延(ms)"
                  width="140"
                ></el-table-column>
              </el-table>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getTaskLogs, getIOStatMetrics, getRealtimeMetrics, downloadLog, getFioMetricsFromLogs } from "@/api/logs";
import tasksApi from "@/api/tasks";
import localDataManager from "@/utils/localDataManager";

// 路由相关
const router = useRouter();
const route = useRoute();
const taskId = ref(route.params.id || route.query.taskId || "1");

// 页面状态
const activeTab = ref("overview");
const loading = ref(false);
const taskInfo = reactive({
  id: "",
  name: "",
  created_at: "",
  completed_at: "",
  status: "",
  total_duration: "",
  node_count: 0,
  test_case_count: 0,
});

// 任务节点
const taskNodes = ref([]);

// 日志数据
const taskLogs = ref([]);
const availableLogs = ref([]);
const selectedLog = ref("");
const selectedNode = ref("");

// 数据表格
const availableDevices = ref([]);
const selectedNodes = ref([]);
const selectedDevices = ref([]);
const rawIOStatData = ref([]);
const displayedData = ref([]);

// 加载任务信息
const loadTaskInfo = async () => {
  loading.value = true;
  try {
    // 直接从API获取最新数据，确保数据准确性
    const response = await tasksApi.getTask(taskId.value);
    if (response && response.data) {
      Object.assign(taskInfo, response.data);
      if (response.data.nodes) {
        taskNodes.value = response.data.nodes;
        taskInfo.node_count = response.data.nodes.length;
        if (taskNodes.value.length > 0) {
          // 设置默认选中所有节点
          selectedNodes.value = taskNodes.value.map(node => node.id);
          selectedNode.value = taskNodes.value[0].id;
          loadTaskLogs();
          // 加载可用设备
          await loadAvailableDevices();
        }
      }
      // 保存到本地
      localDataManager.saveTaskData(taskId.value, response.data);
    }
  } catch (error) {
    console.error("加载任务信息失败:", error);
    // 尝试从本地获取数据
    const localData = localDataManager.getTaskData(taskId.value);
    if (localData) {
      Object.assign(taskInfo, localData);
      if (localData.nodes) {
        taskNodes.value = localData.nodes;
        taskInfo.node_count = localData.nodes.length;
        if (taskNodes.value.length > 0) {
          // 设置默认选中所有节点
          selectedNodes.value = taskNodes.value.map(node => node.id);
          selectedNode.value = taskNodes.value[0].id;
          loadTaskLogs();
          // 加载可用设备
          await loadAvailableDevices();
        }
      }
    }
  } finally {
    loading.value = false;
  }
};

// 加载可用设备
const loadAvailableDevices = async () => {
  try {
    // 从任务信息中获取节点的分区信息
    if (taskInfo && taskInfo.nodes) {
      const devices = new Set();
      // 从节点列表中获取所有分区
      taskInfo.nodes.forEach(node => {
        // 首先检查是否有io_partitions字段（实际存储分区信息的地方）
        if (node.io_partitions && Array.isArray(node.io_partitions)) {
          node.io_partitions.forEach(partition => {
            if (typeof partition === 'string') {
              // 如果是字符串形式，直接添加
              devices.add(partition);
            } else if (partition && partition.path) {
              // 如果是对象形式，从path中提取设备名
              const deviceName = partition.path.split('/').pop();
              devices.add(deviceName);
            } else if (partition && partition.device_name) {
              // 如果有明确的device_name字段
              devices.add(partition.device_name);
            }
          });
        } else if (node.node_info && node.node_info.partitions) {
          // 备用方案：从node_info.partitions中获取
          node.node_info.partitions.forEach(partition => {
            if (partition.device_name) {
              devices.add(partition.device_name);
            }
          });
        }
      });
      
      if (devices.size > 0) {
        availableDevices.value = Array.from(devices);
        selectedDevices.value = Array.from(devices);
        // 加载FIO日志数据
        loadFioMetricsFromLogs();
      } else {
        // 如果节点信息中没有分区，从日志中提取
        const response = await getTaskLogs(taskId.value);
        if (response && response.data) {
          // 从所有日志中提取唯一设备列表
          const logDevices = new Set();
          response.data.forEach(log => {
            if (log.log_type === 'fio' && log.log_filename) {
              // 当前日志文件名格式：任务名_fio_时间戳.log
              // 由于没有明确的设备信息，我们使用默认设备
              // 可以根据需要修改为从节点信息或其他地方获取设备信息
              logDevices.add('sda'); // 使用默认设备名
            }
          });
          availableDevices.value = Array.from(logDevices);
          selectedDevices.value = Array.from(logDevices);
          // 加载FIO日志数据
          loadFioMetricsFromLogs();
        }
      }
    }
  } catch (error) {
    console.error("加载可用设备失败:", error);
    // 失败时使用空列表，避免硬编码
    availableDevices.value = [];
    selectedDevices.value = [];
    // 加载FIO日志数据
    loadFioMetricsFromLogs();
  }
};

// 从FIO日志文件获取数据
const loadFioMetricsFromLogs = async () => {
  loading.value = true;
  try {
    // 将数组参数转换为逗号分隔的字符串格式
    const params = {
      node_ids: selectedNodes.value.join(','),
      devices: selectedDevices.value.join(',')
    };
    
    // 调用API从FIO日志文件获取数据
    const response = await getFioMetricsFromLogs(taskId.value, params);
    
    if (response && response.data) {
      rawIOStatData.value = response.data;
      updateDataTable();
    } else {
      // 确保数据为空时也能正确更新表格
      rawIOStatData.value = [];
      updateDataTable();
    }
  } catch (error) {
    console.error("加载FIO日志数据失败:", error);
    // 失败时使用空数据，避免显示错误数据
    rawIOStatData.value = [];
    updateDataTable();
  } finally {
    loading.value = false;
  }
};

// 生成模拟数据（用于测试）
const generateMockData = () => {
  const mockData = [];
  const timestamp = new Date();
  
  // 为每个选中的节点和设备生成模拟数据
  selectedNodes.value.forEach(nodeId => {
    selectedDevices.value.forEach(device => {
      for (let i = 0; i < 10; i++) {
        const data = {
          node_id: nodeId,
          device: device,
          timestamp: new Date(timestamp.getTime() - i * 60000).toISOString(),
          read_iops: (Math.random() * 1000).toFixed(2),
          write_iops: (Math.random() * 1000).toFixed(2),
          read_kbps: (Math.random() * 10000).toFixed(2),
          write_kbps: (Math.random() * 10000).toFixed(2),
          await_time: (Math.random() * 10).toFixed(2),
          svctm: (Math.random() * 5).toFixed(2),
          util: (Math.random() * 100).toFixed(2)
        };
        mockData.push(data);
      }
    });
  });
  
  return mockData;
};

// 加载任务日志
const loadTaskLogs = async () => {
  loading.value = true;
  try {
    // 优先从本地获取数据
    const localData = localDataManager.getTaskData(taskId.value);

    if (localData && localData.logs) {
      console.log("使用本地日志数据");
      taskLogs.value = localData.logs;
      // 过滤出iostat类型的日志，用于数据表格
      availableLogs.value = localData.logs.filter(
        (log) => log.log_type === "iostat",
      );
      if (availableLogs.value.length > 0) {
        selectedLog.value = availableLogs.value[0].id;
        loadIOStatMetrics();
      }
    } else {
      // 本地没有数据，从API获取
      const response = await getTaskLogs(taskId.value, {
        node_id: selectedNode.value,
      });
      if (response && response.data) {
        taskLogs.value = response.data;
        // 过滤出iostat类型的日志，用于数据表格
        availableLogs.value = response.data.filter(
          (log) => log.log_type === "iostat",
        );
        if (availableLogs.value.length > 0) {
          selectedLog.value = availableLogs.value[0].id;
          loadIOStatMetrics();
        }

        // 保存到本地
        const taskData = localDataManager.getTaskData(taskId.value) || {};
        taskData.logs = response.data;
        localDataManager.saveTaskData(taskId.value, taskData);
      }
    }
  } catch (error) {
    console.error("加载任务日志失败:", error);
    console.error("错误详情:", error.response?.data || error.message || error);
    console.error("请求URL:", `/api/logs/task/${taskId.value}`, "节点ID:", selectedNode.value);
  } finally {
    loading.value = false;
  }
};

// 加载IOSTAT指标数据（保留旧方法但使用新的变量名）
const loadIOStatMetrics = async () => {
  if (!selectedLog.value) return;

  loading.value = true;
  try {
    // 优先从本地获取数据
    const localLogData = localDataManager.getLogFile(
      taskId.value,
      selectedLog.value,
    );

    if (localLogData && localLogData.metrics) {
      console.log("使用本地性能指标数据");
      rawIOStatData.value = localLogData.metrics;

      // 提取所有设备名称
      const devices = [
        ...new Set(localLogData.metrics.map((item) => item.device)),
      ];
      availableDevices.value = devices;
      if (devices.length > 0) {
        selectedDevices.value = devices;
      }

      updateDataTable();
    } else {
      // 本地没有数据，从API获取
      const response = await getIOStatMetrics(selectedLog.value);
      console.log("API响应:", response);
      if (response && response.data) {
        console.log("API返回数据:", response.data);
        rawIOStatData.value = response.data;

        // 提取所有设备名称
        const devices = [...new Set(response.data.map((item) => item.device))];
        availableDevices.value = devices;
        if (devices.length > 0) {
          selectedDevices.value = devices;
        }

        updateDataTable();

        // 保存到本地
        localDataManager.saveLogFile(taskId.value, selectedLog.value, {
          metrics: response.data,
          log_type: "fio",
        });
      }
    }
  } catch (error) {
    console.error("加载性能指标数据失败:", error);
  } finally {
    loading.value = false;
  }
};

// 更新数据表格
const updateDataTable = () => {
  if (!rawIOStatData.value.length) {
    displayedData.value = [];
    return;
  }

  let filteredData = rawIOStatData.value;

  // 按节点过滤（支持多选）
  if (selectedNodes.value && selectedNodes.value.length > 0) {
    filteredData = filteredData.filter(
      (item) => selectedNodes.value.includes(item.node_id),
    );
  }

  // 按设备过滤（支持多选）
  if (selectedDevices.value && selectedDevices.value.length > 0) {
    filteredData = filteredData.filter(
      (item) => selectedDevices.value.includes(item.device),
    );
  }

  // 直接展示原始数据，不自动分组汇总，保留每个节点和分区的详细信息
  displayedData.value = filteredData.map((item) => {
    // 计算总IOPS和总吞吐量
    const total_iops = parseFloat(item.read_iops || 0) + parseFloat(item.write_iops || 0);
    const total_kbps = parseFloat(item.read_kbps || 0) + parseFloat(item.write_kbps || 0);
    
    // 处理IO模型开始时间和结束时间
    let ioStartDate = new Date();
    let ioEndDate = new Date();
    
    if (item.io_start_time) {
      ioStartDate = new Date(item.io_start_time);
    } else if (item.collection_time) {
      ioStartDate = new Date(item.collection_time);
    } else if (item.timestamp) {
      ioStartDate = new Date(item.timestamp);
    }
    
    if (item.io_end_time) {
      ioEndDate = new Date(item.io_end_time);
    } else {
      ioEndDate = ioStartDate;
    }
    
    return {
      io_model_name: item.io_model_name || '未知IO模型',
      io_start_time: ioStartDate.toLocaleString(),
      io_end_time: ioEndDate.toLocaleString(),
      device: item.device,
      total_iops: total_iops.toFixed(2),
      total_kbps: total_kbps.toFixed(2),
      await_time: parseFloat(item.await_time || 0).toFixed(2),
      read_iops: parseFloat(item.read_iops || 0).toFixed(2),
      write_iops: parseFloat(item.write_iops || 0).toFixed(2),
      read_kbps: parseFloat(item.read_kbps || 0).toFixed(2),
      write_kbps: parseFloat(item.write_kbps || 0).toFixed(2),
      lat_p99: parseFloat(item.lat_p99 || 0).toFixed(2),
      lat_max: parseFloat(item.lat_max || 0).toFixed(2),
      // 保留原始数据的其他字段
      collection_time: item.collection_time
    };
  });
};

// 查看日志详情
const viewLogDetails = (logId) => {
  // 跳转到日志详情页面
  router.push(`/logs/${logId}`);
};

// 查看抖动图表
const viewJitterChart = (logId) => {
  // 跳转到抖动图表页面
  router.push(`/io-jitter-chart/${taskId.value}?logId=${logId}`);
};

// 处理标签页切换
const handleTabChange = (tabName) => {
  console.log("切换到标签页:", tabName);
  if (tabName === "data-table") {
    console.log("准备加载详细数据...");
    // 确保有选中的节点和设备
    if (selectedNodes.value.length === 0 && taskNodes.value.length > 0) {
      selectedNodes.value = taskNodes.value.map(node => node.id);
    }
    if (selectedDevices.value.length === 0 && availableDevices.value.length > 0) {
      selectedDevices.value = Array.from(availableDevices.value);
    }
    // 加载FIO日志数据
    loadFioMetricsFromLogs();
  }
};

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return "-";
  const date = new Date(dateString);
  return date.toLocaleString();
};

// 获取状态标签
const getStatusLabel = (status) => {
  const statusMap = {
    pending: "等待中",
    running: "运行中",
    completed: "已完成",
    failed: "失败",
    cancelled: "已取消",
  };
  return statusMap[status] || status || "-";
};

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

// 导出数据
const exportData = () => {
  if (!displayedData.value.length) {
    return;
  }

  // 将数据转换为CSV格式
  const headers = [
    "IO模型名称",
    "IO模型开始时间",
    "IO模型结束时间",
    "分区",
    "总IOPS",
    "总吞吐量(KB/s)",
    "平均时延(ms)",
    "读IOPS",
    "写IOPS",
    "读吞吐量(KB/s)",
    "写吞吐量(KB/s)",
    "p99时延(ms)",
    "最大时延(ms)",
  ];
  const csvContent = [
    headers.join(","),
    ...displayedData.value.map((row) =>
      [
        row.io_model_name,
        row.io_start_time,
        row.io_end_time,
        row.device,
        row.total_iops,
        row.total_kbps,
        row.await_time,
        row.read_iops,
        row.write_iops,
        row.read_kbps,
        row.write_kbps,
        row.lat_p99,
        row.lat_max,
      ].join(","),
    ),
  ].join("\n");

  // 创建下载链接
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute(
    "download",
    `io_test_results_${taskId.value}_${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.csv`,
  );
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// 处理文件上传
const handleFileUpload = async (file) => {
  try {
    loading.value = true;
    const success = await localDataManager.processUploadedFile(
      file.raw,
      taskId.value,
    );
    if (success) {
      ElMessage.success("文件上传成功");
      // 重新加载数据
      loadTaskInfo();
    } else {
      ElMessage.error("文件上传失败");
    }
  } catch (error) {
    console.error("文件上传失败:", error);
    ElMessage.error("文件上传失败: " + error.message);
  } finally {
    loading.value = false;
  }
};

// 组件挂载时
onMounted(() => {
  loadTaskInfo();
});
</script>

<style scoped>
.results-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-tabs {
  margin-top: 20px;
}

.overview-section {
  margin-bottom: 20px;
}

.logs-section {
  margin-bottom: 20px;
}

.data-table-section {
  margin-bottom: 20px;
}

.data-controls {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}
</style>
