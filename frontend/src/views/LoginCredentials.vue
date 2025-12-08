<template>
  <div class="login-credentials-container">
    <!-- 页面标题和操作按钮 -->
    <div class="page-header">
      <h1 class="page-title">登录凭证管理</h1>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 新建登录凭证
      </el-button>
    </div>

    <!-- 登录凭证列表 -->
    <el-card shadow="hover" class="credentials-card">
      <template #header>
        <div class="card-header">
          <span>登录凭证列表</span>
          <el-input
            v-model="searchQuery"
            placeholder="搜索凭证别名"
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
        :data="filteredCredentials"
        style="width: 100%"
        border
        stripe
        v-loading="loading"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="alias" label="凭证别名" show-overflow-tooltip />
        <el-table-column prop="host" label="主机地址" show-overflow-tooltip />
        <el-table-column prop="port" label="端口" width="80" />
        <el-table-column prop="username" label="用户名" show-overflow-tooltip />
        <el-table-column prop="auth_type" label="认证类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getAuthTypeTag(row.auth_type)">
              {{ row.auth_type === "password" ? "密码认证" : "密钥认证" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="openEditDialog(row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteCredential(row)"
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
          :total="credentials.length"
        />
      </div>
    </el-card>

    <!-- 创建/编辑登录凭证对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        :model="credentialForm"
        :rules="formRules"
        ref="credentialFormRef"
        label-width="120px"
      >
        <el-form-item label="凭证别名" prop="alias">
          <el-input
            v-model="credentialForm.alias"
            placeholder="请输入凭证别名"
          />
        </el-form-item>
        <el-form-item v-if="!editingCredential" label="主机地址" prop="host">
          <el-input
            v-model="credentialForm.host"
            placeholder="请输入主机地址（如：192.168.1.100）"
          />
        </el-form-item>
        <el-form-item v-if="!editingCredential" label="端口" prop="port">
          <el-input-number
            v-model="credentialForm.port"
            :min="1"
            :max="65535"
            placeholder="请输入端口"
          />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="credentialForm.username"
            placeholder="请输入用户名"
          />
        </el-form-item>
        <el-form-item label="认证类型" prop="auth_type">
          <el-radio-group v-model="credentialForm.auth_type">
            <el-radio label="password">密码认证</el-radio>
            <el-radio label="key">密钥认证</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item
          v-if="credentialForm.auth_type === 'password'"
          label="密码"
          prop="password"
        >
          <el-input
            v-model="credentialForm.password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="请输入密码"
          >
            <template #suffix>
              <el-icon @click="showPassword = !showPassword">
                <Hide v-if="showPassword" />
                <View v-else />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item
          v-if="credentialForm.auth_type === 'key'"
          label="私钥内容"
          prop="private_key"
        >
          <el-input
            v-model="credentialForm.private_key"
            type="textarea"
            placeholder="请输入私钥内容"
            :rows="6"
          />
        </el-form-item>
        <el-form-item
          v-if="credentialForm.auth_type === 'key'"
          label="私钥密码"
          prop="passphrase"
        >
          <el-input
            v-model="credentialForm.passphrase"
            type="password"
            placeholder="请输入私钥密码（如无则不填）"
          />
        </el-form-item>
        <el-form-item label="平台分区路径" prop="platform_partition">
          <el-input
            v-model="credentialForm.platform_partition"
            placeholder="请输入平台分区路径，用于存储运行日志、IO日志和依赖文件"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="credentialForm.description"
            type="textarea"
            placeholder="请输入凭证描述"
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
  </div>
</template>

<script setup>
import { ref, reactive, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import loginCredentialsApi from "@/api/loginCredentials";
import { useRouter } from "vue-router";
import { Plus, Search, Edit, Delete, Hide, View } from "@element-plus/icons-vue";

// 创建路由实例
const router = useRouter();
// 数据
const credentials = ref([]);
const loading = ref(false);
const searchQuery = ref("");
const currentPage = ref(1);
const pageSize = ref(10);
const showPassword = ref(false);

// 对话框
const dialogVisible = ref(false);
const dialogTitle = ref("新建登录凭证");
const editingCredential = ref(null);

// 表单
const credentialFormRef = ref(null);
const credentialForm = reactive({
  alias: "",
  host: "",
  port: 22,
  username: "",
  auth_type: "password",
  password: "",
  private_key: "",
  passphrase: "",
  platform_partition: "/opt/io_platform",
  description: "",
});

// 表单规则
const formRules = reactive({
  alias: [
    { required: true, message: "请输入凭证别名", trigger: "blur" },
    {
      min: 2,
      max: 50,
      message: "凭证别名长度在 2 到 50 个字符",
      trigger: "blur",
    },
  ],
  host: [
    {
      required: () => !editingCredential.value,
      message: "请输入主机地址",
      trigger: "blur",
    },
    {
      pattern:
        /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
      message: "请输入有效的IP地址",
      trigger: "blur",
    },
  ],
  port: [
    {
      required: () => !editingCredential.value,
      message: "请输入端口",
      trigger: "blur",
    },
    {
      type: "number",
      min: 1,
      max: 65535,
      message: "端口范围在 1 到 65535 之间",
      trigger: "blur",
    },
  ],
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    {
      min: 1,
      max: 50,
      message: "用户名长度在 1 到 50 个字符",
      trigger: "blur",
    },
  ],
  password: [
    {
      required: () => !editingCredential.value && credentialForm.auth_type === "password",
      message: "请输入密码",
      trigger: "blur",
    },
  ],
  private_key: [
    {
      required: () => !editingCredential.value && credentialForm.auth_type === "key",
      message: "请输入私钥内容",
      trigger: "blur",
    },
  ],
});

// 计算属性：过滤后的凭证列表
const filteredCredentials = computed(() => {
  if (!searchQuery.value) return credentials.value;
  return credentials.value.filter((credential) =>
    credential.alias.toLowerCase().includes(searchQuery.value.toLowerCase()),
  );
});

// 方法：加载登录凭证列表
const loadCredentials = async () => {
  loading.value = true;
  try {
    const response = await loginCredentialsApi.getLoginCredentials();
    credentials.value = response.data;
  } catch (error) {
    ElMessage.error("加载登录凭证列表失败: " + error.message);
  } finally {
    loading.value = false;
  }
};

// 方法：打开创建对话框
const openCreateDialog = () => {
  dialogTitle.value = "新建登录凭证";
  editingCredential.value = null;
  resetForm();
  dialogVisible.value = true;
};

// 方法：打开编辑对话框
const openEditDialog = async (credential) => {
  loading.value = true;
  try {
    dialogTitle.value = "编辑登录凭证";
    editingCredential.value = credential;
    
    console.log('打开编辑对话框，原始凭证信息:', credential);
    
    // 获取包含敏感字段的完整凭证信息
    const response = await loginCredentialsApi.getLoginCredential(credential.id);
    console.log('API响应:', response);
    
    // 安全地获取凭证数据，处理不同的响应结构
    let fullCredential = null;
    if (response && response.data) {
      // 如果响应数据有data字段，检查是否是嵌套结构
      if (response.data.data) {
        fullCredential = response.data.data;
      } else {
        fullCredential = response.data;
      }
    }
    
    console.log('最终使用的凭证信息:', fullCredential);
    
    // 检查fullCredential是否有效
    if (!fullCredential || typeof fullCredential !== 'object') {
      throw new Error('获取的凭证信息格式不正确');
    }
    
    // 复制凭证信息到表单，添加空值检查
    credentialForm.alias = fullCredential.alias || credential.alias;
    credentialForm.username = fullCredential.username || credential.username;
    credentialForm.auth_type = fullCredential.auth_type || credential.auth_type;
    credentialForm.password = fullCredential.password || '';
    credentialForm.private_key = fullCredential.private_key || '';
    credentialForm.passphrase = fullCredential.passphrase || '';
    credentialForm.platform_partition = fullCredential.platform_partition || credential.platform_partition;
    credentialForm.description = fullCredential.description || credential.description;
    
    console.log('表单数据设置后:', credentialForm);
    
    dialogVisible.value = true;
  } catch (error) {
    console.error('加载登录凭证详情失败:', error);
    ElMessage.error("加载登录凭证详情失败: " + error.message);
  } finally {
    loading.value = false;
  }
};

// 方法：重置表单
const resetForm = () => {
  if (credentialFormRef.value) {
    credentialFormRef.value.resetFields();
  }
  Object.assign(credentialForm, {
    alias: "",
    host: "",
    port: 22,
    username: "",
    auth_type: "password",
    password: "",
    private_key: "",
    passphrase: "",
    platform_partition: "/opt/io_platform",
    description: "",
  });
};

// 方法：提交表单
const submitForm = async () => {
  if (!credentialFormRef.value) return;

  try {
    await credentialFormRef.value.validate();

    if (editingCredential.value) {
      // 更新登录凭证
      await loginCredentialsApi.updateLoginCredential(
        editingCredential.value.id,
        credentialForm,
      );
      ElMessage.success("登录凭证更新成功");
    } else {
      // 创建登录凭证
      await loginCredentialsApi.createLoginCredential(credentialForm);
      ElMessage.success("登录凭证创建成功");
    }

    dialogVisible.value = false;
    loadCredentials(); // 重新加载登录凭证列表
  } catch (error) {
    if (error.name !== "Error") {
      // 表单验证错误
      return;
    }
    ElMessage.error("操作失败: " + error.message);
  }
};

// 方法：删除登录凭证
const deleteCredential = (credential) => {
  ElMessageBox.confirm(
    `确定要删除登录凭证「${credential.alias}」吗？此操作不可恢复。`,
    "删除确认",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    },
  )
    .then(async () => {
      try {
        await loginCredentialsApi.deleteLoginCredential(credential.id);
        ElMessage.success("登录凭证删除成功");
        loadCredentials(); // 重新加载登录凭证列表
      } catch (error) {
        ElMessage.error("删除登录凭证失败: " + error.message);
      }
    })
    .catch(() => {
      // 取消删除
    });
};

// 方法：获取认证类型标签
const getAuthTypeTag = (authType) => {
  return authType === "password" ? "primary" : "success";
};

// 分页方法
const handleSizeChange = (size) => {
  pageSize.value = size;
  currentPage.value = 1;
};

const handleCurrentChange = (current) => {
  currentPage.value = current;
};

// 初始化加载登录凭证列表
loadCredentials();
</script>

<style scoped>
.login-credentials-container {
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

.credentials-card {
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
