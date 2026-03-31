<template>
  <div class="environment-spaces-container">
    <!-- 页面标题和操作按钮 -->
    <div class="page-header">
      <h1 class="page-title">环境空间管理</h1>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 新建环境空间
      </el-button>
    </div>

    <!-- 环境空间列表 -->
    <el-card shadow="hover" class="spaces-card">
      <template #header>
        <div class="card-header">
          <span>环境空间列表</span>
          <el-input
            v-model="searchQuery"
            placeholder="搜索环境空间名称"
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
        :data="paginatedSpaces"
        style="width: 100%"
        border
        stripe
        v-loading="loading"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="环境名称" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="goToDetail(row.id)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column
          prop="description"
          label="描述"
          show-overflow-tooltip
        />
        <el-table-column prop="owner_name" label="所有者" width="120" />
        <el-table-column prop="node_count" label="节点数" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.node_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              @click="goToMonitoring(row.id)"
            >
              <el-icon><Monitor /></el-icon> 监控
            </el-button>
            <el-button size="small" @click="goToDetail(row.id)">
              <el-icon><View /></el-icon> 详情
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteSpace(row)"
              v-if="row.owner_id === currentUserId"
            >
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
          :total="filteredSpaces.length"
        />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        :model="spaceForm"
        :rules="formRules"
        ref="spaceFormRef"
        label-width="120px"
      >
        <el-form-item label="环境空间名称" prop="name">
          <el-input
            v-model="spaceForm.name"
            placeholder="请输入环境空间名称"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="spaceForm.description"
            type="textarea"
            placeholder="请输入环境空间描述"
            :rows="4"
          />
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

<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Search, Monitor, View, Delete } from "@element-plus/icons-vue";
import environmentSpacesApi from "@/api/environmentSpaces";
import { useAuthStore } from "@/store/auth";

const router = useRouter();
const authStore = useAuthStore();

// 数据
const spaces = ref([]);
const loading = ref(false);
const searchQuery = ref("");
const currentPage = ref(1);
const pageSize = ref(10);
const currentUserId = computed(() => authStore.userId);

// 对话框
const dialogVisible = ref(false);
const dialogTitle = ref("新建环境空间");
const editingSpace = ref(null);

// 表单
const spaceFormRef = ref(null);
const spaceForm = reactive({
  name: "",
  description: "",
});

// 表单规则
const formRules = reactive({
  name: [
    { required: true, message: "请输入环境空间名称", trigger: "blur" },
    {
      min: 2,
      max: 100,
      message: "环境空间名称长度在 2 到 100 个字符",
      trigger: "blur",
    },
  ],
});

// 计算属性：过滤后的环境空间列表
const filteredSpaces = computed(() => {
  if (!searchQuery.value) return spaces.value;
  return spaces.value.filter((space) =>
    space.name.toLowerCase().includes(searchQuery.value.toLowerCase()),
  );
});

// 计算属性：分页后的环境空间列表
const paginatedSpaces = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return filteredSpaces.value.slice(start, end);
});

// 方法：加载环境空间列表
const loadSpaces = async () => {
  loading.value = true;
  try {
    const response = await environmentSpacesApi.getEnvironmentSpaces();
    spaces.value = response.data;
  } catch (error) {
    ElMessage.error("加载环境空间列表失败: " + error.message);
  } finally {
    loading.value = false;
  }
};

// 方法：打开创建对话框
const openCreateDialog = () => {
  dialogTitle.value = "新建环境空间";
  editingSpace.value = null;
  resetForm();
  dialogVisible.value = true;
};

// 方法：重置表单
const resetForm = () => {
  if (spaceFormRef.value) {
    spaceFormRef.value.resetFields();
  }
  Object.assign(spaceForm, {
    name: "",
    description: "",
  });
};

// 方法：提交表单
const submitForm = async () => {
  if (!spaceFormRef.value) return;

  try {
    await spaceFormRef.value.validate();

    if (editingSpace.value) {
      // 更新环境空间
      await environmentSpacesApi.updateEnvironmentSpace(
        editingSpace.value.id,
        spaceForm,
      );
      ElMessage.success("环境空间更新成功");
    } else {
      // 创建环境空间
      await environmentSpacesApi.createEnvironmentSpace(spaceForm);
      ElMessage.success("环境空间创建成功");
    }

    dialogVisible.value = false;
    loadSpaces();
  } catch (error) {
    if (error.name !== "Error") {
      return;
    }
    ElMessage.error("操作失败: " + error.message);
  }
};

// 方法：删除环境空间
const deleteSpace = (space) => {
  ElMessageBox.confirm(
    `确定要删除环境空间「${space.name}」吗？此操作不可恢复。`,
    "删除确认",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    },
  )
    .then(async () => {
      try {
        await environmentSpacesApi.deleteEnvironmentSpace(space.id);
        ElMessage.success("环境空间删除成功");
        loadSpaces();
      } catch (error) {
        ElMessage.error("删除环境空间失败: " + error.message);
      }
    })
    .catch(() => {
      // 取消删除
    });
};

// 方法：跳转到详情页
const goToDetail = (spaceId) => {
  router.push(`/environment-spaces/${spaceId}`);
};

// 方法：跳转到监控页
const goToMonitoring = (spaceId) => {
  router.push(`/environment-spaces/${spaceId}/monitoring`);
};

// 分页方法
const handleSizeChange = (size) => {
  pageSize.value = size;
  currentPage.value = 1;
};

const handleCurrentChange = (current) => {
  currentPage.value = current;
};

// 监听搜索查询变化，重置页码
watch(searchQuery, () => {
  currentPage.value = 1;
});

// 初始化加载
onMounted(() => {
  loadSpaces();
});
</script>

<style scoped>
.environment-spaces-container {
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

.spaces-card {
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
</style>
