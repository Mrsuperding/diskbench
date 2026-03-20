<template>
  <div class="task-detail-container">
    <!-- 页面标题和操作按钮 -->
    <div class="page-header">
      <h1 class="page-title">任务详情</h1>
      <div class="page-actions">
        <el-button
          type="primary"
          :disabled="taskDetail.status === 'completed'"
          @click="startTask"
        >
          开始任务
        </el-button>
        <el-button
          type="warning"
          :disabled="taskDetail.status !== 'running'"
          @click="pauseTask"
        >
          暂停任务
        </el-button>
        <el-button type="danger" @click="deleteTask"> 删除任务 </el-button>
        <el-button type="success" @click="showAddDialog"> 增加 </el-button>
        <el-button type="primary" @click="showDetailedDataDialog">
          详细数据
        </el-button>
        <el-button type="info" @click="navigateToIOJitterChart">
          性能抖动图表
        </el-button>
        <el-button type="info" @click="navigateToIOStatChart">
          IOSTAT性能图表
        </el-button>
        <el-button type="success" @click="downloadTaskLogs">
          下载日志
        </el-button>
      </div>
    </div>

    <!-- 任务详情卡片 -->
    <el-card class="task-detail-card">
      <!-- 任务基本信息 - 可展开 -->
      <el-collapse
        v-model="activeNames"
        accordion
        @change="handleActiveNamesChange"
      >
        <!-- 任务详情 -->
        <el-collapse-item title="任务详情" name="1">
          <div class="task-info">
            <el-form label-position="top" :model="taskDetail">
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="任务名称">
                    <el-input
                      v-model="taskDetail.name"
                      placeholder="请输入任务名称"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="任务ID">
                    <el-input
                      v-model="taskDetail.id"
                      disabled
                      placeholder="任务ID"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="状态">
                    <el-tag :type="getStatusType(taskDetail.status)">
                      {{ getStatusText(taskDetail.status) }}
                    </el-tag>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="优先级">
                    <el-tag :type="getPriorityType(taskDetail.priority)">
                      {{ getPriorityText(taskDetail.priority) }}
                    </el-tag>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="创建时间">
                    <el-input
                      v-model="taskDetail.created_at"
                      disabled
                      placeholder="创建时间"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="更新时间">
                    <el-input
                      v-model="taskDetail.updated_at"
                      disabled
                      placeholder="更新时间"
                    />
                  </el-form-item>
                </el-col>
              </el-row>

              <!-- 任务失败原因 -->
              <el-row :gutter="20">
                <el-col :span="24">
                  <el-form-item
                    label="失败原因"
                    v-if="taskDetail.status === 'failed'"
                  >
                    <el-input
                      v-model="taskDetail.error_message"
                      type="textarea"
                      :rows="3"
                      disabled
                      placeholder="任务执行失败的原因"
                    />
                  </el-form-item>
                </el-col>
              </el-row>

              <!-- 定时运行设置 -->
              <el-form-item label="定时运行设置">
                <el-date-picker
                  v-model="scheduledTime"
                  type="datetime"
                  placeholder="选择定时运行时间"
                  format="YYYY-MM-DD HH:mm:ss"
                  value-format="YYYY-MM-DD HH:mm:ss"
                />
                <el-button
                  type="primary"
                  size="small"
                  style="margin-left: 10px"
                  @click="setScheduledTime"
                >
                  设置定时
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-collapse-item>

        <!-- 节点列表 -->
        <el-collapse-item title="节点列表" name="2">
          <div class="node-section" v-if="taskNodes.length > 0">
            <el-table
              :data="taskNodes"
              style="width: 100%"
              border
              stripe
              @row-click="selectNode"
            >
              <el-table-column prop="id" label="节点ID" width="80" />
              <el-table-column prop="name" label="节点名称" />
              <el-table-column prop="ip_address" label="IP地址" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="scope">
                  <el-tag
                    :type="scope.row.status === 'active' ? 'success' : 'danger'"
                  >
                    {{ scope.row.status === "active" ? "在线" : "离线" }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150">
                <template #default="scope">
                  <el-button
                    v-if="!editIpDialogVisible"
                    type="primary"
                    size="small"
                    @click="startEditIp(scope.row)"
                  >
                    编辑IP信息
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <div class="selection-info" v-if="selectedNode">
              <p>已选中节点: {{ selectedNode.name }}</p>
              <el-button type="danger" size="small" @click="deleteSelectedItem">
                删除选中节点
              </el-button>
            </div>
          </div>
          <div v-else class="no-data">暂无节点信息</div>
        </el-collapse-item>

        <!-- IO任务列表 -->
        <el-collapse-item title="IO任务列表" name="3">
          <div class="io-task-section">
            <el-table :data="ioTasks" style="width: 100%" border stripe>
              <el-table-column prop="id" label="IO任务ID" width="80" />
              <el-table-column label="IO任务名称">
                <template #default="scope">
                  <a href="#" @click.prevent="editIOTask(scope.row)">{{
                    scope.row.name
                  }}</a>
                </template>
              </el-table-column>
              <el-table-column prop="type" label="类型" width="100" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="scope">
                  <el-tag :type="getStatusType(scope.row.status)">
                    {{ getStatusText(scope.row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="progress" label="进度" width="150">
                <template #default="scope">
                  <el-progress :percentage="scope.row.progress || 0" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="scope">
                  <el-button
                    type="danger"
                    size="small"
                    @click="deleteIOTask(scope.row)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-collapse-item>

        <!-- 日志输出 -->
        <el-collapse-item title="日志输出" name="4">
          <div class="task-logs">
            <!-- 日志过滤和搜索 -->
            <div class="log-filter" style="margin-bottom: 10px">
              <el-select
                v-model="logFilter.level"
                placeholder="日志级别"
                style="width: 120px; margin-right: 10px"
              >
                <el-option label="全部" value="" />
                <el-option label="DEBUG" value="DEBUG" />
                <el-option label="INFO" value="INFO" />
                <el-option label="WARNING" value="WARNING" />
                <el-option label="ERROR" value="ERROR" />
                <el-option label="CRITICAL" value="CRITICAL" />
              </el-select>
              <el-input
                v-model="logFilter.keyword"
                placeholder="搜索关键词"
                style="width: 200px; margin-right: 10px"
              >
                <template #append>
                  <el-button @click="clearLogFilter">清空</el-button>
                </template>
              </el-input>
              <el-button type="primary" @click="filterLogs">过滤</el-button>
            </div>

            <!-- 日志列表 -->
            <el-scrollbar height="400px">
              <div
                v-for="log in filteredLogs"
                :key="log.id"
                :class="[
                  'log-item',
                  'log-level-' +
                    (typeof log.level === 'string'
                      ? log.level
                      : 'info'
                    ).toLowerCase(),
                ]"
              >
                <div class="log-header">
                  <span class="log-time">{{
                    formatLogTime(log.timestamp)
                  }}</span>
                  <span
                    class="log-level"
                    :class="
                      'log-level-' +
                      (typeof log.level === 'string'
                        ? log.level
                        : 'info'
                      ).toLowerCase()
                    "
                    >{{ log.level || "INFO" }}</span
                  >
                  <span class="log-module">{{ log.module }}</span>
                </div>
                <div class="log-content">{{ log.message }}</div>
                <div
                  v-if="
                    log.context &&
                    typeof log.context === 'object' &&
                    Object.keys(log.context).length > 0
                  "
                  class="log-context"
                >
                  <el-button
                    type="text"
                    size="small"
                    @click="showLogContext(log.context)"
                    >查看上下文</el-button
                  >
                </div>
              </div>
              <div v-if="filteredLogs.length === 0" class="no-logs">
                暂无日志
              </div>
            </el-scrollbar>

            <el-button
              type="primary"
              size="small"
              @click="loadMoreLogs"
              style="margin-top: 10px"
            >
              加载更多日志
            </el-button>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- 增加对话框 -->
    <el-dialog
      v-model="addDialogVisible"
      :title="addType === 'node' ? '新增节点' : '新增IO测试用例'"
      width="500px"
    >
      <el-form label-width="120px">
        <el-form-item v-if="addType === 'node'" label="节点名称">
          <el-input placeholder="请输入节点名称" />
        </el-form-item>
        <el-form-item v-if="addType === 'node'" label="IP地址">
          <el-input placeholder="请输入IP地址" />
        </el-form-item>
        <el-form-item v-if="addType === 'node'" label="端口">
          <el-input placeholder="请输入端口" />
        </el-form-item>
        <el-form-item v-if="addType === 'io_case'" label="用例名称">
          <el-input placeholder="请输入IO测试用例名称" />
        </el-form-item>
        <el-form-item v-if="addType === 'io_case'" label="类型">
          <el-select placeholder="请选择类型">
            <el-option label="随机读" value="randread" />
            <el-option label="随机写" value="randwrite" />
            <el-option label="顺序读" value="read" />
            <el-option label="顺序写" value="write" />
            <el-option label="随机读写" value="randrw" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="addDialogVisible = false"
            >确定</el-button
          >
        </span>
      </template>
    </el-dialog>

    <!-- 编辑IP信息对话框 -->
    <el-dialog v-model="editIpDialogVisible" title="编辑IP信息" width="500px">
      <el-form label-width="120px">
        <el-form-item label="IP地址">
          <el-input
            v-model="editingNode.ip_address"
            placeholder="请输入IP地址"
          />
        </el-form-item>

        <!-- IO分区列表 -->
        <el-form-item label="IO分区">
          <el-table
            :data="ioPartitions"
            style="width: 100%; margin-bottom: 10px"
            border
          >
            <el-table-column prop="name" label="分区名称" />
            <el-table-column prop="path" label="分区路径" />
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button
                  type="danger"
                  size="small"
                  @click="removePartition(scope.$index)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 添加分区表单 -->
          <div class="add-partition-form">
            <el-input
              v-model="newPartition.name"
              placeholder="分区名称"
              style="width: 200px; margin-right: 10px"
            />
            <el-input
              v-model="newPartition.path"
              placeholder="分区路径"
              style="width: 200px; margin-right: 10px"
            />
            <el-button type="primary" size="small" @click="addPartition">
              添加分区
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cancelEditIp">取消</el-button>
          <el-button type="primary" @click="saveEditIp">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 详细数据对话框 -->
    <el-dialog
      v-model="detailedDataDialogVisible"
      title="任务详细数据"
      width="90%"
      :fullscreen="false"
    >
      <el-table :data="detailedData" style="width: 100%">
        <el-table-column
          prop="ioModelName"
          label="IO模型"
          width="200"
        ></el-table-column>
        <el-table-column
          prop="nodeName"
          label="节点名称"
          width="150"
        ></el-table-column>
        <el-table-column
          prop="nodeIp"
          label="节点IP"
          width="150"
        ></el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag
              :type="scope.row.status === 'completed' ? 'success' : 'danger'"
            >
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="createdAt"
          label="创建时间"
          width="200"
        ></el-table-column>
        <el-table-column label="详细结果" width="120">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click="showResultDetails(scope.row)"
            >
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 编辑IO用例模型对话框 -->
    <IOCaseEditor
      v-model="editIOTaskDialogVisible"
      :dialogTitle="editIOTaskDialogTitle"
      :showStatus="true"
      :initialData="currentIOTaskData"
      @submit="handleIOTaskSubmit"
    />
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, computed, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import tasksApi from "../api/tasks";
import nodesApi from "../api/nodes";
import ioCasesApi from "../api/ioCases";
import { useRoute, useRouter } from "vue-router";
import { io } from "socket.io-client";
import * as echarts from "echarts";
import { use } from "echarts/core";
import { LineChart, BarChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import IOCaseEditor from "../components/IOCaseEditor.vue";

// 注册ECharts组件
use([
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  CanvasRenderer,
]);

export default {
  name: "TaskDetail",
  components: {
    IOCaseEditor,
  },
  setup() {
    // 路由
    const route = useRoute();
    const taskId = computed(() => route.params.id);

    // 展开面板状态 - 默认展开日志输出面板
    const activeNames = ref(["4"]);

    // 任务详情数据
    const taskDetail = reactive({
      id: "",
      name: "",
      description: "",
      status: "pending",
      priority: "medium",
      created_at: "",
      updated_at: "",
      // IO任务相关字段
      io_test_case_ids: [], // 与后端保持一致的字段名
      progress: 0,
      // 节点相关字段
      node_ids: [],
      node_id: "",
    });

    // 节点列表
    const nodes = ref([]);

    // 解析的iostat指标数据
    const iostatMetrics = ref([]);

    // iostat图表实例
    let iostatChartInstance = null;

    // 当前任务节点列表（支持多个节点）
    const taskNodes = ref([]);

    // 选中的节点
    const selectedNode = ref(null);

    // 选中的IO测试用例
    const selectedIOCase = ref(null);

    // IO任务列表
    const ioTasks = ref([]);

    // 选中的IO任务
    const selectedIOTask = ref(null);

    // 增加对话框
    const addDialogVisible = ref(false);
    const addType = ref(""); // 'node' 或 'io_case'

    // 编辑IO用例模型对话框
    const editIOTaskDialogVisible = ref(false);
    const editIOTaskDialogTitle = ref("编辑IO用例模型");
    const editingIOTask = ref(null);
    const currentIOTaskData = ref({});

    // 处理IO任务表单提交
    const handleIOTaskSubmit = async (taskData) => {
      try {
        // 调用API更新IO测试用例
        await ioCasesApi.updateIOCase(editingIOTask.value.id, taskData);

        // 更新本地数据
        const index = ioTasks.value.findIndex(
          (t) => t.id === editingIOTask.value.id,
        );
        if (index > -1) {
          // 更新本地数据
          const updatedTask = {
            ...ioTasks.value[index],
            ...taskData,
          };

          // 如果有io_cases数组，也更新其中的数据
          if (updatedTask.io_cases && updatedTask.io_cases.length > 0) {
            updatedTask.io_cases[0] = {
              ...updatedTask.io_cases[0],
              ...taskData,
            };
          }

          ioTasks.value[index] = updatedTask;
          ElMessage.success("IO任务更新成功");
          editIOTaskDialogVisible.value = false;
        }
      } catch (error) {
        ElMessage.error("IO任务更新失败: " + error.message);
      }
    };

    // 日志数据
    const logs = ref([]);

    // 日志过滤条件
    const logFilter = reactive({
      level: "",
      keyword: "",
    });

    // 过滤后的日志
    const filteredLogs = computed(() => {
      let result = [...logs.value];

      // 按级别过滤
      if (logFilter.level) {
        result = result.filter((log) => log.level === logFilter.level);
      }

      // 按关键词过滤
      if (logFilter.keyword) {
        const keyword = logFilter.keyword.toLowerCase();
        result = result.filter(
          (log) =>
            (typeof log.message === "string" &&
              log.message.toLowerCase().includes(keyword)) ||
            (log.context &&
              typeof log.context === "object" &&
              JSON.stringify(log.context).toLowerCase().includes(keyword)),
        );
      }

      return result;
    });

    // WebSocket相关
    const socket = ref(null);
    let logId = 1;

    // 详细数据对话框
    const detailedDataDialogVisible = ref(false);
    const detailedData = ref([]);
    const testResults = ref([]);

    // 定时运行时间
    const scheduledTime = ref("");

    // 编辑IP对话框可见状态
    const editIpDialogVisible = ref(false);

    // 编辑中的节点数据
    const editingNode = reactive({
      id: "",
      ip_address: "",
    });

    // IO分区列表
    const ioPartitions = ref([]);

    // 新添加的分区
    const newPartition = reactive({
      name: "",
      path: "",
    });

    // 初始化WebSocket连接
    const initWebSocket = () => {
      console.log("初始化WebSocket连接，任务ID:", taskId.value);
      // 创建WebSocket连接
      socket.value = io("http://localhost:5003", {
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

        // 处理新的结构化日志格式
        if (data && typeof data === "object" && data.data) {
          const logData = data.data;
          logs.value.push({
            id: logId++,
            timestamp: logData.timestamp || new Date().toLocaleString(),
            level: logData.level || "INFO",
            module: logData.module || "tasks",
            message: logData.message,
            context: logData.context || {},
          });
          console.log("添加结构化日志:", logData);
        } else {
          // 兼容旧格式
          let logContent = "";
          if (data && typeof data === "object") {
            if (data.log) {
              logContent = data.log;
            } else {
              logContent = JSON.stringify(data);
            }
          } else if (typeof data === "string") {
            logContent = data;
          }

          if (typeof logContent === "string") {
            const logLines = logContent.split("\n");
            logLines.forEach((line) => {
              if (line.trim()) {
                logs.value.push({
                  id: logId++,
                  timestamp: new Date().toLocaleString(),
                  level: "INFO",
                  module: "tasks",
                  message: line.trim(),
                  context: {},
                });
                console.log("添加旧格式日志:", line.trim());

                // 尝试解析iostat日志
                parseIostatLog(line.trim());
              }
            });
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
        logs.value.push({
          id: logId++,
          timestamp: new Date().toLocaleString(),
          content: `已加入任务日志房间: ${data.message}`,
        });
      });

      // 接收错误
      socket.value.on("error", (error) => {
        console.error("WebSocket错误:", error);
        logs.value.push({
          id: logId++,
          timestamp: new Date().toLocaleString(),
          content: `WebSocket错误: ${JSON.stringify(error)}`,
        });
      });

      // 接收连接断开
      socket.value.on("disconnect", (reason) => {
        console.log("WebSocket连接断开:", reason);
        logs.value.push({
          id: logId++,
          timestamp: new Date().toLocaleString(),
          content: `WebSocket连接断开: ${reason}`,
        });
      });

      // 接收重连尝试
      socket.value.on("reconnect_attempt", (attempt) => {
        console.log(`WebSocket重连尝试 ${attempt}`);
        logs.value.push({
          id: logId++,
          timestamp: new Date().toLocaleString(),
          content: `WebSocket重连尝试 ${attempt}`,
        });
      });

      // 接收重连成功
      socket.value.on("reconnect", (attempt) => {
        console.log(`WebSocket重连成功，尝试次数: ${attempt}`);
        logs.value.push({
          id: logId++,
          timestamp: new Date().toLocaleString(),
          content: `WebSocket重连成功，尝试次数: ${attempt}`,
        });
        // 重新加入任务日志房间
        socket.value.emit("join_task_room", { task_id: taskId.value });
      });

      // 接收重连失败
      socket.value.on("reconnect_failed", () => {
        console.error("WebSocket重连失败");
        logs.value.push({
          id: logId++,
          timestamp: new Date().toLocaleString(),
          content: "WebSocket重连失败",
        });
      });
    };

    // 获取任务详情
    const getTaskDetail = async () => {
      try {
        const response = await tasksApi.getTask(taskId.value);
        Object.assign(taskDetail, response.data);
        // 设置定时时间
        if (response.data.scheduled_at) {
          scheduledTime.value = response.data.scheduled_at;
        }
        // 加载相关数据
        loadRelatedData();

        // 初始化WebSocket连接
        initWebSocket();
      } catch (error) {
        ElMessage.error("获取任务详情失败: " + error.message);
      }
    };

    // 加载测试结果数据
    const loadTestResults = async () => {
      try {
        // 获取任务的测试结果
        const resultsResponse = await tasksApi.getTaskResults(taskId.value);
        testResults.value = resultsResponse.data;

        // 处理详细数据
        let processedData = [];

        // 检查返回的数据结构
        if (Array.isArray(testResults.value)) {
          // 处理API返回的实时FIO日志指标数据结构
          testResults.value.forEach((result, index) => {
            const node = taskNodes.value.find((n) => n.id === result.node_id);

            processedData.push({
              id: `${result.node_id}_${index}`,
              ioModelName: result.io_model_name || "未知IO模型",
              nodeName: node ? node.name : "未知节点",
              nodeIp: node ? node.ip_address : "未知IP",
              status: "success", // 假设所有返回的结果都是成功的
              createdAt: result.collection_time || new Date().toISOString(),
              rawResult: JSON.stringify(result),
              parsedResult: result,
            });
          });
        } else {
          // 处理旧的数据结构
          testResults.value.forEach((result) => {
            const ioTestCase = ioTasks.value.find(
              (task) => task.id === result.io_test_case_id,
            );
            const node = taskNodes.value.find((n) => n.id === result.node_id);

            // 检查parsed_results是否为数组（多个测试组合）
            if (Array.isArray(result.parsed_results)) {
              // 为每个测试组合创建一个条目
              result.parsed_results.forEach((testResult, index) => {
                processedData.push({
                  id: `${result.id}_${index}`,
                  ioModelName: ioTestCase
                    ? `${ioTestCase.name} (${testResult.params.io_type}, ${testResult.params.blocksize}, ${testResult.params.iodepth})`
                    : "未知IO模型",
                  nodeName: node ? node.name : "未知节点",
                  nodeIp: node ? node.ip_address : "未知IP",
                  status: testResult.success ? "success" : "failed",
                  createdAt: result.created_at,
                  rawResult: testResult.raw_output,
                  parsedResult: testResult,
                });
              });
            } else {
              // 单个测试结果
              processedData.push({
                id: result.id,
                ioModelName: ioTestCase ? ioTestCase.name : "未知IO模型",
                nodeName: node ? node.name : "未知节点",
                nodeIp: node ? node.ip_address : "未知IP",
                status: result.status,
                createdAt: result.created_at,
                rawResult: result.raw_output,
                parsedResult: result.parsed_results,
              });
            }
          });
        }
        detailedData.value = processedData;
      } catch (error) {
        console.error("加载测试结果失败:", error);
        ElMessage.error("加载测试结果失败");
      }
    };

    // 加载相关数据
    const loadRelatedData = async () => {
      try {
        // 加载节点数据 - 支持单个节点和多个节点
        if (
          taskDetail.node_ids &&
          Array.isArray(taskDetail.node_ids) &&
          taskDetail.node_ids.length > 0
        ) {
          // 处理多个节点
          const nodePromises = taskDetail.node_ids.map((nodeId) =>
            nodesApi.getNode(nodeId),
          );
          const nodeResponses = await Promise.all(nodePromises);
          taskNodes.value = nodeResponses.map((response) => ({
            ...response.data,
            io_partitions: response.data.io_partitions || [],
          }));
        } else if (taskDetail.node_id) {
          // 兼容单个节点的情况
          const nodeResponse = await nodesApi.getNode(taskDetail.node_id);
          taskNodes.value = [
            {
              ...nodeResponse.data,
              io_partitions: nodeResponse.data.io_partitions || [],
            },
          ];
        } else {
          // 没有节点数据
          taskNodes.value = [];
        }

        // 获取IO任务数据
        try {
          // 获取所有IO测试用例
          const ioCasesResponse = await ioCasesApi.getIOCases();

          // 确保获取到正确的数据结构
          let allIOCases = [];
          if (ioCasesResponse && ioCasesResponse.data) {
            allIOCases = Array.isArray(ioCasesResponse.data)
              ? ioCasesResponse.data
              : [];
          }

          console.log("获取到的所有IO测试用例:", allIOCases);
          console.log("任务详情:", taskDetail);
          console.log(
            "任务详情中的IO测试用例ID列表:",
            taskDetail.io_test_case_ids,
          );

          // 从任务详情中获取与当前任务相关的IO测试用例
          if (
            taskDetail &&
            taskDetail.io_test_case_ids &&
            Array.isArray(taskDetail.io_test_case_ids)
          ) {
            const taskIOCaseIds = taskDetail.io_test_case_ids;
            console.log("任务关联的IO测试用例ID:", taskIOCaseIds);

            // 只获取当前任务关联的IO测试用例
            const taskIOCases = [];
            for (const ioCaseId of taskIOCaseIds) {
              const matchedCase = allIOCases.find(
                (ioCase) => ioCase.id === ioCaseId,
              );
              if (matchedCase) {
                taskIOCases.push(matchedCase);
              } else {
                console.warn(`未找到ID为${ioCaseId}的IO测试用例`);
              }
            }

            console.log("任务关联的IO测试用例:", taskIOCases);

            // 构建IO任务列表
            if (taskIOCases.length > 0) {
              ioTasks.value = taskIOCases.map((ioCase) => {
                // 查找该IO用例的测试结果，获取真实状态
                const ioCaseResults = testResults.value.filter(
                  (result) => result.io_test_case_id === ioCase.id,
                );

                // 确定IO任务的状态
                let ioStatus = "pending";
                if (ioCaseResults.length > 0) {
                  // 检查是否有失败的结果
                  const hasFailed = ioCaseResults.some(
                    (result) => result.status === "failed",
                  );
                  if (hasFailed) {
                    ioStatus = "failed";
                  } else {
                    // 检查是否所有结果都已完成
                    const allCompleted = ioCaseResults.every(
                      (result) => result.status === "completed",
                    );
                    if (allCompleted) {
                      ioStatus = "completed";
                    } else {
                      // 检查是否有运行中的结果
                      const hasRunning = ioCaseResults.some(
                        (result) => result.status === "running",
                      );
                      if (hasRunning) {
                        ioStatus = "running";
                      }
                    }
                  }
                } else if (taskDetail.status === "completed") {
                  // 如果任务已完成，但没有该IO用例的结果，可能是跳过了
                  ioStatus = "skipped";
                } else {
                  // 否则使用任务状态
                  ioStatus = taskDetail.status || "pending";
                }

                return {
                  id: ioCase.id,
                  name: ioCase.name || "未命名IO任务",
                  type:
                    ioCase.parameters?.read_write_mode || ioCase.type || "read",
                  status: ioStatus,
                  progress:
                    ioCaseResults.length > 0 ? 100 : taskDetail.progress || 0,
                  io_cases: [ioCase],
                  results: ioCaseResults,
                };
              });
            } else {
              // 如果没有找到任何关联的IO测试用例，显示所有IO测试用例
              console.log("没有找到关联的IO测试用例，显示所有IO测试用例");
              ioTasks.value = allIOCases.map((ioCase) => {
                // 查找该IO用例的测试结果，获取真实状态
                const ioCaseResults = testResults.value.filter(
                  (result) => result.io_test_case_id === ioCase.id,
                );

                // 确定IO任务的状态
                let ioStatus = "pending";
                if (ioCaseResults.length > 0) {
                  // 检查是否有失败的结果
                  const hasFailed = ioCaseResults.some(
                    (result) => result.status === "failed",
                  );
                  if (hasFailed) {
                    ioStatus = "failed";
                  } else {
                    // 检查是否所有结果都已完成
                    const allCompleted = ioCaseResults.every(
                      (result) => result.status === "completed",
                    );
                    if (allCompleted) {
                      ioStatus = "completed";
                    } else {
                      // 检查是否有运行中的结果
                      const hasRunning = ioCaseResults.some(
                        (result) => result.status === "running",
                      );
                      if (hasRunning) {
                        ioStatus = "running";
                      }
                    }
                  }
                } else if (taskDetail.status === "completed") {
                  // 如果任务已完成，但没有该IO用例的结果，可能是跳过了
                  ioStatus = "skipped";
                } else {
                  // 否则使用任务状态
                  ioStatus = taskDetail.status || "pending";
                }

                return {
                  id: ioCase.id,
                  name: ioCase.name || "未命名IO任务",
                  type:
                    ioCase.parameters?.read_write_mode || ioCase.type || "read",
                  status: ioStatus,
                  progress:
                    ioCaseResults.length > 0 ? 100 : taskDetail.progress || 0,
                  io_cases: [ioCase],
                  results: ioCaseResults,
                };
              });
            }
          } else {
            // 如果任务详情中没有IO测试用例ID列表，显示所有IO测试用例
            console.log("任务详情中没有IO测试用例ID列表，显示所有IO测试用例");
            ioTasks.value = allIOCases.map((ioCase) => {
              // 查找该IO用例的测试结果，获取真实状态
              const ioCaseResults = testResults.value.filter(
                (result) => result.io_test_case_id === ioCase.id,
              );

              // 确定IO任务的状态
              let ioStatus = "pending";
              if (ioCaseResults.length > 0) {
                // 检查是否有失败的结果
                const hasFailed = ioCaseResults.some(
                  (result) => result.status === "failed",
                );
                if (hasFailed) {
                  ioStatus = "failed";
                } else {
                  // 检查是否所有结果都已完成
                  const allCompleted = ioCaseResults.every(
                    (result) => result.status === "completed",
                  );
                  if (allCompleted) {
                    ioStatus = "completed";
                  } else {
                    // 检查是否有运行中的结果
                    const hasRunning = ioCaseResults.some(
                      (result) => result.status === "running",
                    );
                    if (hasRunning) {
                      ioStatus = "running";
                    }
                  }
                }
              } else if (taskDetail.status === "completed") {
                // 如果任务已完成，但没有该IO用例的结果，可能是跳过了
                ioStatus = "skipped";
              } else {
                // 否则使用任务状态
                ioStatus = taskDetail.status || "pending";
              }

              return {
                id: ioCase.id,
                name: ioCase.name || "未命名IO任务",
                type:
                  ioCase.parameters?.read_write_mode || ioCase.type || "read",
                status: ioStatus,
                progress:
                  ioCaseResults.length > 0 ? 100 : taskDetail.progress || 0,
                io_cases: [ioCase],
                results: ioCaseResults,
              };
            });
          }

          console.log("最终的IO任务列表:", ioTasks.value);

          // 加载测试结果数据
          await loadTestResults();
        } catch (error) {
          console.error("加载IO测试用例失败:", error);
          ElMessage.error("加载IO测试用例失败: " + error.message);
          // 如果API调用失败，使用任务详情中的IO测试用例信息
          if (
            taskDetail.io_test_cases &&
            Array.isArray(taskDetail.io_test_cases)
          ) {
            ioTasks.value = taskDetail.io_test_cases.map((ioCase) => ({
              id: ioCase.id || Math.random(),
              name: ioCase.name || "未命名IO任务",
              type: ioCase.parameters?.read_write_mode || ioCase.type || "read",
              status: taskDetail.status || "pending",
              progress: taskDetail.progress || 0,
              io_cases: [ioCase],
            }));
          } else if (
            taskDetail.io_test_case_ids &&
            Array.isArray(taskDetail.io_test_case_ids)
          ) {
            // 如果只有ID列表，创建简单的任务项
            ioTasks.value = taskDetail.io_test_case_ids.map((id) => ({
              id: id,
              name: `IO任务 ${id}`,
              type: "read",
              status: taskDetail.status || "pending",
              progress: taskDetail.progress || 0,
              io_cases: [],
            }));
          } else {
            // 如果没有任何IO测试用例信息，显示空列表
            ioTasks.value = [];
          }

          // 加载测试结果数据
          await loadTestResults();
        }
        // 不再需要默认展开所有行，改为点击选中查看详细信息
      } catch (error) {
        ElMessage.error("加载相关数据失败: " + error.message);
      }
    };

    // 设置定时时间
    const setScheduledTime = async () => {
      try {
        await tasksApi.updateTask(taskId.value, {
          scheduled_at: scheduledTime.value,
        });
        ElMessage.success("定时时间设置成功");
      } catch (error) {
        ElMessage.error("设置定时时间失败: " + error.message);
      }
    };

    // 开始编辑IP
    const startEditIp = (node) => {
      if (node) {
        editingNode.id = node.id;
        editingNode.ip_address = node.ip_address;
        // 初始化IO分区列表（从后端获取已保存的数据）
        ioPartitions.value = node.io_partitions || [];
        editIpDialogVisible.value = true;
      }
    };

    // 保存编辑的IP
    const saveEditIp = async () => {
      try {
        // 保存IP地址和IO分区数据
        await nodesApi.updateNode(editingNode.id, {
          ip_address: editingNode.ip_address,
          io_partitions: ioPartitions.value,
        });
        // 更新本地节点信息
        const index = taskNodes.value.findIndex(
          (node) => node.id === editingNode.id,
        );
        if (index !== -1) {
          taskNodes.value[index].ip_address = editingNode.ip_address;
          taskNodes.value[index].io_partitions = ioPartitions.value;
        }
        editIpDialogVisible.value = false;
        ElMessage.success("IP信息更新成功");
      } catch (error) {
        ElMessage.error("更新IP信息失败: " + error.message);
      }
    };

    // 取消编辑IP
    const cancelEditIp = () => {
      editIpDialogVisible.value = false;
    };

    // 添加IO分区
    const addPartition = () => {
      if (newPartition.name && newPartition.path) {
        ioPartitions.value.push({ ...newPartition });
        newPartition.name = "";
        newPartition.path = "";
      } else {
        ElMessage.warning("请填写分区名称和路径");
      }
    };

    // 删除IO分区
    const removePartition = (index) => {
      ioPartitions.value.splice(index, 1);
    };

    // 加载更多日志（保留接口，实际由WebSocket实时更新）
    const loadMoreLogs = () => {
      ElMessage.info("日志已实时更新");
    };

    // 查看结果详情
    const showResultDetails = (result) => {
      // 这里可以添加查看详细结果的逻辑
      console.log("查看结果详情:", result);
      ElMessage.info("查看结果详情功能正在开发中");
    };

    // 状态类型
    const getStatusType = (status) => {
      const types = {
        running: "primary",
        completed: "success",
        failed: "danger",
        stopped: "info",
        pending: "warning",
        cancelled: "danger",
        cancelling: "warning",
        skipped: "info",
      };
      return types[status] || "info";
    };

    // 状态文本
    const getStatusText = (status) => {
      const texts = {
        running: "运行中",
        completed: "已完成",
        failed: "失败",
        stopped: "已停止",
        pending: "待执行",
        cancelled: "已取消",
        cancelling: "取消中",
        skipped: "已跳过",
      };
      return texts[status] || status;
    };

    // 开始任务
    const startTask = async () => {
      try {
        await tasksApi.executeTask(taskId.value);
        ElMessage.success("任务开始成功");
        // 更新任务状态
        taskDetail.status = "running";
      } catch (error) {
        ElMessage.error("任务开始失败: " + error.message);
      }
    };

    // 暂停任务
    const pauseTask = async () => {
      try {
        await tasksApi.pauseTask(taskId.value);
        ElMessage.success("任务暂停成功");
        // 更新任务状态
        taskDetail.status = "stopped";
      } catch (error) {
        ElMessage.error("任务暂停失败: " + error.message);
      }
    };

    // 删除任务
    const deleteTask = async () => {
      try {
        await tasksApi.deleteTask(taskId.value);
        ElMessage.success("任务删除成功");
        // 跳转到任务列表页面
        router.push("/tasks");
      } catch (error) {
        ElMessage.error("任务删除失败: " + error.message);
      }
    };

    // 显示详细数据对话框
    const showDetailedDataDialog = async () => {
      try {
        // 加载最新的测试结果
        await loadTestResults();
      } catch (error) {
        console.error("加载测试结果失败，但仍跳转页面:", error);
      } finally {
        // 跳转到结果详情页面
        router.push(`/results?taskId=${taskId.value}`);
      }
    };

    // 显示增加对话框
    const showAddDialog = (type) => {
      addType.value = type || "node"; // 默认增加节点
      addDialogVisible.value = true;
    };

    // 选中节点
    const selectNode = (node) => {
      selectedNode.value = node;
      selectedIOCase.value = null;
      selectedIOTask.value = null;
    };

    // 选中IO任务
    const selectIOTask = (task) => {
      selectedIOTask.value = task;
      selectedNode.value = null;
      selectedIOCase.value = null;
    };

    // 选中IO测试用例
    const selectIOCase = (ioCase) => {
      selectedIOCase.value = ioCase;
      selectedNode.value = null;
      selectedIOTask.value = null;
    };

    // 编辑IO用例模型
    const editIOTask = (row) => {
      console.log("编辑IO用例模型，row数据:", row);
      editIOTaskDialogTitle.value = "编辑IO用例模型";
      editingIOTask.value = row;
      // 如果row中有io_cases数组，使用第一个元素作为initialData
      // 否则直接使用row
      if (row.io_cases && row.io_cases.length > 0) {
        console.log("使用io_cases[0]作为initialData:", row.io_cases[0]);
        currentIOTaskData.value = row.io_cases[0];
      } else {
        console.log("直接使用row作为initialData:", row);
        currentIOTaskData.value = row;
      }
      console.log("最终的currentIOTaskData:", currentIOTaskData.value);
      editIOTaskDialogVisible.value = true;
    };

    // 删除IO任务
    const deleteIOTask = (row) => {
      ElMessageBox.confirm(
        `确定要删除IO任务「${row.name}」吗？此操作不可恢复。`,
        "删除确认",
        {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
        },
      )
        .then(async () => {
          try {
            // 从本地IO任务列表中移除
            const index = ioTasks.value.findIndex((t) => t.id === row.id);
            if (index > -1) {
              ioTasks.value.splice(index, 1);
            }

            // 从任务详情的IO测试用例ID列表中移除
            const caseIndex = taskDetail.io_test_case_ids.findIndex(
              (id) => id === row.id,
            );
            if (caseIndex > -1) {
              taskDetail.io_test_case_ids.splice(caseIndex, 1);

              // 调用API更新任务的IO测试用例关联
              await tasksApi.updateTask(taskId.value, {
                io_test_case_ids: taskDetail.io_test_case_ids,
              });
            }

            ElMessage.success("IO任务删除成功");
          } catch (error) {
            ElMessage.error("IO任务删除失败: " + error.message);
          }
        })
        .catch(() => {
          // 取消删除操作
        });
    };

    // 删除选中项
    const deleteSelectedItem = async () => {
      if (selectedNode.value) {
        // 删除选中节点
        try {
          // 从本地节点列表中移除
          const index = taskNodes.value.findIndex(
            (n) => n.id === selectedNode.value.id,
          );
          if (index > -1) {
            taskNodes.value.splice(index, 1);
          }

          // 从任务详情的节点ID列表中移除
          const nodeIndex = taskDetail.node_ids.findIndex(
            (id) => id === selectedNode.value.id,
          );
          if (nodeIndex > -1) {
            taskDetail.node_ids.splice(nodeIndex, 1);

            // 调用API更新任务的节点关联
            await tasksApi.updateTask(taskId.value, {
              node_ids: taskDetail.node_ids,
            });
          }

          ElMessage.success("节点删除成功");
          selectedNode.value = null;
        } catch (error) {
          ElMessage.error("节点删除失败: " + error.message);
        }
      } else if (selectedIOTask.value) {
        // 删除选中IO任务
        try {
          // 从本地IO任务列表中移除
          const index = ioTasks.value.findIndex(
            (t) => t.id === selectedIOTask.value.id,
          );
          if (index > -1) {
            ioTasks.value.splice(index, 1);
          }

          // 从任务详情的IO测试用例ID列表中移除
          const caseIndex = taskDetail.io_test_case_ids.findIndex(
            (id) => id === selectedIOTask.value.id,
          );
          if (caseIndex > -1) {
            taskDetail.io_test_case_ids.splice(caseIndex, 1);

            // 调用API更新任务的IO测试用例关联
            await tasksApi.updateTask(taskId.value, {
              io_test_case_ids: taskDetail.io_test_case_ids,
            });
          }

          ElMessage.success("IO任务删除成功");
          selectedIOTask.value = null;
        } catch (error) {
          ElMessage.error("IO任务删除失败: " + error.message);
        }
      } else if (selectedIOCase.value) {
        // 删除选中IO测试用例
        try {
          // 从本地IO任务的IO用例列表中移除
          if (selectedIOTask.value && selectedIOTask.value.io_cases) {
            const index = selectedIOTask.value.io_cases.findIndex(
              (c) => c.id === selectedIOCase.value.id,
            );
            if (index > -1) {
              selectedIOTask.value.io_cases.splice(index, 1);
            }
          }

          // 从任务详情的IO测试用例ID列表中移除
          const caseIndex = taskDetail.io_test_case_ids.findIndex(
            (id) => id === selectedIOCase.value.id,
          );
          if (caseIndex > -1) {
            taskDetail.io_test_case_ids.splice(caseIndex, 1);

            // 调用API更新任务的IO测试用例关联
            await tasksApi.updateTask(taskId.value, {
              io_test_case_ids: taskDetail.io_test_case_ids,
            });
          }

          ElMessage.success("IO测试用例删除成功");
          selectedIOCase.value = null;
        } catch (error) {
          ElMessage.error("IO测试用例删除失败: " + error.message);
        }
      }
    };

    // 下载任务日志
    const downloadTaskLogs = async () => {
      try {
        ElMessage.info("正在准备下载日志...");
        // 调用API下载日志
        const response = await tasksApi.downloadTaskLogs(taskId.value);

        // 创建下载链接
        const blob = new Blob([response.data]);
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `task_${taskId.value}_logs.tar.gz`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        ElMessage.success("日志下载成功");
      } catch (error) {
        console.error("下载日志失败:", error);
        ElMessage.error("下载日志失败: " + error.message);
      }
    };

    // 优先级类型
    const getPriorityType = (priority) => {
      const types = {
        high: "danger",
        medium: "warning",
        low: "success",
      };
      return types[priority] || "info";
    };

    // 优先级文本
    const getPriorityText = (priority) => {
      const texts = {
        high: "高",
        medium: "中",
        low: "低",
      };
      return texts[priority] || priority;
    };

    // 解析iostat日志行
    const parseIostatLog = (line) => {
      try {
        // iostat -xdm 1 的输出格式示例:
        // Device:         rrqm/s   wrqm/s     r/s     w/s    rMB/s    wMB/s avgrq-sz avgqu-sz   await r_await w_await  svctm  %util
        // sda               0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00

        // 跳过标题行和空行
        if (!line || line.startsWith("Device:") || line.trim() === "") {
          return null;
        }

        // 使用正则表达式解析设备数据行
        // 格式: device_name  rrqm/s  wrqm/s  r/s  w/s  rMB/s  wMB/s  avgrq-sz  avgqu-sz  await  r_await  w_await  svctm  %util
        const parts = line.trim().split(/\s+/);

        if (parts.length < 14) {
          return null;
        }

        const device = parts[0];

        // 提取指标值
        const readKbps = parseFloat(parts[5]) * 1024; // rMB/s 转换为 KB/s
        const writeKbps = parseFloat(parts[6]) * 1024; // wMB/s 转换为 KB/s
        const readIOPS = parseFloat(parts[2]);
        const writeIOPS = parseFloat(parts[3]);
        const awaitTime = parseFloat(parts[9]);
        const svctm = parseFloat(parts[12]);
        const util = parseFloat(parts[13]);

        // 检查是否为有效数字
        if (
          isNaN(readKbps) ||
          isNaN(writeKbps) ||
          isNaN(readIOPS) ||
          isNaN(writeIOPS)
        ) {
          return null;
        }

        const metric = {
          timestamp: new Date().toISOString(),
          device: device,
          read_kbps: readKbps,
          write_kbps: writeKbps,
          total_kbps: readKbps + writeKbps,
          read_iops: readIOPS,
          write_iops: writeIOPS,
          total_iops: readIOPS + writeIOPS,
          await_time: awaitTime,
          svctm: svctm,
          util: util,
        };

        // 添加到指标列表
        iostatMetrics.value.push(metric);

        // 限制指标数量，防止内存溢出
        if (iostatMetrics.value.length > 1000) {
          iostatMetrics.value.shift();
        }

        console.log("解析iostat指标:", metric);
        return metric;
      } catch (error) {
        console.error("解析iostat日志失败:", error);
        return null;
      }
    };

    // 处理iostat对象数据
    const processIostatData = (data) => {
      try {
        if (data.metrics) {
          const metric = {
            timestamp: data.timestamp || new Date().toISOString(),
            device: data.metrics.device || "unknown",
            read_kbps: data.metrics.read_kbps || 0,
            write_kbps: data.metrics.write_kbps || 0,
            total_kbps:
              (data.metrics.read_kbps || 0) + (data.metrics.write_kbps || 0),
            read_iops: data.metrics.read_iops || 0,
            write_iops: data.metrics.write_iops || 0,
            total_iops:
              (data.metrics.read_iops || 0) + (data.metrics.write_iops || 0),
            await_time: data.metrics.await_time || 0,
            svctm: data.metrics.svctm || 0,
            util: data.metrics.util || 0,
          };

          iostatMetrics.value.push(metric);

          // 限制指标数量，防止内存溢出
          if (iostatMetrics.value.length > 1000) {
            iostatMetrics.value.shift();
          }

          console.log("处理iostat数据:", metric);
        }
      } catch (error) {
        console.error("处理iostat数据失败:", error);
      }
    };

    // 组件卸载时清理WebSocket连接
    onUnmounted(() => {
      if (socket.value) {
        socket.value.emit("leave_task_room", { task_id: taskId.value });
        socket.value.disconnect();
      }
    });

    // 初始化
    onMounted(() => {
      if (taskId.value) {
        getTaskDetail();
      }
    });

    const router = useRouter();

    // 跳转到性能抖动图表页面
    const navigateToIOJitterChart = () => {
      router.push({ name: "IOJitterChart", params: { id: taskId.value } });
    };

    // 跳转到IOSTAT性能图表页面
    const navigateToIOStatChart = () => {
      router.push({ name: "IOStatChart", params: { id: taskId.value } });
    };

    // 日志过滤方法
    const filterLogs = () => {
      // 过滤逻辑已经在computed属性中实现
      console.log("过滤日志:", logFilter);
    };

    // 清空日志过滤条件
    const clearLogFilter = () => {
      logFilter.level = "";
      logFilter.keyword = "";
    };

    // 格式化日志时间
    const formatLogTime = (timestamp) => {
      if (!timestamp) return "";
      const date = new Date(timestamp);
      return date.toLocaleString();
    };

    // 显示日志上下文
    const showLogContext = (context) => {
      ElMessageBox.alert(JSON.stringify(context, null, 2), "日志上下文", {
        confirmButtonText: "确定",
        type: "info",
      });
    };

    // 组件挂载后初始化图表
    onMounted(() => {
      // 这里的图表初始化代码已经移除，性能抖动图表现在是一个独立的页面
    });

    return {
      taskDetail,
      nodes,
      taskNodes,
      ioTasks,
      logs,
      logFilter,
      filteredLogs,
      activeNames,
      scheduledTime,
      editIpDialogVisible,
      editingNode,
      ioPartitions,
      newPartition,
      addDialogVisible,
      addType,
      selectedNode,
      selectedIOTask,
      selectedIOCase,
      getStatusType,
      getStatusText,
      getPriorityType,
      getPriorityText,
      loadMoreLogs,
      setScheduledTime,
      startEditIp,
      saveEditIp,
      cancelEditIp,
      addPartition,
      removePartition,
      editIOTask,
      deleteIOTask,
      startTask,
      pauseTask,
      deleteTask,
      showAddDialog,
      selectNode,
      selectIOTask,
      selectIOCase,
      deleteSelectedItem,
      editIOTaskDialogVisible,
      editIOTaskDialogTitle,
      editingIOTask,
      currentIOTaskData,
      handleIOTaskSubmit,
      detailedDataDialogVisible,
      detailedData,
      testResults,
      showDetailedDataDialog,
      showResultDetails,
      // 跳转到性能抖动图表
      navigateToIOJitterChart,
      // 跳转到IOSTAT性能图表
      navigateToIOStatChart,
      // 日志相关方法
      filterLogs,
      clearLogFilter,
      formatLogTime,
      showLogContext,
      // iostat指标数据
      iostatMetrics,
      // 解析iostat日志函数
      parseIostatLog,
      // 处理iostat数据函数
      processIostatData,
    };
  },
};
</script>

<style scoped>
.task-detail-container {
  padding: 20px;
}

/* 日志样式 */
.log-item {
  margin-bottom: 10px;
  padding: 10px;
  border-radius: 4px;
  background-color: #f9f9f9;
  border-left: 4px solid #d9d9d9;
}

.log-header {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
  font-size: 12px;
}

.log-time {
  margin-right: 10px;
  color: #999;
}

.log-level {
  margin-right: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: bold;
}

.log-level-debug {
  background-color: #e6f7ff;
  color: #1890ff;
  border-left-color: #1890ff;
}

.log-level-info {
  background-color: #f6ffed;
  color: #52c41a;
  border-left-color: #52c41a;
}

.log-level-warning {
  background-color: #fffbe6;
  color: #faad14;
  border-left-color: #faad14;
}

.log-level-error {
  background-color: #fff2f0;
  color: #f5222d;
  border-left-color: #f5222d;
}

.log-level-critical {
  background-color: #fff1f0;
  color: #cf1322;
  border-left-color: #cf1322;
}

.log-module {
  color: #666;
  font-size: 12px;
}

.log-content {
  margin-top: 5px;
  font-size: 14px;
  line-height: 1.4;
}

.log-context {
  margin-top: 5px;
  font-size: 12px;
}

.no-logs {
  text-align: center;
  color: #999;
  padding: 20px;
}

.log-filter {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-actions {
  display: flex;
  gap: 10px;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}

.task-detail-card {
  margin-bottom: 24px;
}

.task-info {
  margin-top: 10px;
}

.task-logs {
  margin-top: 10px;
}

.log-item {
  margin: 0;
  padding: 5px 0;
  border-bottom: 1px solid #f0f0f0;
}

.log-time {
  color: #909399;
  margin-right: 10px;
}

.log-content {
  color: #303133;
}

/* 性能图表样式 */
.performance-charts {
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 节点信息样式 */
.node-section {
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.node-info {
  margin-bottom: 15px;
}

.node-field {
  margin-bottom: 10px;
}

.node-field .label {
  display: inline-block;
  width: 80px;
  font-weight: bold;
  color: #606266;
}

.node-field .value {
  display: inline-block;
  color: #303133;
}

.node-actions {
  margin-bottom: 20px;
}

.edit-actions {
  display: inline-block;
}

.edit-actions button {
  margin-right: 10px;
}

/* IO分区样式 */
.io-partitions {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.io-partitions h4 {
  margin-bottom: 15px;
  color: #303133;
  font-size: 16px;
}

.add-partition-form {
  margin-top: 10px;
}

/* 选择信息样式 */
.selection-info {
  margin-top: 15px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.io-cases-list {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}
</style>
