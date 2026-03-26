<template>
  <div class="io-cases-container">
    <!-- 页面标题和操作按钮 -->
    <div class="page-header">
      <h1 class="page-title">IO测试用例管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 新建测试用例
        </el-button>
      </div>
    </div>

    <!-- 测试用例列表 -->
    <el-card shadow="hover" class="io-cases-card">
      <template #header>
        <div class="card-header">
          <span>测试用例列表</span>
          <el-input
            v-model="searchQuery"
            placeholder="搜索测试用例名称"
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
        :data="paginatedIOCases"
        style="width: 100%"
        border
        stripe
        v-loading="loading"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="用例名称" show-overflow-tooltip>
          <template #default="scope">
            <a href="#" @click.prevent="openEditDialog(scope.row)">{{
              scope.row.name
            }}</a>
          </template>
        </el-table-column>
        <el-table-column label="模板ID" width="100">
          <template #default="{ row }">
            {{ row.parameters?.template_id || "-" }}
          </template>
        </el-table-column>
        <el-table-column label="块大小" width="120">
          <template #default="{ row }">
            {{ row.parameters?.block_size || "-" }}KB
          </template>
        </el-table-column>
        <el-table-column label="队列深度" width="120">
          <template #default="{ row }">
            {{ row.parameters?.queue_depth || "-" }}
          </template>
        </el-table-column>
        <el-table-column label="IO类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getIOType(row.parameters?.io_type)">
              {{ getIOTypeText(row.parameters?.io_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="读写比例" width="120">
          <template #default="{ row }">
            {{ row.parameters?.read_write_ratio || "-" }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="deleteIOCase(row)">
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
          :total="filteredIOCases.length"
        />
      </div>
    </el-card>

    <!-- 创建/编辑/查看测试用例对话框 -->
    <IOCaseEditor
      v-model="dialogVisible"
      :dialogTitle="dialogTitle"
      :initialData="currentIOCaseData"
      @submit="handleFormSubmit"
    />
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Search, Delete } from "@element-plus/icons-vue";
import ioCasesApi from "../api/ioCases";
import IOCaseEditor from "../components/IOCaseEditor.vue";

export default {
  name: "IOCases",
  components: {
    Plus,
    Search,
    Delete,
    IOCaseEditor,
  },
  setup() {
    // 数据
    const ioCases = ref([]);
    const loading = ref(false);
    const searchQuery = ref("");
    const currentPage = ref(1);
    const pageSize = ref(10);

    // 对话框
    const dialogVisible = ref(false);
    const dialogTitle = ref("新建测试用例");
    const editingIOCase = ref(null);
    const currentIOCaseData = ref({});

    // 计算属性：过滤后的测试用例列表
    const filteredIOCases = computed(() => {
      if (!searchQuery.value) return ioCases.value;
      return ioCases.value.filter((ioCase) =>
        ioCase.name.toLowerCase().includes(searchQuery.value.toLowerCase()),
      );
    });

    // 计算属性：分页后的测试用例列表
    const paginatedIOCases = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value;
      const end = start + pageSize.value;
      return filteredIOCases.value.slice(start, end);
    });

    // 方法：加载测试用例列表
    const loadIOCases = async () => {
      loading.value = true;
      try {
        const response = await ioCasesApi.getIOCases();
        ioCases.value = response.data;
      } catch (error) {
        ElMessage.error("加载测试用例列表失败: " + error.message);
      } finally {
        loading.value = false;
      }
    };

    // 方法：打开创建对话框
    const openCreateDialog = () => {
      dialogTitle.value = "新建测试用例";
      editingIOCase.value = null;
      currentIOCaseData.value = {};
      dialogVisible.value = true;
    };

    // 方法：打开编辑对话框
    const openEditDialog = (ioCase) => {
      dialogTitle.value = "编辑测试用例";
      editingIOCase.value = ioCase;
      currentIOCaseData.value = ioCase;
      dialogVisible.value = true;
    };

    // 方法：处理表单提交
    const handleFormSubmit = async (caseData) => {
      try {
        if (editingIOCase.value) {
          // 更新测试用例
          await ioCasesApi.updateIOCase(editingIOCase.value.id, caseData);
          ElMessage.success("测试用例更新成功");
        } else {
          // 创建测试用例
          await ioCasesApi.createIOCase(caseData);
          ElMessage.success("测试用例创建成功");
        }

        dialogVisible.value = false;
        loadIOCases(); // 重新加载测试用例列表
      } catch (error) {
        ElMessage.error("操作失败: " + error.message);
      }
    };

    // 方法：删除测试用例
    const deleteIOCase = (ioCase) => {
      ElMessageBox.confirm(
        `确定要删除测试用例「${ioCase.name}」吗？此操作不可恢复。`,
        "删除确认",
        {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
        },
      )
        .then(async () => {
          try {
            await ioCasesApi.deleteIOCase(ioCase.id);
            ElMessage.success("测试用例删除成功");
            loadIOCases(); // 重新加载测试用例列表
          } catch (error) {
            ElMessage.error("删除测试用例失败: " + error.message);
          }
        })
        .catch(() => {
          // 取消删除
        });
    };

    // 方法：获取IO类型
    const getIOType = (ioType) => {
      const types = {
        read: "primary",
        write: "danger",
        readwrite: "info",
        randread: "info",
        randwrite: "warning",
        randrw: "success",
      };
      return types[ioType] || "info";
    };

    // 方法：获取IO类型文本
    const getIOTypeText = (ioType) => {
      const texts = {
        read: "顺序读",
        write: "顺序写",
        readwrite: "顺序读写",
        randread: "随机读",
        randwrite: "随机写",
        randrw: "随机顺序读写",
      };
      return texts[ioType] || ioType;
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

    // 初始化加载数据
    onMounted(() => {
      loadIOCases();
    });

    return {
      ioCases,
      loading,
      searchQuery,
      currentPage,
      pageSize,
      filteredIOCases,
      paginatedIOCases,
      dialogVisible,
      dialogTitle,
      currentIOCaseData,
      loadIOCases,
      openCreateDialog,
      openEditDialog,
      handleFormSubmit,

      deleteIOCase,
      getIOType,
      getIOTypeText,
      handleSizeChange,
      handleCurrentChange,
    };
  },
};
</script>

<style scoped>
.io-cases-container {
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

.header-actions {
  display: flex;
  gap: 12px;
}

.io-cases-card {
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

/* 编辑对话框样式 */
.io-case-edit-container {
  display: flex;
  gap: 20px;
}

.edit-section {
  flex: 1;
}

.view-section {
  flex: 1;
}

.fio-params-card {
  margin-bottom: 20px;
}

.fio-params-form {
  margin-top: 10px;
}

.model-list-card {
  margin-bottom: 20px;
  max-height: 400px;
  overflow-y: auto;
}

/* 实时更新表单变化 */
.el-input,
.el-select,
.el-input-number {
  transition: all 0.3s;
}

/* 表单提示文本 */
.form-item-hint {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}
</style>
