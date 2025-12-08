<template>
  <div class="task-space-detail-container">
    <!-- 页面标题和操作按钮 -->
    <div class="page-header">
      <h1 class="page-title">任务空间详情</h1>
      <el-button type="primary" @click="goBack">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
    </div>

    <!-- 任务空间基本信息 -->
    <el-card shadow="hover" class="space-info-card">
      <template #header>
        <div class="card-header">
          <span>空间基本信息</span>
        </div>
      </template>
      <div class="space-info">
        <h3>{{ taskSpace.name }}</h3>
        <p class="space-description">
          {{ taskSpace.description || "暂无描述" }}
        </p>
        <div class="space-meta">
          <el-tag>所有者: {{ taskSpace.owner_name }}</el-tag>
          <el-tag>{{ taskSpace.is_public ? "公开空间" : "私有空间" }}</el-tag>
          <el-tag>创建于: {{ taskSpace.created_at }}</el-tag>
          <el-tag>任务数量: {{ tasks.length }}</el-tag>
        </div>
      </div>
    </el-card>

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
        <el-table-column prop="id" label="任务ID" width="80" />
        <el-table-column prop="name" label="任务名称" show-overflow-tooltip />
        <el-table-column label="任务类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.type === 'io' ? 'success' : 'warning'">
              {{ row.type === "io" ? "IO任务" : "脚本任务" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="warning" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">
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
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { getTaskSpace } from "@/api/taskSpaces";
import { deleteTask } from "@/api/tasks";
import { ArrowLeft, Search, Edit, Delete } from "@element-plus/icons-vue";

export default {
  name: "TaskSpaceDetail",
  components: {
    ArrowLeft,
    Search,
    Edit,
    Delete,
  },
  setup() {
    const route = useRoute();
    const router = useRouter();
    const taskSpaceId = route.params.id;

    // 数据
    const taskSpace = ref({});
    const tasks = ref([]);
    const loading = ref(false);
    const searchQuery = ref("");

    // 分页
    const currentPage = ref(1);
    const pageSize = ref(10);

    // 过滤后的任务列表
    const filteredTasks = computed(() => {
      if (!searchQuery.value) {
        return tasks.value;
      }
      return tasks.value.filter((task) =>
        task.name.toLowerCase().includes(searchQuery.value.toLowerCase()),
      );
    });

    // 获取任务空间详情
    const fetchTaskSpaceDetail = async () => {
      loading.value = true;
      try {
        const response = await getTaskSpace(taskSpaceId);
        taskSpace.value = response.data;
      } catch (error) {
        ElMessage.error(
          "获取任务空间详情失败: " +
            (error.response?.data?.message || error.message),
        );
      } finally {
        loading.value = false;
      }
    };

    // 获取任务空间下的任务列表
    const fetchTasksBySpaceId = async () => {
      loading.value = true;
      try {
        // 调用API获取特定任务空间下的任务列表
        const response = await getTasks({ task_space_id: taskSpaceId });
        tasks.value = response.data || [];
      } catch (error) {
        ElMessage.error(
          "获取任务列表失败: " +
            (error.response?.data?.message || error.message),
        );
      } finally {
        loading.value = false;
      }
    };

    // 根据状态获取标签类型
    const getStatusType = (status) => {
      const statusMap = {
        pending: "info",
        running: "warning",
        completed: "success",
        failed: "danger",
        paused: "primary",
      };
      return statusMap[status] || "info";
    };

    // 根据状态获取显示文本
    const getStatusText = (status) => {
      const statusMap = {
        pending: "待执行",
        running: "执行中",
        completed: "已完成",
        failed: "失败",
        paused: "已暂停",
      };
      return statusMap[status] || status;
    };

    // 返回上一页
    const goBack = () => {
      router.push("/task-space/manage");
    };

    // 编辑任务
    const handleEdit = (task) => {
      router.push(`/tasks/${task.id}`);
    };

    // 删除任务
    const handleDelete = async (task) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除任务 "${task.name}" 吗？`,
          "删除确认",
          {
            confirmButtonText: "确定",
            cancelButtonText: "取消",
            type: "warning",
          },
        );

        await deleteTask(task.id);
        ElMessage.success("任务删除成功");
        fetchTasksBySpaceId(); // 重新获取任务列表
      } catch (error) {
        if (error !== "cancel") {
          ElMessage.error(
            "任务删除失败: " + (error.response?.data?.message || error.message),
          );
        }
      }
    };

    // 分页处理
    const handleSizeChange = (size) => {
      pageSize.value = size;
    };

    const handleCurrentChange = (current) => {
      currentPage.value = current;
    };

    // 页面加载时获取数据
    onMounted(() => {
      fetchTaskSpaceDetail();
      fetchTasksBySpaceId();
    });

    return {
      taskSpace,
      tasks,
      loading,
      searchQuery,
      currentPage,
      pageSize,
      filteredTasks,
      getStatusType,
      getStatusText,
      goBack,
      handleEdit,
      handleDelete,
      handleSizeChange,
      handleCurrentChange,
    };
  },
};
</script>

<style scoped>
.task-space-detail-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
}

.space-info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.space-info h3 {
  margin: 0 0 10px 0;
  font-size: 20px;
}

.space-description {
  margin: 0 0 15px 0;
  color: #606266;
}

.space-meta {
  margin-top: 10px;
}

.space-meta .el-tag {
  margin-right: 10px;
  margin-bottom: 5px;
}

.tasks-card {
  margin-bottom: 20px;
}

.search-input {
  width: 300px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
