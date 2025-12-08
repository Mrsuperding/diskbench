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
      </div>
    </div>

    <!-- 任务详情卡片 -->
    <el-card class="task-detail-card">
      <!-- 任务基本信息 - 可展开 -->
      <el-collapse v-model="activeNames" accordion>
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
            <el-scrollbar height="400px">
              <pre v-for="log in logs" :key="log.id" class="log-item">
                <span class="log-time">{{ log.timestamp }}</span>
                <span class="log-content">{{ log.content }}</span>
              </pre>
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

        <!-- 性能图表 -->
        <el-collapse-item title="性能图表" name="5">
          <div class="performance-charts">
            <el-card shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>IO性能抖动图表</span>
                  <el-select
                    v-model="selectedIOModels"
                    placeholder="选择IO模型"
                    multiple
                    style="width: 300px"
                  >
                    <el-option
                      v-for="task in ioTasks"
                      :key="task.id"
                      :label="task.name"
                      :value="task.id"
                    ></el-option>
                  </el-select>
                </div>
              </template>
              <div class="chart-container">
                <!-- 性能抖动图表 -->
                <div ref="ioJitterChart" class="performance-chart"></div>
              </div>
            </el-card>
            
            <el-card shadow="hover" style="margin-top: 20px;">
              <template #header>
                <div class="card-header">
                  <span>IOPS性能对比</span>
                </div>
              </template>
              <div class="chart-container">
                <!-- IOPS对比图表 -->
                <div ref="iopsChart" class="performance-chart"></div>
              </div>
            </el-card>
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

    <!-- 编辑IO任务对话框 -->
    <el-dialog
      v-model="editIOTaskDialogVisible"
      :title="editIOTaskDialogTitle"
      width="1200px"
      @close="resetIOTaskForm"
    >
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
      <div class="io-case-edit-container">
        <!-- 左侧：编辑表单 -->
        <div class="edit-section">
          <h3>编辑信息</h3>
          <el-form
            :model="ioTaskForm"
            :rules="ioTaskFormRules"
            ref="ioTaskFormRef"
            label-width="120px"
          >
            <el-form-item label="任务名称" prop="name">
              <el-input
                v-model="ioTaskForm.name"
                placeholder="请输入IO任务名称"
                @input="updateIOTaskPreviewData"
              />
            </el-form-item>
            <el-form-item label="模板选择" prop="template_id">
              <el-select
                v-model="ioTaskForm.template_id"
                placeholder="请选择模板"
                filterable
                clearable
                @change="updateIOTaskPreviewData"
              >
                <el-option
                  v-for="template in templates"
                  :key="template.id"
                  :label="template.name"
                  :value="template.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="块大小(KB)" prop="block_size">
              <el-input
                v-model="ioTaskForm.block_size"
                placeholder="支持多个值，用逗号分隔，例如：4,8,16"
                @input="updateIOTaskPreviewData"
              />
            </el-form-item>
            <el-form-item label="队列深度" prop="queue_depth">
              <el-input
                v-model="ioTaskForm.queue_depth"
                placeholder="支持多个值，用逗号分隔，例如：1,8,16,32"
                @input="updateIOTaskPreviewData"
              />
            </el-form-item>
            <el-form-item label="IO类型" prop="io_type">
              <el-input
                v-model="ioTaskForm.io_type"
                placeholder="支持多个值，用逗号分隔，例如：read,write,randread,randwrite"
                @input="updateIOTaskPreviewData"
              />
            </el-form-item>
            <el-form-item label="读写比例" prop="read_write_ratio">
              <el-input
                v-model="ioTaskForm.read_write_ratio"
                placeholder="例如: 70:30"
                @input="updateIOTaskPreviewData"
              />
            </el-form-item>
            <el-form-item label="运行时间(秒)" prop="runtime">
              <el-input-number
                v-model="ioTaskForm.runtime"
                :min="1"
                placeholder="请输入运行时间"
                @change="updateIOTaskPreviewData"
              />
            </el-form-item>
            <el-form-item label="测试文件大小" prop="size">
              <el-input
                v-model="ioTaskForm.size"
                placeholder="例如: 1G"
                @input="updateIOTaskPreviewData"
              />
            </el-form-item>
            <el-form-item label="分区选择" prop="partitions">
              <el-input
                v-model="ioTaskForm.partitions"
                placeholder="支持多个分区，用逗号分隔，例如：sda1,sda2,sdb1"
                @input="updateIOTaskPreviewData"
              />
            </el-form-item>
            <el-form-item label="描述" prop="description">
              <el-input
                v-model="ioTaskForm.description"
                type="textarea"
                placeholder="请输入IO任务描述"
                :rows="3"
                @input="updateIOTaskPreviewData"
              />
            </el-form-item>
            <el-form-item label="任务状态" prop="status">
              <el-select
                v-model="ioTaskForm.status"
                placeholder="请选择任务状态"
              >
                <el-option label="待执行" value="pending" />
                <el-option label="执行中" value="running" />
                <el-option label="已完成" value="completed" />
                <el-option label="失败" value="failed" />
                <el-option label="已停止" value="stopped" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- 右侧：展示区域 -->
        <div class="view-section">
          <!-- 模型列表 -->
          <h3>模型列表</h3>
          <el-card shadow="hover" class="model-list-card">
            <el-table :data="modelList" style="width: 100%" border stripe>
              <el-table-column prop="queueDepth" label="队列深度" width="100" />
              <el-table-column prop="ioType" label="读写模式" width="120" />
              <el-table-column prop="modelName" label="模型名称" />
            </el-table>
          </el-card>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editIOTaskDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitIOTaskForm">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, computed, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import tasksApi from "../api/tasks";
