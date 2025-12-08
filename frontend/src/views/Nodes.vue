<template>
  <div class="nodes-container">
    <!-- 页面标题和操作按钮 -->
    <div class="page-header">
      <h1 class="page-title">节点管理</h1>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 新建节点
      </el-button>
    </div>

    <!-- 节点列表 -->
    <el-card shadow="hover" class="nodes-card">
      <template #header>
        <div class="card-header">
          <span>节点列表</span>
          <el-input
            v-model="searchQuery"
            placeholder="搜索节点名称"
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
        :data="filteredNodes"
        style="width: 100%"
        border
        stripe
        v-loading="loading"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="节点名称" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="openDetailDialog(row)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column
          prop="ip_address"
          label="主机地址"
          show-overflow-tooltip
        />

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="节点类型" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="deleteNode(row)">
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
          :total="nodes.length"
        />
      </div>
    </el-card>

    <!-- 创建节点对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        :model="nodeForm"
        :rules="formRules"
        ref="nodeFormRef"
        label-width="100px"
      >
        <el-form-item label="节点名称" prop="name">
          <el-input v-model="nodeForm.name" placeholder="请输入节点名称" />
        </el-form-item>
        <el-form-item label="主机地址" prop="ip_address">
          <el-input
            v-model="nodeForm.ip_address"
            placeholder="请输入主机地址（如：192.168.1.100）"
          />
        </el-form-item>
        <el-form-item label="登录凭证" prop="login_credential_id">
          <el-select
            v-model="nodeForm.login_credential_id"
            placeholder="请选择登录凭证"
            filterable
            :filter-value="credentialSearchQuery"
            @filter-change="credentialSearchQuery = $event"
          >
            <el-option
              v-for="credential in filteredLoginCredentials"
              :key="credential.id"
              :label="credential.alias"
              :value="credential.id"
            >
              <div>{{ credential.alias }}</div>
              <div class="text-xs text-gray-500">
                {{ credential.host }}:{{ credential.port }}
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="节点类型" prop="type">
          <el-select v-model="nodeForm.type" placeholder="请选择节点类型">
            <el-option label="主节点" value="master" />
            <el-option label="工作节点" value="worker" />
          </el-select>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="nodeForm.description"
            type="textarea"
            placeholder="请输入节点描述"
            :rows="3"
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

    <!-- 节点详情/编辑对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="节点详情"
      width="800px"
      @close="resetDetailForm"
    >
      <!-- 对话框头部操作按钮 -->
      <template #header>
        <div
          style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
          "
        >
          <span>节点详情</span>
          <div>
            <el-button size="small" @click="detailDialogVisible = false">
              <el-icon><ArrowLeft /></el-icon> 返回
            </el-button>
            <el-button size="small" type="primary" @click="saveNodeDetail">
              <el-icon><Check /></el-icon> 保存
            </el-button>
          </div>
        </div>
      </template>

      <el-form
        :model="detailNodeForm"
        :rules="formRules"
        ref="detailNodeFormRef"
        label-width="120px"
      >
        <el-form-item label="节点名称" prop="name">
          <el-input
            v-model="detailNodeForm.name"
            placeholder="请输入节点名称"
          />
        </el-form-item>
        <el-form-item label="主机地址" prop="ip_address">
          <el-input
            v-model="detailNodeForm.ip_address"
            placeholder="请输入主机地址（如：192.168.1.100）"
          />
        </el-form-item>
        <el-form-item label="登录凭证" prop="login_credential_id">
          <el-select
            v-model="detailNodeForm.login_credential_id"
            placeholder="请选择登录凭证"
            filterable
            :filter-value="detailCredentialSearchQuery"
            @filter-change="detailCredentialSearchQuery = $event"
          >
            <el-option
              v-for="credential in filteredLoginCredentials"
              :key="credential.id"
              :label="credential.alias"
              :value="credential.id"
            >
              <div>{{ credential.alias }}</div>
              <div class="text-xs text-gray-500">
                {{ credential.host }}:{{ credential.port }}
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="节点类型" prop="type">
          <el-select v-model="detailNodeForm.type" placeholder="请选择节点类型">
            <el-option label="主节点" value="master" />
            <el-option label="工作节点" value="worker" />
          </el-select>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="detailNodeForm.description"
            type="textarea"
            placeholder="请输入节点描述"
            :rows="4"
          />
        </el-form-item>
        <el-form-item label="创建时间" prop="created_at">
          <el-input
            v-model="detailNodeForm.created_at"
            disabled
            placeholder="自动生成"
          />
        </el-form-item>
        <el-form-item label="更新时间" prop="updated_at">
          <el-input
            v-model="detailNodeForm.updated_at"
            disabled
            placeholder="自动更新"
          />
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Plus,
  Search,
  Delete,
  ArrowLeft,
  Check,
} from "@element-plus/icons-vue";
import nodesApi from "../api/nodes";
import loginCredentialsApi from "../api/loginCredentials";

