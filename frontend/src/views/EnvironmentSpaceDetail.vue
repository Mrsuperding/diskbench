<template>
  <div class="environment-space-detail-container">
    <!-- 顶部导航栏 -->
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/environment-spaces' }">
          环境空间
        </el-breadcrumb-item>
        <el-breadcrumb-item>{{ environmentSpace?.name || '加载中...' }}</el-breadcrumb-item>
      </el-breadcrumb>
      <div class="header-actions">
        <el-button @click="goBack">
          <el-icon><Back /></el-icon> 返回
        </el-button>
        <el-button type="primary" @click="goToMonitoring">
          <el-icon><Monitor /></el-icon> 查看监控
        </el-button>
      </div>
    </div>

    <!-- 环境空间基本信息 -->
    <el-card shadow="hover" class="info-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>基本信息</span>
          <el-button
            size="small"
            type="primary"
            @click="openEditDialog"
            v-if="canEdit"
          >
            <el-icon><Edit /></el-icon> 编辑
          </el-button>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="环境名称">
          {{ environmentSpace?.name }}
        </el-descriptions-item>
        <el-descriptions-item label="所有者">
          {{ environmentSpace?.owner_name }}
        </el-descriptions-item>
        <el-descriptions-item label="节点数量">
          <el-tag>{{ environmentSpace?.node_count || 0 }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ environmentSpace?.created_at }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ environmentSpace?.description || '无' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 节点列表 -->
    <el-card shadow="hover" class="nodes-card">
      <template #header>
        <div class="card-header">
          <span>节点列表</span>
          <el-button size="small" type="primary" @click="openAddNodesDialog">
            <el-icon><Plus /></el-icon> 添加节点
          </el-button>
        </div>
      </template>
      <el-table
        :data="nodes"
        style="width: 100%"
        border
        stripe
        v-loading="nodesLoading"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="节点名称" show-overflow-tooltip />
        <el-table-column prop="hostname" label="主机名" show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP地址" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="danger"
              @click="removeNode(row)"
              v-if="canEdit"
            >
              <el-icon><Delete /></el-icon> 移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑环境空间"
      width="600px"
      @close="resetEditForm"
    >
      <el-form
        :model="editForm"
        :rules="formRules"
        ref="editFormRef"
        label-width="120px"
      >
        <el-form-item label="环境空间名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入环境空间名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            placeholder="请输入环境空间描述"
            :rows="4"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitEdit">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 添加节点对话框 -->
    <el-dialog
      v-model="addNodesDialogVisible"
      title="添加节点"
      width="800px"
      @close="resetAddNodesForm"
    >
      <el-table
        ref="nodesTableRef"
        :data="availableNodes"
        style="width: 100%"
        @selection-change="handleNodesSelectionChange"
        v-loading="availableNodesLoading"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="节点名称" show-overflow-tooltip />
        <el-table-column prop="hostname" label="主机名" show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP地址" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addNodesDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="submitAddNodes"
            :disabled="selectedNodes.length === 0"
          >
            添加 ({{ selectedNodes.length }})
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Back,
  Monitor,
  Edit,
  Plus,
  Delete,
} from "@element-plus/icons-vue";
import environmentSpacesApi from "@/api/environmentSpaces";
import nodesApi from "@/api/nodes";
import { useAuthStore } from "@/store/auth";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

// 获取环境空间ID
const spaceId = computed(() => parseInt(route.params.id));

// 数据
const environmentSpace = ref(null);
const nodes = ref([]);
const loading = ref(false);
const nodesLoading = ref(false);

// 编辑对话框
const editDialogVisible = ref(false);
const editFormRef = ref(null);
const editForm = reactive({
  name: "",
  description: "",
});

// 添加节点对话框
const addNodesDialogVisible = ref(false);
const availableNodes = ref([]);
const availableNodesLoading = ref(false);
const selectedNodes = ref([]);

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

// 计算属性：是否可以编辑
const canEdit = computed(() => {
  return (
    environmentSpace.value &&
    environmentSpace.value.owner_id === authStore.userId
  );
});