import nodesApi from "../api/nodes";
import ioCasesApi from "../api/ioCases";
import { useRoute } from "vue-router";
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
  setup() {
    // 路由
    const route = useRoute();
    const taskId = computed(() => route.params.id);

    // 展开面板状态
    const activeNames = ref(["1"]);

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

    // 编辑IO任务对话框
    const editIOTaskDialogVisible = ref(false);
    const editIOTaskDialogTitle = ref("编辑IO任务");
    const editingIOTask = ref(null);

    // 模板列表
    const templates = ref([]);

    // 表单
    const ioTaskFormRef = ref(null);
    const ioTaskForm = reactive({
      name: "",
      template_id: null,
      block_size: "4",
      queue_depth: "16",
      io_type: "randread",
      read_write_ratio: "100:0",
      runtime: 60,
      size: "1G",
      partitions: "",
      description: "",
      status: "pending",
    });

    // 表单规则
    const ioTaskFormRules = reactive({
      name: [
        { required: true, message: "请输入任务名称", trigger: "blur" },
        {
          min: 2,
          max: 50,
          message: "任务名称长度在 2 到 50 个字符",
          trigger: "blur",
        },
      ],
      block_size: [
        { required: true, message: "请输入块大小", trigger: "blur" },
      ],
      queue_depth: [
        { required: true, message: "请输入队列深度", trigger: "blur" },
      ],
      io_type: [{ required: true, message: "请输入IO类型", trigger: "blur" }],
      runtime: [
        { required: true, message: "请输入运行时间", trigger: "blur" },
        {
          type: "number",
          min: 1,
          message: "运行时间必须大于0",
          trigger: "blur",
        },
      ],
    });

    // 预览数据
    const previewIOTask = reactive({});

    // 模型列表
    const modelList = ref([]);

    // 日志数据
    const logs = ref([]);

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
      socket.value = io("http://localhost:5001", {
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
        if (data && typeof data === 'object') {
          if (data.log) {
            // 如果是字符串类型的日志
            const logContent = data.log;
            if (typeof logContent === 'string') {
              // 如果是多条日志，分割后添加
              const logLines = logContent.split("\n");
              logLines.forEach((line) => {
                if (line.trim()) {
                  logs.value.push({
                    id: logId++,
                    timestamp: new Date().toLocaleString(),
                    content: line.trim(),
                  });
                  console.log("添加日志:", line.trim());
                }
              });
            } else if (typeof logContent === 'object') {
              // 如果是对象类型的日志
              logs.value.push({
                id: logId++,
                timestamp: new Date().toLocaleString(),
                content: JSON.stringify(logContent),
              });
            }
          } else {
            // 如果直接是日志内容
            logs.value.push({
              id: logId++,
              timestamp: new Date().toLocaleString(),
              content: JSON.stringify(data),
            });
          }
        } else if (typeof data === 'string') {
          // 如果直接是字符串
          logs.value.push({
            id: logId++,
            timestamp: new Date().toLocaleString(),
            content: data,
          });
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
        detailedData.value = testResults.value.map((result) => {
          const ioTestCase = ioTasks.value.find(
            (task) => task.id === result.io_test_case_id,
          );
          const node = taskNodes.value.find((n) => n.id === result.node_id);

          return {
            id: result.id,
            ioModelName: ioTestCase ? ioTestCase.name : "未知IO模型",
            nodeName: node ? node.name : "未知节点",
            nodeIp: node ? node.ip_address : "未知IP",
            status: result.status,
            createdAt: result.created_at,
            rawResult: result.raw_output,
            parsedResult: result.parsed_results,
          };
        });
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
              ioTasks.value = taskIOCases.map((ioCase) => ({
                id: ioCase.id,
                name: ioCase.name || "未命名IO任务",
                type:
                  ioCase.parameters?.read_write_mode || ioCase.type || "read",
                status: taskDetail.status || "pending",
                progress: taskDetail.progress || 0,
                io_cases: [ioCase],
              }));
            } else {
              // 如果没有找到任何关联的IO测试用例，显示所有IO测试用例
              console.log("没有找到关联的IO测试用例，显示所有IO测试用例");
              ioTasks.value = allIOCases.map((ioCase) => ({
                id: ioCase.id,
                name: ioCase.name || "未命名IO任务",
                type:
                  ioCase.parameters?.read_write_mode || ioCase.type || "read",
                status: taskDetail.status || "pending",
                progress: taskDetail.progress || 0,
                io_cases: [ioCase],
              }));
            }
          } else {
            // 如果任务详情中没有IO测试用例ID列表，显示所有IO测试用例
            console.log("任务详情中没有IO测试用例ID列表，显示所有IO测试用例");
            ioTasks.value = allIOCases.map((ioCase) => ({
              id: ioCase.id,
              name: ioCase.name || "未命名IO任务",
              type: ioCase.parameters?.read_write_mode || ioCase.type || "read",
              status: taskDetail.status || "pending",
              progress: taskDetail.progress || 0,
              io_cases: [ioCase],
            }));
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
        cancelling: "warning"
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
        cancelling: "取消中"
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
      // 加载最新的测试结果
      await loadTestResults();
      detailedDataDialogVisible.value = true;
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

    // 加载模板列表
    const loadTemplates = async () => {
      try {
        const response = await ioCasesApi.getTemplates();
        templates.value = response.data;
      } catch (error) {
        ElMessage.error("加载模板列表失败: " + error.message);
      }
    };

    // 更新IO任务预览数据
    const updateIOTaskPreviewData = () => {
      // 更新预览数据
      Object.assign(previewIOTask, {
        name: ioTaskForm.name,
        description: ioTaskForm.description,
        parameters: {
          template_id: ioTaskForm.template_id,
          block_size: ioTaskForm.block_size,
          queue_depth: ioTaskForm.queue_depth,
          io_type: ioTaskForm.io_type,
          read_write_ratio: ioTaskForm.read_write_ratio,
          runtime: ioTaskForm.runtime,
          size: ioTaskForm.size,
          partitions: ioTaskForm.partitions,
        },
      });

      // 生成模型列表
      generateModelList(previewIOTask);
    };

    // 生成模型列表
    const generateModelList = (taskData) => {
      // 清空现有模型列表
      modelList.value = [];

      // 简单实现，根据IO任务参数生成模型列表
      const ioTypes = (taskData.parameters?.io_type || "randread").split(",");
      const queueDepths = (taskData.parameters?.queue_depth || "16").split(",");

      ioTypes.forEach((ioType) => {
        queueDepths.forEach((queueDepth) => {
          modelList.value.push({
            queueDepth: queueDepth,
            ioType: ioType,
            modelName: `${ioType}_qd${queueDepth}`,
          });
        });
      });
    };

    // 编辑IO任务
    const editIOTask = (row) => {
      editIOTaskDialogTitle.value = "编辑IO任务";
      editingIOTask.value = row;

      // 从parameters中提取字段
      Object.assign(ioTaskForm, {
        name: row.name,
        description: row.description || "",
        template_id: row.parameters?.template_id || null,
        block_size: String(row.parameters?.block_size || "4"),
        queue_depth: String(row.parameters?.queue_depth || "16"),
        io_type: row.parameters?.io_type || "randread",
        read_write_ratio: row.parameters?.read_write_ratio || "100:0",
        runtime: row.parameters?.runtime || 60,
        size: row.parameters?.size || "1G",
        partitions: row.parameters?.partitions || "",
        status: row.status || "pending",
      });

      // 更新预览数据
      updateIOTaskPreviewData();

      // 打开编辑对话框
      editIOTaskDialogVisible.value = true;
    };

    // 重置IO任务表单
    const resetIOTaskForm = () => {
      if (ioTaskFormRef.value) {
        ioTaskFormRef.value.resetFields();
      }
      Object.assign(ioTaskForm, {
        name: "",
        template_id: null,
        block_size: "4",
        queue_depth: "16",
        io_type: "randread",
        read_write_ratio: "100:0",
        runtime: 60,
        size: "1G",
        partitions: "",
        description: "",
        status: "pending",
      });

      // 更新预览数据
      updateIOTaskPreviewData();
    };

    // 提交IO任务表单
    const submitIOTaskForm = async () => {
      if (!ioTaskFormRef.value) return;

      try {
        await ioTaskFormRef.value.validate();

        // 构建parameters JSON对象
        const taskData = {
          name: ioTaskForm.name,
          description: ioTaskForm.description,
          parameters: {
            template_id: ioTaskForm.template_id,
            block_size: ioTaskForm.block_size,
            queue_depth: ioTaskForm.queue_depth,
            io_type: ioTaskForm.io_type,
            read_write_ratio: ioTaskForm.read_write_ratio,
            runtime: ioTaskForm.runtime,
            size: ioTaskForm.size,
            partitions: ioTaskForm.partitions,
          },
          status: ioTaskForm.status,
        };

        // 这里需要调用API更新IO任务
        // await tasksApi.updateIOTask(editingIOTask.value.id, taskData)

        // 暂时使用本地数据更新
        const index = ioTasks.value.findIndex(
          (t) => t.id === editingIOTask.value.id,
        );
        if (index > -1) {
          // 更新本地数据
          ioTasks.value[index] = {
            ...ioTasks.value[index],
            ...taskData,
          };
          ElMessage.success("IO任务更新成功");
          editIOTaskDialogVisible.value = false;
        }
      } catch (error) {
        ElMessage.error("IO任务更新失败: " + error.message);
      }
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
            // 这里需要调用API删除IO任务
            // await tasksApi.deleteIOTask(row.id)
            // 暂时使用本地数据删除
            const index = ioTasks.value.findIndex((t) => t.id === row.id);
            if (index > -1) {
              ioTasks.value.splice(index, 1);
              ElMessage.success("IO任务删除成功");
            }
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
          // 这里需要调用API删除节点
          // await tasksApi.deleteNode(taskId.value, selectedNode.value.id)
          // 暂时使用本地数据删除
          const index = taskNodes.value.findIndex(
            (n) => n.id === selectedNode.value.id,
          );
          if (index > -1) {
            taskNodes.value.splice(index, 1);
            ElMessage.success("节点删除成功");
            selectedNode.value = null;
          }
        } catch (error) {
          ElMessage.error("节点删除失败: " + error.message);
        }
      } else if (selectedIOTask.value) {
        // 删除选中IO任务
        try {
          // 这里需要调用API删除IO任务
          // await tasksApi.deleteIOTask(selectedIOTask.value.id)
          // 暂时使用本地数据删除
          const index = ioTasks.value.findIndex(
            (t) => t.id === selectedIOTask.value.id,
          );
          if (index > -1) {
            ioTasks.value.splice(index, 1);
            ElMessage.success("IO任务删除成功");
            selectedIOTask.value = null;
          }
        } catch (error) {
          ElMessage.error("IO任务删除失败: " + error.message);
        }
      } else if (selectedIOCase.value) {
        // 删除选中IO测试用例
        try {
          // 这里需要调用API删除IO测试用例
          // await tasksApi.deleteIOCase(selectedIOCase.value.id)
          // 暂时使用本地数据删除
          if (selectedIOTask.value && selectedIOTask.value.io_cases) {
            const index = selectedIOTask.value.io_cases.findIndex(
              (c) => c.id === selectedIOCase.value.id,
            );
            if (index > -1) {
              selectedIOTask.value.io_cases.splice(index, 1);
              ElMessage.success("IO测试用例删除成功");
              selectedIOCase.value = null;
            }
          }
        } catch (error) {
          ElMessage.error("IO测试用例删除失败: " + error.message);
        }
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
      // 加载模板列表
      loadTemplates();
    });

    // 性能图表相关
    const selectedIOModels = ref([]);
    const ioJitterChartRef = ref(null);
    const iopsChartRef = ref(null);
    let ioJitterChart = null;
    let iopsChart = null;
    
    // 初始化IO性能抖动图表
    const initIOJitterChart = () => {
      if (ioJitterChartRef.value) {
        ioJitterChart = echarts.init(ioJitterChartRef.value);
        
        const option = {
          title: {
            text: 'IO性能抖动图',
            left: 'center'
          },
          tooltip: {
            trigger: 'axis'
          },
          legend: {
            data: ['读IOPS', '写IOPS', '总IOPS'],
            bottom: 0
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            boundaryGap: false,
            data: [],
            name: '时间'
          },
          yAxis: {
            type: 'value',
            name: 'IOPS'
          },
          series: [
            {
              name: '读IOPS',
              type: 'line',
              data: [],
              smooth: true,
              lineStyle: {
                color: '#5470c6'
              },
              areaStyle: {
                color: {
                  type: 'linear',
                  x: 0,
                  y: 0,
                  x2: 0,
                  y2: 1,
                  colorStops: [{
                    offset: 0, color: 'rgba(84, 112, 198, 0.5)'
                  }, {
                    offset: 1, color: 'rgba(84, 112, 198, 0.1)'
                  }]
                }
              }
            },
            {
              name: '写IOPS',
              type: 'line',
              data: [],
              smooth: true,
              lineStyle: {
                color: '#91cc75'
              },
              areaStyle: {
                color: {
                  type: 'linear',
                  x: 0,
                  y: 0,
                  x2: 0,
                  y2: 1,
                  colorStops: [{
                    offset: 0, color: 'rgba(145, 204, 117, 0.5)'
                  }, {
                    offset: 1, color: 'rgba(145, 204, 117, 0.1)'
                  }]
                }
              }
            },
            {
              name: '总IOPS',
              type: 'line',
              data: [],
              smooth: true,
              lineStyle: {
                color: '#fac858'
              },
              areaStyle: {
                color: {
                  type: 'linear',
                  x: 0,
                  y: 0,
                  x2: 0,
                  y2: 1,
                  colorStops: [{
                    offset: 0, color: 'rgba(250, 200, 88, 0.5)'
                  }, {
                    offset: 1, color: 'rgba(250, 200, 88, 0.1)'
                  }]
                }
              }
            }
          ]
        };
        
        ioJitterChart.setOption(option);
        
        // 监听窗口大小变化，自适应调整图表大小
        window.addEventListener('resize', () => {
          ioJitterChart.resize();
        });
      }
    };
    
    // 初始化IOPS对比图表
    const initIOPSChart = () => {
      if (iopsChartRef.value) {
        iopsChart = echarts.init(iopsChartRef.value);
        
        const option = {
          title: {
            text: 'IOPS性能对比',
            left: 'center'
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow'
            }
          },
          legend: {
            data: ['最大IOPS', '平均IOPS', '最小IOPS'],
            bottom: 0
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: [],
            name: 'IO模型'
          },
          yAxis: {
            type: 'value',
            name: 'IOPS'
          },
          series: [
            {
              name: '最大IOPS',
              type: 'bar',
              data: [],
              itemStyle: {
                color: '#5470c6'
              }
            },
            {
              name: '平均IOPS',
              type: 'bar',
              data: [],
              itemStyle: {
                color: '#91cc75'
              }
            },
            {
              name: '最小IOPS',
              type: 'bar',
              data: [],
              itemStyle: {
                color: '#fac858'
              }
            }
          ]
        };
        
        iopsChart.setOption(option);
        
        // 监听窗口大小变化，自适应调整图表大小
        window.addEventListener('resize', () => {
          iopsChart.resize();
        });
      }
    };
    
    // 更新IO性能抖动图表数据
    const updateIOJitterChart = () => {
      if (ioJitterChart) {
        // 模拟数据，实际应该从后端获取iostat数据
        const timeData = [];
        const readIOPS = [];
        const writeIOPS = [];
        const totalIOPS = [];
        
        // 生成过去60秒的数据
        for (let i = 60; i >= 0; i--) {
          const time = new Date(Date.now() - i * 1000);
          timeData.push(time.toLocaleTimeString());
          
          // 生成随机IOPS数据
          const read = Math.floor(Math.random() * 1000) + 500;
          const write = Math.floor(Math.random() * 800) + 300;
          readIOPS.push(read);
          writeIOPS.push(write);
          totalIOPS.push(read + write);
        }
        
        ioJitterChart.setOption({
          xAxis: {
            data: timeData
          },
          series: [
            {
              data: readIOPS
            },
            {
              data: writeIOPS
            },
            {
              data: totalIOPS
            }
          ]
        });
      }
    };
    
    // 更新IOPS对比图表数据
    const updateIOPSChart = () => {
      if (iopsChart && selectedIOModels.value.length > 0) {
        const ioModelNames = selectedIOModels.value.map(id => {
          const task = ioTasks.value.find(t => t.id === id);
          return task ? task.name : `IO模型${id}`;
        });
        
        const maxIOPS = [];
        const avgIOPS = [];
        const minIOPS = [];
        
        // 为每个选中的IO模型生成随机数据
        selectedIOModels.value.forEach(() => {
          const max = Math.floor(Math.random() * 2000) + 1000;
          const min = Math.floor(Math.random() * 800) + 300;
          const avg = Math.floor((max + min) / 2);
          
          maxIOPS.push(max);
          avgIOPS.push(avg);
          minIOPS.push(min);
        });
        
        iopsChart.setOption({
          xAxis: {
            data: ioModelNames
          },
          series: [
            {
              data: maxIOPS
            },
            {
              data: avgIOPS
            },
            {
              data: minIOPS
            }
          ]
        });
      }
    };
    
    // 监听选中IO模型变化，更新图表
    watch(selectedIOModels, () => {
      updateIOPSChart();
    }, { deep: true });
    
    // 组件挂载后初始化图表
    onMounted(() => {
      initIOJitterChart();
      initIOPSChart();
      // 模拟数据更新
      updateIOJitterChart();
    });

    return {
      taskDetail,
      nodes,
      taskNodes,
      ioTasks,
      logs,
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
      templates,
      ioTaskFormRef,
      ioTaskForm,
      ioTaskFormRules,
      previewIOTask,
      modelList,
      loadTemplates,
      updateIOTaskPreviewData,
      generateModelList,
      resetIOTaskForm,
      submitIOTaskForm,
      detailedDataDialogVisible,
      detailedData,
      testResults,
      selectedIOModels,
      showDetailedDataDialog,
      showResultDetails,
      // 图表相关
      ioJitterChartRef,
      iopsChartRef,
    };
  },
};
</script>

<style scoped>
.task-detail-container {
  padding: 20px;
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