export default {
  name: "Nodes",
  components: {
    Plus,
    Search,
    Delete,
    ArrowLeft,
    Check,
  },
  setup() {
    // 数据
    const nodes = ref([]);
    const loading = ref(false);
    const searchQuery = ref("");
    const currentPage = ref(1);
    const pageSize = ref(10);

    // 对话框
    const dialogVisible = ref(false);
    const dialogTitle = ref("新建节点");
    const editingNode = ref(null);

    // 节点详情对话框
    const detailDialogVisible = ref(false);
    const detailEditingNode = ref(null);

    // 登录凭证
    const loginCredentials = ref([]);
    const credentialSearchQuery = ref("");
    const detailCredentialSearchQuery = ref("");

    // 表单
    const nodeFormRef = ref(null);
    const nodeForm = reactive({
      name: "",
      ip_address: "",
      login_credential_id: "",
      type: "worker",
      description: "",
    });

    // 节点详情表单
    const detailNodeFormRef = ref(null);
    const detailNodeForm = reactive({
      name: "",
      ip_address: "",
      login_credential_id: "",
      type: "worker",
      description: "",
      created_at: "",
      updated_at: "",
    });

    // 表单规则
    const formRules = reactive({
      name: [
        { required: true, message: "请输入节点名称", trigger: "blur" },
        {
          min: 2,
          max: 50,
          message: "节点名称长度在 2 到 50 个字符",
          trigger: "blur",
        },
      ],
      ip_address: [
        { required: true, message: "请输入主机地址", trigger: "blur" },
        {
          pattern:
            /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
          message: "请输入有效的IP地址",
          trigger: "blur",
        },
      ],
      login_credential_id: [
        { required: false, message: "请选择登录凭证", trigger: "change" },
      ],
      type: [{ required: true, message: "请选择节点类型", trigger: "change" }],
    });

    // 计算属性：过滤后的节点列表
    const filteredNodes = computed(() => {
      if (!searchQuery.value) return nodes.value;
      return nodes.value.filter((node) =>
        node.name.toLowerCase().includes(searchQuery.value.toLowerCase()),
      );
    });

    // 计算属性：过滤后的登录凭证列表
    const filteredLoginCredentials = computed(() => {
      if (!credentialSearchQuery.value) return loginCredentials.value;
      const searchValue = credentialSearchQuery.value.toLowerCase();
      return loginCredentials.value.filter(
        (credential) =>
          credential.alias.toLowerCase().includes(searchValue) ||
          credential.host.toLowerCase().includes(searchValue) ||
          credential.username.toLowerCase().includes(searchValue),
      );
    });

    // 方法：加载节点列表
    const loadNodes = async () => {
      loading.value = true;
      try {
        const response = await nodesApi.getNodes();
        nodes.value = response.data;
      } catch (error) {
        ElMessage.error("加载节点列表失败: " + error.message);
      } finally {
        loading.value = false;
      }
    };

    // 方法：打开创建对话框
    const openCreateDialog = () => {
      dialogTitle.value = "新建节点";
      editingNode.value = null;
      resetForm();
      dialogVisible.value = true;
    };

    // 方法：打开编辑对话框
    const openEditDialog = (node) => {
      dialogTitle.value = "编辑节点";
      editingNode.value = node;
      Object.assign(nodeForm, node);
      dialogVisible.value = true;
    };

    // 方法：重置表单
    const resetForm = () => {
      if (nodeFormRef.value) {
        nodeFormRef.value.resetFields();
      }
      Object.assign(nodeForm, {
        name: "",
        ip_address: "",
        type: "worker",
        description: "",
      });
    };

    // 方法：获取登录凭证
    const getLoginCredentials = async () => {
      try {
        const response = await loginCredentialsApi.getLoginCredentials();
        loginCredentials.value = response.data;
      } catch (error) {
        ElMessage.error("获取登录凭证失败: " + error.message);
      }
    };

    // 方法：提交表单
    const submitForm = async () => {
      if (!nodeFormRef.value) return;

      try {
        await nodeFormRef.value.validate();

        if (editingNode.value) {
          // 更新节点
          await nodesApi.updateNode(editingNode.value.id, nodeForm);
          ElMessage.success("节点更新成功");
        } else {
          // 创建节点
          await nodesApi.createNode(nodeForm);
          ElMessage.success("节点创建成功");
        }

        dialogVisible.value = false;
        loadNodes(); // 重新加载节点列表
      } catch (error) {
        if (error.name !== "Error") {
          // 表单验证错误
          return;
        }
        ElMessage.error("操作失败: " + error.message);
      }
    };

    // 方法：打开节点详情对话框
    const openDetailDialog = (node) => {
      detailEditingNode.value = node;
      Object.assign(detailNodeForm, node);
      detailDialogVisible.value = true;
    };

    // 方法：保存节点详情
    const saveNodeDetail = async () => {
      if (!detailNodeFormRef.value) return;

      try {
        await detailNodeFormRef.value.validate();

        if (detailEditingNode.value) {
          // 更新节点
          await nodesApi.updateNode(detailEditingNode.value.id, detailNodeForm);
          ElMessage.success("节点更新成功");
          detailDialogVisible.value = false;
          loadNodes(); // 重新加载节点列表
        }
      } catch (error) {
        if (error.name !== "Error") {
          // 表单验证错误
          return;
        }
        ElMessage.error("操作失败: " + error.message);
      }
    };

    // 方法：重置详情表单
    const resetDetailForm = () => {
      if (detailNodeFormRef.value) {
        detailNodeFormRef.value.resetFields();
      }
      detailEditingNode.value = null;
    };

    // 方法：删除节点
    const deleteNode = (node) => {
      ElMessageBox.confirm(
        `确定要删除节点「${node.name}」吗？此操作不可恢复。`,
        "删除确认",
        {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
        },
      )
        .then(async () => {
          try {
            await nodesApi.deleteNode(node.id);
            ElMessage.success("节点删除成功");
            loadNodes(); // 重新加载节点列表
          } catch (error) {
            ElMessage.error("删除节点失败: " + error.message);
          }
        })
        .catch(() => {
          // 取消删除
        });
    };

    // 方法：获取状态类型
    const getStatusType = (status) => {
      const types = {
        active: "success",
        inactive: "danger",
        maintenance: "warning",
        error: "danger",
      };
      return types[status] || "info";
    };

    // 方法：获取状态文本
    const getStatusText = (status) => {
      const texts = {
        active: "在线",
        inactive: "离线",
        maintenance: "维护中",
        error: "错误",
      };
      return texts[status] || status;
    };

    // 分页方法
    const handleSizeChange = (size) => {
      pageSize.value = size;
      currentPage.value = 1;
    };

    const handleCurrentChange = (current) => {
      currentPage.value = current;
    };

    // 方法：检测节点状态
    const checkNodeStatus = async () => {
      try {
        // 循环遍历所有节点，检查状态
        for (const node of nodes.value) {
          try {
            // 这里应该调用API检查节点状态
            const response = await nodesApi.checkNodeStatus(node.id);
            // 更新节点状态
            node.status = response.data.status;
          } catch (error) {
            // 检查失败，标记为离线
            node.status = "inactive";
          }
        }
      } catch (error) {
        console.error("检测节点状态失败:", error);
      }
    };

    // 定时检测节点状态（每5分钟）
    let statusCheckInterval = null;

    // 组件挂载时启动定时任务
    onMounted(() => {
      // 立即检查一次
      checkNodeStatus();
      // 然后每5分钟检查一次
      statusCheckInterval = setInterval(checkNodeStatus, 5 * 60 * 1000);
    });

    // 组件卸载时清除定时任务
    onBeforeUnmount(() => {
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
      }
    });

    // 初始化加载节点列表和登录凭证
    loadNodes();
    getLoginCredentials();

    return {
      nodes,
      loading,
      searchQuery,
      currentPage,
      pageSize,
      filteredNodes,
      dialogVisible,
      dialogTitle,
      nodeFormRef,
      nodeForm,
      formRules,
      loginCredentials,
      credentialSearchQuery,
      detailCredentialSearchQuery,
      filteredLoginCredentials,
      detailDialogVisible,
      detailNodeFormRef,
      detailNodeForm,
      loadNodes,
      getLoginCredentials,
      openCreateDialog,
      openEditDialog,
      resetForm,
      submitForm,
      openDetailDialog,
      saveNodeDetail,
      resetDetailForm,
      deleteNode,
      getStatusType,
      getStatusText,
      handleSizeChange,
      handleCurrentChange,
    };
  },
};
</script>

<style scoped>
.nodes-container {
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

.nodes-card {
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
