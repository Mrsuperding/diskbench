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
              <el-table-column label="操作" width="220">
                <template #default="scope">
                  <el-button
                    type="primary"
                    size="small"
                    @click.stop="startEditIp(scope.row)"
                  >
                    编辑IP
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    @click.stop="deleteNode(scope.row)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <div class="selection-info" v-if="selectedNode">
              <p>已选中节点: {{ selectedNode.name }}</p>
            </div>
          </div>
          <div v-else class="no-data">暂无节点信息</div>

          <!-- 添加节点按钮 -->
          <div class="add-button-container">
            <el-button type="primary" icon="Plus" @click="showAddNodeDialog">
              添加现有节点
            </el-button>
            <el-button type="success" icon="Plus" @click="showCreateNodeDialog">
              创建新节点
            </el-button>
          </div>
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

          <!-- 添加IO任务按钮 -->
          <div class="add-button-container">
            <el-button type="primary" icon="Plus" @click="showAddIOCaseDialog">
              添加现有IO用例
            </el-button>
            <el-button type="success" icon="Plus" @click="showCreateIOCaseDialog">
              创建新IO用例
            </el-button>
          </div>
        </el-collapse-item>

        <!-- 任务实时运行状态 -->
        <el-collapse-item title="任务实时运行状态" name="4">
          <div class="task-status-display">
            <!-- 当前运行状态 -->
            <div class="current-status-box">
              <div class="status-header">
                <span class="status-icon">
                  <el-icon v-if="taskDetail.status === 'running'" class="is-loading">
                    <Loading />
                  </el-icon>
                  <el-icon v-else-if="taskDetail.status === 'completed'" color="#67C23A">
                    <CircleCheck />
                  </el-icon>
                  <el-icon v-else-if="taskDetail.status === 'failed'" color="#F56C6C">
                    <CircleClose />
                  </el-icon>
                  <el-icon v-else color="#909399">
                    <Clock />
                  </el-icon>
                </span>
                <span class="status-text">
                  {{ getTaskStatusText() }}
                </span>
              </div>

              <!-- 当前操作 -->
              <div v-if="currentOperation" class="current-operation">
                <div class="operation-label">当前操作：</div>
                <div class="operation-content">{{ currentOperation }}</div>
              </div>

              <!-- 操作历史 -->
              <div class="operation-history">
                <div class="history-label">操作历史：</div>
                <div class="history-list">
                  <div
                    v-for="(op, index) in operationHistory"
                    :key="index"
                    class="history-item"
                    :class="{
                      'is-current': index === operationHistory.length - 1,
                      'is-error': op.level === 'ERROR',
                      'is-warning': op.level === 'WARNING'
                    }"
                  >
                    <div class="history-main">
                      <span class="history-time">{{ formatLogTime(op.timestamp) }}</span>
                      <span class="history-stage" v-if="op.context && op.context.stage">
                        【{{ op.context.stage }}】
                      </span>
                      <span class="history-text">{{ op.message }}</span>
                    </div>
                    <div class="history-details" v-if="op.context">
                      <!-- FIO命令特殊显示 -->
                      <div v-if="op.context.fio_command" class="fio-command-block">
                        <div class="fio-command-label">FIO命令：</div>
                        <pre class="fio-command-code">{{ op.context.fio_command }}</pre>
                      </div>

                      <!-- 其他详细信息 -->
                      <div v-if="!op.context.fio_command" class="detail-items">
                        <span v-if="op.context.nodes && op.context.nodes.length > 0" class="detail-item">
                          节点: {{ op.context.nodes.join(', ') }}
                        </span>
                        <span v-if="op.context.io_models && op.context.io_models.length > 0" class="detail-item">
                          IO模型: {{ op.context.io_models.join(', ') }}
                        </span>
                        <span v-if="op.context.partition" class="detail-item">
                          分区: {{ op.context.partition }}
                        </span>
                        <span v-if="op.context.duration" class="detail-item">
                          耗时: {{ op.context.duration }}秒
                        </span>
                      </div>
                    </div>
                    <el-tag
                      v-if="op.level === 'ERROR'"
                      type="danger"
                      size="small"
                      effect="plain"
                    >
                      失败
                    </el-tag>
                    <el-tag
                      v-else-if="op.level === 'WARNING'"
                      type="warning"
                      size="small"
                      effect="plain"
                    >
                      警告
                    </el-tag>
                  </div>
                  <div v-if="operationHistory.length === 0" class="no-history">
                    暂无操作记录
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- 创建新节点对话框 -->
    <el-dialog
      v-model="createNodeDialogVisible"
      title="创建新节点"
      width="600px"
    >
      <el-form :model="newNodeForm" label-width="120px">
        <el-form-item label="节点名称" required>
          <el-input v-model="newNodeForm.name" placeholder="请输入节点名称" />
        </el-form-item>
        <el-form-item label="IP地址" required>
          <el-input v-model="newNodeForm.ip_address" placeholder="请输入IP地址" />
        </el-form-item>
        <el-form-item label="登录凭证" required>
          <el-select v-model="newNodeForm.login_credential_id" placeholder="请选择登录凭证" style="width: 100%">
            <el-option
              v-for="cred in loginCredentials"
              :key="cred.id"
              :label="cred.alias"
              :value="cred.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="节点描述">
          <el-input
            v-model="newNodeForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入节点描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createNodeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmCreateNode">创建并添加</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 创建新IO用例对话框 -->
    <IOCaseEditor
      v-model="createIOCaseDialogVisible"
      dialog-title="创建新IO用例"
      form-title="IO用例信息"
      :initial-data="{}"
      @submit="handleCreateIOCase"
    />

    <!-- 添加节点对话框 -->
    <el-dialog
      v-model="addNodeDialogVisible"
      title="选择要添加的节点"
      width="700px"
    >
      <el-table
        :data="availableNodes"
        style="width: 100%"
        @selection-change="handleNodeSelectionChange"
      >
        <el-table-column type="selection" width="55" />
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
      </el-table>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addNodeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmAddNodes">
            确定添加 ({{ selectedNodesToAdd.length }})
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 添加IO用例对话框 -->
    <el-dialog
      v-model="addIOCaseDialogVisible"
      title="选择要添加的IO测试用例"
      width="800px"
    >
      <el-table
        :data="availableIOCases"
        style="width: 100%"
        @selection-change="handleIOCaseSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="用例ID" width="80" />
        <el-table-column prop="name" label="用例名称" />
        <el-table-column prop="tool" label="工具" width="100" />
        <el-table-column label="IO类型" width="150">
          <template #default="scope">
            <el-tag v-if="scope.row.parameters && scope.row.parameters.io_type">
              {{ Array.isArray(scope.row.parameters.io_type)
                  ? scope.row.parameters.io_type.join(', ')
                  : scope.row.parameters.io_type }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="块大小" width="100">
          <template #default="scope">
            {{ scope.row.parameters?.block_size || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="队列深度" width="100">
          <template #default="scope">
            {{ scope.row.parameters?.queue_depth || '-' }}
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addIOCaseDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmAddIOCases">
            确定添加 ({{ selectedIOCasesToAdd.length }})
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 旧的增加对话框（保留用于兼容） -->
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
import { Loading, CircleCheck, CircleClose, Clock } from "@element-plus/icons-vue";
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

    // 增加对话框（旧的，保留兼容）
    const addDialogVisible = ref(false);
    const addType = ref(""); // 'node' 或 'io_case'

    // 添加节点对话框
    const addNodeDialogVisible = ref(false);
    const availableNodes = ref([]);
    const selectedNodesToAdd = ref([]);

    // 创建新节点对话框
    const createNodeDialogVisible = ref(false);
    const newNodeForm = ref({
      name: '',
      ip_address: '',
      login_credential_id: null,
      description: ''
    });
    const loginCredentials = ref([]);

    // 添加IO用例对话框
    const addIOCaseDialogVisible = ref(false);
    const availableIOCases = ref([]);
    const selectedIOCasesToAdd = ref([]);

    // 创建新IO用例对话框
    const createIOCaseDialogVisible = ref(false);

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

    // 任务实时状态
    const currentOperation = ref(""); // 当前正在执行的操作
    const operationHistory = ref([]); // 操作历史记录（最多保留20条）

    // 日志数据
    const logs = ref([]);

    // 日志数据 - 直接使用，不需要过滤
    // logs.value 已在上面定义

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

          // 更新当前操作状态
          if (logData.message) {
            currentOperation.value = logData.message;
          }

          // 添加到操作历史
          operationHistory.value.push({
            timestamp: logData.timestamp || new Date().toISOString(),
            message: logData.message,
            level: logData.level || "INFO",
            context: logData.context || {},
          });

          // 限制操作历史数量，避免内存占用过大（保留最近100条）
          if (operationHistory.value.length > 100) {
            operationHistory.value.shift();
          }

          console.log("更新任务状态:", {
            currentOperation: currentOperation.value,
            historyCount: operationHistory.value.length
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

        // 从nodes数组提取node_ids
        if (response.data.nodes && Array.isArray(response.data.nodes)) {
          taskDetail.node_ids = response.data.nodes.map(node => node.id);
        } else if (!taskDetail.node_ids) {
          taskDetail.node_ids = [];
        }

        // 从io_test_cases数组提取io_test_case_ids
        if (response.data.io_test_cases && Array.isArray(response.data.io_test_cases)) {
          taskDetail.io_test_case_ids = response.data.io_test_cases.map(ioCase => ioCase.id);
        } else if (!taskDetail.io_test_case_ids) {
          taskDetail.io_test_case_ids = [];
        }

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

    // 加载操作历史日志
    const loadOperationHistory = async () => {
      try {
        const taskId = route.params.id;
        const response = await fetch(`/api/tasks/${taskId}/operation-logs?limit=100`);
        const result = await response.json();

        if (result.success && result.data) {
          // 将数据库中的历史日志映射为前端格式
          const historyLogs = result.data.map(log => ({
            timestamp: log.timestamp,
            message: log.message,
            level: log.level,
            context: log.context || {}
          }));

          // 如果当前没有操作历史（页面刚加载），直接赋值
          if (operationHistory.value.length === 0) {
            operationHistory.value = historyLogs;
          } else {
            // 如果已有操作历史（WebSocket 已接收到日志），则合并并去重
            // 使用 timestamp + message 作为唯一标识
            const existingKeys = new Set(
              operationHistory.value.map(log => `${log.timestamp}_${log.message}`)
            );

            // 只添加不存在的历史日志
            historyLogs.forEach(log => {
              const key = `${log.timestamp}_${log.message}`;
              if (!existingKeys.has(key)) {
                operationHistory.value.push(log);
                existingKeys.add(key);
              }
            });

            // 按时间戳排序
            operationHistory.value.sort((a, b) => {
              return new Date(a.timestamp) - new Date(b.timestamp);
            });
          }

          // 如果有日志，将最后一条设置为当前操作
          if (operationHistory.value.length > 0) {
            const lastLog = operationHistory.value[operationHistory.value.length - 1];
            currentOperation.value = lastLog.message;
          }

          console.log(`加载了操作历史，总计 ${operationHistory.value.length} 条`);
        }
      } catch (error) {
        console.error("加载操作历史失败:", error);
        // 加载失败不影响页面其他功能
      }
    };

    // 加载相关数据
    const loadRelatedData = async () => {
      try {
        // 加载节点数据 - 从后端返回的nodes列表中获取
        if (
          taskDetail.nodes &&
          Array.isArray(taskDetail.nodes) &&
          taskDetail.nodes.length > 0
        ) {
          // 直接使用后端返回的节点数据
          taskNodes.value = taskDetail.nodes.map((node) => ({
            ...node,
            io_partitions: node.io_partitions || [],
          }));
        } else {
          // 没有节点数据
          taskNodes.value = [];
        }

        // 获取IO任务数据
        try {
          // 直接从任务详情中获取IO测试用例，不再获取所有用例
          let taskIOCases = [];

          if (
            taskDetail &&
            taskDetail.io_test_cases &&
            Array.isArray(taskDetail.io_test_cases) &&
            taskDetail.io_test_cases.length > 0
          ) {
            // 直接使用后端返回的IO测试用例对象（最优方案）
            taskIOCases = taskDetail.io_test_cases;
            console.log("使用taskDetail.io_test_cases:", taskIOCases);
          } else if (
            taskDetail &&
            taskDetail.io_test_case_ids &&
            Array.isArray(taskDetail.io_test_case_ids) &&
            taskDetail.io_test_case_ids.length > 0
          ) {
            // 如果只有ID列表，需要单独获取每个IO用例的详情
            console.log("任务关联的IO测试用例ID:", taskDetail.io_test_case_ids);
            console.warn("后端应该直接返回 io_test_cases 对象数组，而不是只返回ID列表");

            // 这里可以调用单个IO用例的API，而不是获取所有用例
            // 暂时创建简单的占位对象
            taskIOCases = taskDetail.io_test_case_ids.map((id) => ({
              id: id,
              name: `IO测试用例 ${id}`,
              parameters: {},
            }));
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
            // 如果没有找到任何关联的IO测试用例，显示空列表
            console.log("没有找到关联的IO测试用例，显示空列表");
            ioTasks.value = [];
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

    // 显示添加节点对话框
    const showAddNodeDialog = async () => {
      try {
        // 获取所有节点列表
        const response = await nodesApi.getNodes();
        const allNodes = response.data || [];

        // 过滤掉已添加的节点
        const currentNodeIds = taskNodes.value.map(n => n.id);
        availableNodes.value = allNodes.filter(node => !currentNodeIds.includes(node.id));

        addNodeDialogVisible.value = true;
      } catch (error) {
        ElMessage.error("获取节点列表失败: " + error.message);
      }
    };

    // 显示创建新节点对话框
    const showCreateNodeDialog = async () => {
      try {
        // 获取登录凭证列表 - 使用 request 以包含认证
        const response = await fetch('/api/login-credentials', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        const result = await response.json();
        if (result.success) {
          loginCredentials.value = result.data || [];
        } else {
          console.error('获取登录凭证失败:', result.message);
          loginCredentials.value = [];
        }

        // 重置表单
        newNodeForm.value = {
          name: '',
          ip_address: '',
          login_credential_id: null,
          description: ''
        };

        createNodeDialogVisible.value = true;
      } catch (error) {
        console.error('获取登录凭证异常:', error);
        ElMessage.error("获取登录凭证失败: " + error.message);
        // 即使获取失败也打开对话框，允许用户手动输入
        newNodeForm.value = {
          name: '',
          ip_address: '',
          login_credential_id: null,
          description: ''
        };
        createNodeDialogVisible.value = true;
      }
    };

    // 确认创建新节点
    const confirmCreateNode = async () => {
      if (!newNodeForm.value.name || !newNodeForm.value.ip_address || !newNodeForm.value.login_credential_id) {
        ElMessage.warning("请填写完整的节点信息");
        return;
      }

      try {
        // 创建新节点
        const createResponse = await nodesApi.createNode(newNodeForm.value);
        const newNode = createResponse.data;

        // 将新节点添加到任务
        const currentNodeIds = taskNodes.value.map(n => n.id);
        const updatedNodeIds = [...currentNodeIds, newNode.id];

        await tasksApi.updateTask(taskId.value, {
          node_ids: updatedNodeIds
        });

        // 更新本地节点列表
        taskNodes.value.push(newNode);

        ElMessage.success("节点创建并添加成功");
        createNodeDialogVisible.value = false;

        // 刷新任务详情
        await getTaskDetail();
      } catch (error) {
        ElMessage.error("创建节点失败: " + error.message);
      }
    };

    // 显示添加IO用例对话框
    const showAddIOCaseDialog = async () => {
      try {
        // 获取所有IO用例列表
        const response = await ioCasesApi.getIOCases();
        const allIOCases = response.data || [];

        // 过滤掉已添加的IO用例
        const currentIOCaseIds = ioTasks.value.map(t => t.id);
        availableIOCases.value = allIOCases.filter(ioCase => !currentIOCaseIds.includes(ioCase.id));

        addIOCaseDialogVisible.value = true;
      } catch (error) {
        ElMessage.error("获取IO用例列表失败: " + error.message);
      }
    };

    // 显示创建新IO用例对话框
    const showCreateIOCaseDialog = () => {
      createIOCaseDialogVisible.value = true;
    };

    // 处理创建新IO用例
    const handleCreateIOCase = async (ioCaseData) => {
      try {
        // 创建新IO用例
        const createResponse = await ioCasesApi.createIOCase(ioCaseData);
        const newIOCase = createResponse.data;

        // 将新IO用例添加到任务
        const currentIOCaseIds = ioTasks.value.map(t => t.id);
        const updatedIOCaseIds = [...currentIOCaseIds, newIOCase.id];

        await tasksApi.updateTask(taskId.value, {
          io_test_case_ids: updatedIOCaseIds
        });

        // 更新本地IO任务列表
        const newIOTask = {
          id: newIOCase.id,
          name: newIOCase.name,
          type: newIOCase.parameters?.io_type || 'read',
          status: 'pending',
          progress: 0,
          io_cases: [newIOCase]
        };
        ioTasks.value.push(newIOTask);

        ElMessage.success("IO用例创建并添加成功");
        createIOCaseDialogVisible.value = false;

        // 刷新任务详情
        await getTaskDetail();
      } catch (error) {
        ElMessage.error("创建IO用例失败: " + error.message);
      }
    };

    // 处理节点选择变化
    const handleNodeSelectionChange = (selection) => {
      selectedNodesToAdd.value = selection;
    };

    // 处理IO用例选择变化
    const handleIOCaseSelectionChange = (selection) => {
      selectedIOCasesToAdd.value = selection;
    };

    // 确认添加节点
    const confirmAddNodes = async () => {
      if (selectedNodesToAdd.value.length === 0) {
        ElMessage.warning("请至少选择一个节点");
        return;
      }

      try {
        // 获取当前任务的节点ID列表
        const currentNodeIds = taskNodes.value.map(n => n.id);
        const newNodeIds = selectedNodesToAdd.value.map(n => n.id);
        const updatedNodeIds = [...currentNodeIds, ...newNodeIds];

        // 调用API更新任务的节点关联
        await tasksApi.updateTask(taskId.value, {
          node_ids: updatedNodeIds
        });

        // 更新本地节点列表
        taskNodes.value.push(...selectedNodesToAdd.value);

        ElMessage.success(`成功添加 ${selectedNodesToAdd.value.length} 个节点`);
        addNodeDialogVisible.value = false;
        selectedNodesToAdd.value = [];

        // 刷新任务详情
        await getTaskDetail();
      } catch (error) {
        ElMessage.error("添加节点失败: " + error.message);
      }
    };

    // 确认添加IO用例
    const confirmAddIOCases = async () => {
      if (selectedIOCasesToAdd.value.length === 0) {
        ElMessage.warning("请至少选择一个IO用例");
        return;
      }

      try {
        // 获取当前任务的IO用例ID列表
        const currentIOCaseIds = ioTasks.value.map(t => t.id);
        const newIOCaseIds = selectedIOCasesToAdd.value.map(c => c.id);
        const updatedIOCaseIds = [...currentIOCaseIds, ...newIOCaseIds];

        // 调用API更新任务的IO用例关联
        await tasksApi.updateTask(taskId.value, {
          io_test_case_ids: updatedIOCaseIds
        });

        // 更新本地IO任务列表
        const newIOTasks = selectedIOCasesToAdd.value.map(ioCase => ({
          id: ioCase.id,
          name: ioCase.name,
          type: ioCase.parameters?.io_type || 'read',
          status: 'pending',
          progress: 0,
          io_cases: [ioCase]
        }));
        ioTasks.value.push(...newIOTasks);

        ElMessage.success(`成功添加 ${selectedIOCasesToAdd.value.length} 个IO用例`);
        addIOCaseDialogVisible.value = false;
        selectedIOCasesToAdd.value = [];

        // 刷新任务详情
        await getTaskDetail();
      } catch (error) {
        ElMessage.error("添加IO用例失败: " + error.message);
      }
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

      // row.io_cases[0]包含完整的IO用例数据
      if (row.io_cases && row.io_cases.length > 0) {
        const ioCase = row.io_cases[0];
        console.log("使用io_cases[0]作为initialData:", ioCase);
        // 确保数据完整
        currentIOTaskData.value = {
          id: ioCase.id,
          name: ioCase.name || row.name,
          description: ioCase.description || '',
          tool: ioCase.tool || 'fio',
          parameters: ioCase.parameters || {}
        };
      } else {
        // 如果没有io_cases，直接使用row（可能只有ID）
        console.log("直接使用row作为initialData:", row);
        currentIOTaskData.value = {
          id: row.id,
          name: row.name || '',
          description: '',
          tool: 'fio',
          parameters: {}
        };
      }
      console.log("最终的currentIOTaskData:", currentIOTaskData.value);
      editIOTaskDialogVisible.value = true;
    };

    // 删除节点
    const deleteNode = (node) => {
      ElMessageBox.confirm(
        `确定要从任务中移除节点「${node.name}」吗？`,
        "删除确认",
        {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
        }
      )
        .then(async () => {
          try {
            // 从本地节点列表中移除
            const index = taskNodes.value.findIndex((n) => n.id === node.id);
            if (index > -1) {
              taskNodes.value.splice(index, 1);
            }

            // 从任务详情的节点ID列表中移除
            const nodeIds = taskDetail.node_ids || taskNodes.value.map(n => n.id);
            const nodeIndex = nodeIds.findIndex((id) => id === node.id);
            if (nodeIndex > -1) {
              nodeIds.splice(nodeIndex, 1);

              // 调用API更新任务的节点关联
              await tasksApi.updateTask(taskId.value, {
                node_ids: nodeIds,
              });
            }

            ElMessage.success("节点删除成功");
            selectedNode.value = null;

            // 刷新任务详情
            await getTaskDetail();
          } catch (error) {
            ElMessage.error("节点删除失败: " + error.message);
          }
        })
        .catch(() => {
          // 取消删除操作
        });
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
    onMounted(async () => {
      if (taskId.value) {
        await getTaskDetail();
        // 加载操作历史（从数据库加载持久化的日志）
        await loadOperationHistory();
      }
    });

    // 监听路由参数变化，重新加载数据
    watch(
      () => route.params.id,
      async (newId, oldId) => {
        if (newId && newId !== oldId) {
          console.log(`路由参数变化: ${oldId} -> ${newId}`);

          // 清理旧的WebSocket连接
          if (socket.value) {
            socket.value.emit("leave_task_room", { task_id: oldId });
            socket.value.disconnect();
            socket.value = null;
          }

          // 重置所有数据状态
          Object.assign(taskDetail, {
            id: "",
            name: "",
            description: "",
            status: "",
            priority: "",
            execution_mode: "",
            node_ids: [],
            io_test_case_ids: [],
            created_at: "",
            updated_at: "",
            completed_at: "",
            task_space_id: null,
          });

          taskNodes.value = [];
          ioTasks.value = [];
          logs.value = [];
          testResults.value = [];
          detailedData.value = [];
          selectedNode.value = null;
          selectedIOCase.value = null;
          selectedIOTask.value = null;

          // 更新taskId
          taskId.value = newId;

          // 重新加载数据
          await getTaskDetail();
          await loadOperationHistory();
        }
      },
      { immediate: false }
    );

    const router = useRouter();

    // 跳转到性能抖动图表页面
    const navigateToIOJitterChart = () => {
      router.push({ name: "IOJitterChart", params: { id: taskId.value } });
    };

    // 跳转到IOSTAT性能图表页面
    const navigateToIOStatChart = () => {
      router.push({ name: "IOStatChart", params: { id: taskId.value } });
    };

    // 格式化日志时间
    // 获取任务状态文本
    const getTaskStatusText = () => {
      const statusMap = {
        'pending': '等待中',
        'running': '正在运行',
        'completed': '已完成',
        'failed': '执行失败',
        'cancelled': '已取消',
        'paused': '已暂停'
      };
      return statusMap[taskDetail.status] || '未知状态';
    };

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
      currentOperation,
      operationHistory,
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
      // 新增对话框相关
      addNodeDialogVisible,
      availableNodes,
      selectedNodesToAdd,
      createNodeDialogVisible,
      newNodeForm,
      loginCredentials,
      addIOCaseDialogVisible,
      availableIOCases,
      selectedIOCasesToAdd,
      createIOCaseDialogVisible,
      getStatusType,
      getStatusText,
      getTaskStatusText,
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
      // 新增函数
      showAddNodeDialog,
      showCreateNodeDialog,
      confirmCreateNode,
      showAddIOCaseDialog,
      showCreateIOCaseDialog,
      handleCreateIOCase,
      handleNodeSelectionChange,
      handleIOCaseSelectionChange,
      confirmAddNodes,
      confirmAddIOCases,
      deleteNode,
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
      formatLogTime,
      showLogContext,
      // iostat指标数据
      iostatMetrics,
      // 解析iostat日志函数
      parseIostatLog,
      // 处理iostat数据函数
      processIostatData,
      // 图标组件
      Loading,
      CircleCheck,
      CircleClose,
      Clock,
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

/* 任务状态显示样式 */
.task-status-display {
  padding: 15px;
}

.current-status-box {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 20px;
}

.status-header {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e8e8e8;
}

.status-icon {
  margin-right: 12px;
  font-size: 24px;
  display: flex;
  align-items: center;
}

.status-icon .is-loading {
  color: #409eff;
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.status-text {
  font-size: 18px;
  color: #303133;
}

.current-operation {
  margin-bottom: 25px;
  padding: 15px;
  background-color: #ffffff;
  border-radius: 6px;
  border-left: 4px solid #409eff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.operation-label {
  font-weight: 600;
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.operation-content {
  font-size: 16px;
  color: #303133;
  line-height: 1.6;
}

.operation-history {
  margin-top: 20px;
}

.history-label {
  font-weight: 600;
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
}

.history-list {
  max-height: 400px;
  overflow-y: auto;
  padding: 10px;
  background-color: #ffffff;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
}

.history-item {
  padding: 12px;
  margin-bottom: 8px;
  background-color: #fafafa;
  border-radius: 4px;
  border-left: 3px solid #d9d9d9;
  display: flex;
  flex-direction: column;
  font-size: 14px;
  transition: all 0.2s;
}

.history-item.is-error {
  border-left-color: #f56c6c;
  background-color: #fef0f0;
}

.history-item.is-warning {
  border-left-color: #e6a23c;
  background-color: #fdf6ec;
}

.history-item.is-current {
  border-left-color: #409eff;
  background-color: #ecf5ff;
  font-weight: 500;
}

.history-item:hover {
  background-color: #f0f0f0;
  transform: translateX(2px);
}

.history-item:last-child {
  margin-bottom: 0;
}

.history-main {
  display: flex;
  align-items: center;
  width: 100%;
}

.history-time {
  color: #909399;
  margin-right: 12px;
  font-size: 12px;
  white-space: nowrap;
  min-width: 80px;
}

.history-stage {
  color: #409eff;
  font-weight: 600;
  margin-right: 8px;
  font-size: 12px;
}

.history-text {
  flex: 1;
  color: #303133;
  line-height: 1.4;
}

.history-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
  margin-left: 92px;
  font-size: 12px;
  color: #606266;
}

.detail-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-item {
  padding: 2px 8px;
  background-color: #f4f4f5;
  border-radius: 3px;
  white-space: nowrap;
}

.fio-command-block {
  width: 100%;
  margin-top: 8px;
}

.fio-command-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
  font-weight: 600;
}

.fio-command-code {
  background-color: #2d2d2d;
  color: #f8f8f2;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Courier New', Consolas, Monaco, monospace;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  border-left: 3px solid #409eff;
}

.no-history {
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

/* 添加按钮容器样式 */
.add-button-container {
  margin-top: 16px;
  padding: 16px 12px;
  background: linear-gradient(135deg, #f5f7fa 0%, #fafbfc 100%);
  border-radius: 8px;
  text-align: center;
  border: 2px dashed #d9dde3;
  display: flex;
  gap: 12px;
  justify-content: center;
  align-items: center;
  transition: all 0.3s ease;
}

.add-button-container:hover {
  border-color: #409eff;
  background: linear-gradient(135deg, #ecf5ff 0%, #f0f7ff 100%);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.add-button-container .el-button {
  font-weight: 500;
  min-width: 140px;
  transition: all 0.3s ease;
}

.add-button-container .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.no-data {
  padding: 20px;
  text-align: center;
  color: #909399;
  font-size: 14px;
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
