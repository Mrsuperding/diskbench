<template>
  <div class="tasks-container">
    <!-- 页面标题和操作按钮 -->
    <div class="page-header">
      <h1 class="page-title">任务管理</h1>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 新建任务
      </el-button>
    </div>

    <!-- 任务列表 -->
    <el-card shadow="hover" class="tasks-card">
      <template #header>
        <div class="card-header">
          <span>任务列表</span>
          <el-input
            v-model="searchQuery"
            placeholder="搜索任务名称"
            clearable
            size="small"
            class="search-input"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>

      <el-table
        :data="filteredTasks"
        style="width: 100%"
        border
        stripe
        v-loading="loading"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="任务名称" show-overflow-tooltip>
          <template #default="{ row }">
            <a class="task-name-link" @click="goToTaskDetail(row)">{{
              row.name
            }}</a>
          </template>
        </el-table-column>
        <el-table-column
          prop="description"
          label="描述"
          show-overflow-tooltip
        />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)">
              {{ getPriorityText(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="200">
          <template #default="{ row }">
            <el-progress
              :percentage="row.progress || 0"
              :status="getStatusType(row.status)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        <el-table-column label="所属空间" width="150">
          <template #default="{ row }">
            <el-tag size="small" v-if="row.task_space_id">
              {{ getTaskSpaceName(row.task_space_id) }}
            </el-tag>
            <span v-else>未分配</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openEditDialog(row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button
              size="small"
              type="success"
              @click="executeTask(row)"
              :disabled="row.status === 'completed'"
            >
              <el-icon><PlayArrow /></el-icon> 执行
            </el-button>
            <el-button
              size="small"
              type="warning"
              @click="pauseTask(row)"
              :disabled="row.status !== 'running'"
            >
              <el-icon><Pause /></el-icon> 暂停
            </el-button>
            <el-button size="small" type="primary" @click="cloneTask(row)">
              <el-icon><CopyDocument /></el-icon> 克隆
            </el-button>
            <el-button size="small" type="danger" @click="deleteTask(row)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="tasks.length"
        />
      </div>
    </el-card>

    <!-- 创建/编辑任务对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        :model="taskForm"
        :rules="formRules"
        ref="taskFormRef"
        label-width="100px"
      >
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="taskForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="taskForm.description"
            type="textarea"
            placeholder="请输入任务描述"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="节点" prop="node_ids">
          <el-select
            v-model="taskForm.node_ids"
            filterable
            placeholder="请输入关键字搜索节点"
            multiple
          >
            <el-option
              v-for="node in nodes"
              :key="node.id"
              :label="node.name"
              :value="node.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="测试用例" prop="io_test_case_ids">
          <el-select
            v-model="taskForm.io_test_case_ids"
            filterable
            placeholder="请输入关键字搜索测试用例"
            multiple
          >
            <el-option
              v-for="ioCase in ioCases"
              :key="ioCase.id"
              :label="ioCase.name"
              :value="ioCase.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="任务空间" prop="task_space_id">
          <el-select
            v-model="taskForm.task_space_id"
            filterable
            placeholder="请选择任务空间（非必选）"
          >
            <el-option
              v-for="space in taskSpaces"
              :key="space.id"
              :label="space.name"
              :value="space.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="taskForm.status" placeholder="请选择任务状态">
            <el-option label="待执行" value="pending" />
            <el-option label="运行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
            <el-option label="已停止" value="stopped" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="taskForm.priority" placeholder="请选择任务优先级">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Plus,
  Search,
  Edit,
  Delete,
  PlayArrow,
  Pause,
} from "@element-plus/icons-vue";
import tasksApi from "../api/tasks";
import nodesApi from "../api/nodes";
import ioCasesApi from "../api/ioCases";
import { getTaskSpaces } from "../api/taskSpaces";
import { useRouter, useRoute } from "vue-router";

export default {
  name: "Tasks",
  components: {
    Plus,
    Search,
    Edit,
    Delete,
    PlayArrow,
    Pause,
  },
  setup() {
    // 路由
    const router = useRouter();
    const route = useRoute();

    // 数据
    const tasks = ref([]);
    const nodes = ref([]);
    const ioCases = ref([]);
    const taskSpaces = ref([]);
    const loading = ref(false);
    const searchQuery = ref("");
    const currentPage = ref(1);
    const pageSize = ref(10);

    // 对话框
    const dialogVisible = ref(false);
    const dialogTitle = ref("新建任务");
    const editingTask = ref(null);

    // 表单
    const taskFormRef = ref(null);
    const taskForm = reactive({
      name: "",
      description: "",
      node_ids: [],
      io_test_case_ids: [],
      task_space_id: "",
      status: "pending",
      priority: "medium",
    });

    // 表单规则
    const formRules = reactive({
      name: [
        { required: true, message: "请输入任务名称", trigger: "blur" },
        {
          min: 2,
          max: 50,
          message: "任务名称长度在 2 到 50 个字符",
          trigger: "blur",
        },
      ],
      node_ids: [
        { required: false, message: "请选择至少一个节点", trigger: "change" },
        { type: "array", message: "节点必须是数组格式", trigger: "change" },
      ],
      io_test_case_ids: [
        {
          required: true,
          message: "请选择至少一个测试用例",
          trigger: "change",
        },
      ],
      task_space_id: [
        { required: false, message: "请选择任务空间", trigger: "change" },
      ],
      status: [
        { required: true, message: "请选择任务状态", trigger: "change" },
      ],
      priority: [
        { required: true, message: "请选择任务优先级", trigger: "change" },
      ],
    });

    // 计算属性：过滤后的任务列表
    const filteredTasks = computed(() => {
      let filtered = tasks.value;

      // 根据当前路由过滤任务类型
      const taskType = getCurrentTaskType();
      if (taskType === "io") {
        // 过滤出IO任务
        filtered = filtered.filter((task) => task.type === "io" || !task.type); // 如果没有type字段，默认为IO任务
      } else if (taskType === "script") {
        // 过滤出脚本任务
        filtered = filtered.filter((task) => task.type === "script");
      }

      // 根据搜索查询过滤
      if (searchQuery.value) {
        filtered = filtered.filter((task) =>
          task.name.toLowerCase().includes(searchQuery.value.toLowerCase()),
        );
      }

      return filtered;
    });

    // 方法：加载任务列表
    const loadTasks = async () => {
      loading.value = true;
      try {
        const response = await tasksApi.getTasks();
        // 存储所有任务
        tasks.value = response.data;
      } catch (error) {
        ElMessage.error("加载任务列表失败: " + error.message);
      } finally {
        loading.value = false;
      }
    };

    // 方法：克隆任务
    const cloneTask = async (task) => {
      try {
        await tasksApi.cloneTask(task.id);
        ElMessage.success("任务克隆成功");
        loadTasks(); // 重新加载任务列表
      } catch (error) {
        ElMessage.error("克隆任务失败: " + error.message);
      }
    };

    // 根据路由获取当前任务类型
    const getCurrentTaskType = () => {
      if (route.path === "/tasks/io-task-management") {
        return "io";
      } else if (route.path === "/tasks/script-task-management") {
        return "script";
      }
      return "all";
    };

    // 监听路由变化，重新加载任务
    watch(
      () => route.path,
      (newPath) => {
        loadTasks();
      },
    );

    // 方法：加载节点列表
    const loadNodes = async () => {
      try {
        const response = await nodesApi.getNodes();
        nodes.value = response.data;
      } catch (error) {
        ElMessage.error("加载节点列表失败: " + error.message);
      }
    };

    // 方法：加载测试用例列表
    const loadIOCases = async () => {
      try {
        const response = await ioCasesApi.getIOCases();
        ioCases.value = response.data;
      } catch (error) {
        ElMessage.error("加载测试用例列表失败: " + error.message);
      }
    };

    // 方法：加载任务空间列表
    const loadTaskSpaces = async () => {
      try {
        const response = await getTaskSpaces();
        taskSpaces.value = response.data.items || response.data;
      } catch (error) {
        ElMessage.error("加载任务空间列表失败: " + error.message);
      }
    };

    // 方法：打开创建对话框
    const openCreateDialog = () => {
      dialogTitle.value = "新建任务";
      editingTask.value = null;
      resetForm();
      dialogVisible.value = true;
    };

    // 方法：打开编辑对话框
    const openEditDialog = (task) => {
      dialogTitle.value = "编辑任务";
      editingTask.value = task;
      // 将单个io_test_case_id转换为数组形式
      const taskData = { ...task };
      // 处理节点数据 - 确保是数组格式
      if (taskData.node_id && !Array.isArray(taskData.node_id)) {
        taskData.node_ids = [taskData.node_id];
        delete taskData.node_id;
      } else if (!taskData.node_ids) {
        taskData.node_ids = taskData.nodes
          ? taskData.nodes.map((node) => node.id)
          : [];
      }

      // 处理测试用例数据 - 确保是数组格式
      if (
        taskData.io_test_case_id &&
        !Array.isArray(taskData.io_test_case_id)
      ) {
        taskData.io_test_case_ids = [taskData.io_test_case_id];
        delete taskData.io_test_case_id;
      }
      Object.assign(taskForm, taskData);
      dialogVisible.value = true;
    };

    // 方法：重置表单
    const resetForm = () => {
      if (taskFormRef.value) {
        taskFormRef.value.resetFields();
      }
      Object.assign(taskForm, {
        name: "",
        description: "",
        node_ids: [],
        io_test_case_ids: [],
        task_space_id: "",
        status: "pending",
        priority: "medium",
      });
    };

    // 方法：提交表单
    const submitForm = async () => {
      if (!taskFormRef.value) return;

      try {
        await taskFormRef.value.validate();

        // 准备提交数据
        const taskData = { ...taskForm };

        if (editingTask.value) {
          // 更新任务
          await tasksApi.updateTask(editingTask.value.id, taskData);
          ElMessage.success("任务更新成功");
        } else {
          // 创建任务
          await tasksApi.createTask(taskData);
          ElMessage.success("任务创建成功");
        }

        dialogVisible.value = false;
        loadTasks(); // 重新加载任务列表
      } catch (error) {
        if (error.name !== "Error") {
          // 表单验证错误
          return;
        }
        ElMessage.error("操作失败: " + error.message);
      }
    };

    // 方法：删除任务
    const deleteTask = (task) => {
      ElMessageBox.confirm(
        `确定要删除任务「${task.name}」吗？此操作不可恢复。`,
        "删除确认",
        {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
        },
      )
        .then(async () => {
          try {
            await tasksApi.deleteTask(task.id);
            ElMessage.success("任务删除成功");
            loadTasks(); // 重新加载任务列表
          } catch (error) {
            ElMessage.error("删除任务失败: " + error.message);
          }
        })
        .catch(() => {
          // 取消删除
        });
    };

    // 方法：执行任务
    const executeTask = async (task) => {
      try {
        await tasksApi.executeTask(task.id);
        ElMessage.success("任务执行成功");
        loadTasks(); // 重新加载任务列表
      } catch (error) {
        ElMessage.error("执行任务失败: " + error.message);
      }
    };

    // 方法：暂停任务
    const pauseTask = async (task) => {
      try {
        await tasksApi.pauseTask(task.id);
        ElMessage.success("任务暂停成功");
        loadTasks(); // 重新加载任务列表
      } catch (error) {
        ElMessage.error("暂停任务失败: " + error.message);
      }
    };

    // 方法：跳转到任务详情页面
    const goToTaskDetail = (task) => {
      router.push(`/tasks/${task.id}`);
    };

    // 方法：获取状态类型
    const getStatusType = (status) => {
      const types = {
        running: "primary",
        completed: "success",
        failed: "danger",
        stopped: "info",
        pending: "warning",
        cancelled: "danger",
        cancelling: "warning",
      };
      return types[status] || "info";
    };

    // 方法：获取状态文本
    const getStatusText = (status) => {
      const texts = {
        running: "运行中",
        completed: "已完成",
        failed: "失败",
        stopped: "已停止",
        pending: "待执行",
        cancelled: "已取消",
        cancelling: "取消中",
      };
      return texts[status] || status;
    };

    // 方法：获取优先级类型
    const getPriorityType = (priority) => {
      const types = {
        high: "danger",
        medium: "warning",
        low: "success",
      };
      return types[priority] || "info";
    };

    // 方法：获取优先级文本
    const getPriorityText = (priority) => {
      const texts = {
        high: "高",
        medium: "中",
        low: "低",
      };
      return texts[priority] || priority;
    };

    // 根据ID获取任务空间名称
    const getTaskSpaceName = (taskSpaceId) => {
      const space = taskSpaces.value.find((space) => space.id === taskSpaceId);
      return space ? space.name : "未知空间";
    };

    // 分页方法
    const handleSizeChange = (size) => {
      pageSize.value = size;
      currentPage.value = 1;
    };

    const handleCurrentChange = (current) => {
      currentPage.value = current;
    };

    // 初始化加载数据
    onMounted(() => {
      loadTasks();
      loadNodes();
      loadIOCases();
      loadTaskSpaces();
    });

    return {
      tasks,
      nodes,
      ioCases,
      taskSpaces,
      loading,
      searchQuery,
      currentPage,
      pageSize,
      filteredTasks,
      dialogVisible,
      dialogTitle,
      taskFormRef,
      taskForm,
      formRules,
      loadTasks,
      loadNodes,
      loadIOCases,
      loadTaskSpaces,
      openCreateDialog,
      openEditDialog,
      resetForm,
      submitForm,
      deleteTask,
      executeTask,
      pauseTask,
      cloneTask,
      goToTaskDetail,
      getStatusType,
      getStatusText,
      getPriorityType,
      getPriorityText,
      getTaskSpaceName,
      handleSizeChange,
      handleCurrentChange,
    };
  },
};
</script>

<style scoped>
.tasks-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}

.tasks-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-input {
  width: 280px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 任务名称链接样式 */
.task-name-link {
  color: #409eff;
  cursor: pointer;
  text-decoration: none;
}

.task-name-link:hover {
  text-decoration: underline;
}
</style>