// 方法：加载环境空间详情
const loadEnvironmentSpace = async () => {
  loading.value = true;
  try {
    const response = await environmentSpacesApi.getEnvironmentSpace(
      spaceId.value
    );
    environmentSpace.value = response.data;
  } catch (error) {
    ElMessage.error("加载环境空间详情失败: " + error.message);
  } finally {
    loading.value = false;
  }
};

// 方法:加载节点列表
const loadNodes = async () => {
  nodesLoading.value = true;
  try {
    const response = await environmentSpacesApi.getEnvironmentSpaceNodes(
      spaceId.value
    );
    nodes.value = response.data;
  } catch (error) {
    ElMessage.error("加载节点列表失败: " + error.message);
  } finally {
    nodesLoading.value = false;
  }
};

// 方法：加载可用节点列表
const loadAvailableNodes = async () => {
  availableNodesLoading.value = true;
  try {
    const response = await nodesApi.getNodes();
    // 过滤掉已添加的节点
    const currentNodeIds = nodes.value.map((n) => n.id);
    availableNodes.value = response.data.filter(
      (node) => !currentNodeIds.includes(node.id)
    );
  } catch (error) {
    ElMessage.error("加载可用节点列表失败: " + error.message);
  } finally {
    availableNodesLoading.value = false;
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

// 方法：打开编辑对话框
const openEditDialog = () => {
  if (!environmentSpace.value) return;
  editForm.name = environmentSpace.value.name;
  editForm.description = environmentSpace.value.description || "";
  editDialogVisible.value = true;
};

// 方法：重置编辑表单
const resetEditForm = () => {
  if (editFormRef.value) {
    editFormRef.value.resetFields();
  }
};

// 方法：提交编辑
const submitEdit = async () => {
  if (!editFormRef.value) return;

  try {
    await editFormRef.value.validate();
    await environmentSpacesApi.updateEnvironmentSpace(spaceId.value, editForm);
    ElMessage.success("环境空间更新成功");
    editDialogVisible.value = false;
    loadEnvironmentSpace();
  } catch (error) {
    if (error.name !== "Error") {
      return;
    }
    ElMessage.error("更新失败: " + error.message);
  }
};

// 方法：打开添加节点对话框
const openAddNodesDialog = () => {
  loadAvailableNodes();
  addNodesDialogVisible.value = true;
};

// 方法：重置添加节点表单
const resetAddNodesForm = () => {
  selectedNodes.value = [];
};

// 方法：处理节点选择变化
const handleNodesSelectionChange = (selection) => {
  selectedNodes.value = selection;
};

// 方法：提交添加节点
const submitAddNodes = async () => {
  if (selectedNodes.value.length === 0) {
    ElMessage.warning("请选择要添加的节点");
    return;
  }

  try {
    const nodeIds = selectedNodes.value.map((node) => node.id);
    await environmentSpacesApi.addNodesToSpace(spaceId.value, nodeIds);
    ElMessage.success(`成功添加 ${nodeIds.length} 个节点`);
    addNodesDialogVisible.value = false;
    loadNodes();
    loadEnvironmentSpace();
  } catch (error) {
    ElMessage.error("添加节点失败: " + error.message);
  }
};

// 方法：移除节点
const removeNode = (node) => {
  ElMessageBox.confirm(
    `确定要从环境空间中移除节点「${node.name}」吗？`,
    "移除确认",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    }
  )
    .then(async () => {
      try {
        await environmentSpacesApi.removeNodeFromSpace(spaceId.value, node.id);
        ElMessage.success("节点移除成功");
        loadNodes();
        loadEnvironmentSpace();
      } catch (error) {
        ElMessage.error("移除节点失败: " + error.message);
      }
    })
    .catch(() => {
      // 取消移除
    });
};

// 方法：返回
const goBack = () => {
  router.back();
};

// 方法：跳转到监控页
const goToMonitoring = () => {
  router.push(`/environment-spaces/${spaceId.value}/monitoring`);
};

// 初始化加载
onMounted(() => {
  loadEnvironmentSpace();
  loadNodes();
});
</script>

<style scoped>
.environment-space-detail-container {
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

.info-card,
.nodes-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
