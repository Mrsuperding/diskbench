<template>
  <div class="io-cases-container">
    <!-- 页面标题和操作按钮 -->
    <div class="page-header">
      <h1 class="page-title">IO测试用例管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 新建测试用例
        </el-button>
        <el-dropdown trigger="click" @command="handleTemplateCommand">
          <el-button type="success">
            <el-icon><CopyDocument /></el-icon> 使用模板
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="template in templates"
                :key="template.id"
                :command="template"
              >
                {{ template.name }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
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
        :data="filteredIOCases"
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
          :total="ioCases.length"
        />
      </div>
    </el-card>

    <!-- 创建/编辑/查看测试用例对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="1200px"
      @close="resetForm"
    >
      <div class="io-case-edit-container">
        <!-- 左侧：编辑表单 -->
        <div class="edit-section">
          <h3>编辑信息</h3>
          <el-form
            :model="ioCaseForm"
            :rules="formRules"
            ref="ioCaseFormRef"
            label-width="120px"
          >
            <el-form-item label="用例名称" prop="name">
              <el-input
                v-model="ioCaseForm.name"
                placeholder="请输入测试用例名称"
                @input="updatePreviewData"
              />
            </el-form-item>
            <el-form-item label="模板选择" prop="template_id">
              <el-select
                v-model="ioCaseForm.template_id"
                placeholder="请选择模板"
                filterable
                clearable
                @change="updatePreviewData"
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
                v-model="ioCaseForm.block_size"
                placeholder="支持多个值，用逗号分隔，例如：4,8,16"
                @input="updatePreviewData"
              />
            </el-form-item>
            <el-form-item label="队列深度" prop="queue_depth">
              <el-input
                v-model="ioCaseForm.queue_depth"
                placeholder="支持多个值，用逗号分隔，例如：1,8,16,32"
                @input="updatePreviewData"
              />
            </el-form-item>
            <el-form-item label="IO类型" prop="io_type">
              <el-input
                v-model="ioCaseForm.io_type"
                placeholder="支持多个值，用逗号分隔，例如：read,write,randread,randwrite"
                @input="updatePreviewData"
              />
            </el-form-item>
            <el-form-item label="读写比例" prop="read_write_ratio">
              <el-input
                v-model="ioCaseForm.read_write_ratio"
                placeholder="例如: 70:30"
                @input="updatePreviewData"
              />
            </el-form-item>
            <el-form-item label="运行时间(秒)" prop="runtime">
              <el-input-number
                v-model="ioCaseForm.runtime"
                :min="1"
                placeholder="请输入运行时间"
                @change="updatePreviewData"
              />
            </el-form-item>
            <el-form-item label="测试文件大小" prop="size">
              <el-input
                v-model="ioCaseForm.size"
                placeholder="例如: 1G"
                @input="updatePreviewData"
              />
            </el-form-item>
            <el-form-item label="分区选择" prop="partitions">
              <el-input
                v-model="ioCaseForm.partitions"
                placeholder="支持多个分区，用逗号分隔，例如：sda1,sda2,sdb1"
                @input="updatePreviewData"
              />
            </el-form-item>
            <el-form-item label="描述" prop="description">
              <el-input
                v-model="ioCaseForm.description"
                type="textarea"
                placeholder="请输入测试用例描述"
                :rows="3"
                @input="updatePreviewData"
              />
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
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Plus,
  Search,
  Delete,
  CopyDocument,
  ArrowDown,
} from "@element-plus/icons-vue";
import ioCasesApi from "../api/ioCases";

export default {
  name: "IOCases",
  components: {
    Plus,
    Search,
    Delete,
    CopyDocument,
    ArrowDown,
  },
  setup() {
    // 数据
    const ioCases = ref([]);
    const templates = ref([]);
    const loading = ref(false);
    const searchQuery = ref("");
    const currentPage = ref(1);
    const pageSize = ref(10);

    // 对话框
    const dialogVisible = ref(false);
    const dialogTitle = ref("新建测试用例");
    const editingIOCase = ref(null);

    // 预览数据
    const previewIOCase = reactive({});

    // 表单
    const ioCaseFormRef = ref(null);
    const ioCaseForm = reactive({
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
    });

    // 表单规则
    const formRules = reactive({
      name: [
        { required: true, message: "请输入测试用例名称", trigger: "blur" },
        {
          min: 2,
          max: 50,
          message: "测试用例名称长度在 2 到 50 个字符",
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

    // 计算属性：过滤后的测试用例列表
    const filteredIOCases = computed(() => {
      if (!searchQuery.value) return ioCases.value;
      return ioCases.value.filter((ioCase) =>
        ioCase.name.toLowerCase().includes(searchQuery.value.toLowerCase()),
      );
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

    // 方法：加载模板列表
    const loadTemplates = async () => {
      try {
        const response = await ioCasesApi.getTemplates();
        templates.value = response.data;
      } catch (error) {
        ElMessage.error("加载模板列表失败: " + error.message);
      }
    };

    // 方法：打开创建对话框
    const openCreateDialog = () => {
      dialogTitle.value = "新建测试用例";
      editingIOCase.value = null;
      resetForm();

      // 更新预览数据
      updatePreviewData();

      dialogVisible.value = true;
    };

    // 方法：更新预览数据
    const updatePreviewData = () => {
      // 更新预览数据
      Object.assign(previewIOCase, {
        name: ioCaseForm.name,
        description: ioCaseForm.description,
        parameters: {
          template_id: ioCaseForm.template_id,
          block_size: ioCaseForm.block_size,
          queue_depth: ioCaseForm.queue_depth,
          io_type: ioCaseForm.io_type,
          read_write_ratio: ioCaseForm.read_write_ratio,
          runtime: ioCaseForm.runtime,
          size: ioCaseForm.size,
          partitions: ioCaseForm.partitions,
        },
      });

      // 生成模型列表
      generateModelList(previewIOCase);
    };

    // 方法：打开编辑对话框
    const openEditDialog = (ioCase) => {
      dialogTitle.value = "编辑测试用例";
      editingIOCase.value = ioCase;

      // 从parameters中提取字段
      Object.assign(ioCaseForm, {
        name: ioCase.name,
        description: ioCase.description,
        template_id: ioCase.parameters?.template_id || null,
        block_size: String(ioCase.parameters?.block_size || "4"),
        queue_depth: String(ioCase.parameters?.queue_depth || "16"),
        io_type: ioCase.parameters?.io_type || "randread",
        read_write_ratio: ioCase.parameters?.read_write_ratio || "100:0",
        runtime: ioCase.parameters?.runtime || 60,
        size: ioCase.parameters?.size || "1G",
        partitions: ioCase.parameters?.partitions || "",
      });

      // 更新预览数据
      updatePreviewData();

      dialogVisible.value = true;
    };

    // 方法：重置表单
    const resetForm = () => {
      if (ioCaseFormRef.value) {
        ioCaseFormRef.value.resetFields();
      }
      Object.assign(ioCaseForm, {
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
      });

      // 更新预览数据
      updatePreviewData();
    };

    // 方法：提交表单
    const submitForm = async () => {
      if (!ioCaseFormRef.value) return;

      try {
        await ioCaseFormRef.value.validate();

        // 构建parameters JSON对象
        const caseData = {
          name: ioCaseForm.name,
          description: ioCaseForm.description,
          parameters: {
            template_id: ioCaseForm.template_id,
            block_size: ioCaseForm.block_size,
            queue_depth: ioCaseForm.queue_depth,
            io_type: ioCaseForm.io_type,
            read_write_ratio: ioCaseForm.read_write_ratio,
            runtime: ioCaseForm.runtime,
            size: ioCaseForm.size,
            partitions: ioCaseForm.partitions,
          },
        };

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
        if (error.name !== "Error") {
          // 表单验证错误
          return;
        }
        ElMessage.error("操作失败: " + error.message);
      }
    };

    // 方法：生成模型列表
    const modelList = ref([]);
    const generateModelList = (ioCase) => {
      const parameters = ioCase.parameters || {};
      const queueDepths = parameters.queue_depth
        ? parameters.queue_depth.split(",")
        : ["1"];
      const ioTypes = parameters.io_type
        ? parameters.io_type.split(",")
        : ["randread"];

      // 清空模型列表
      modelList.value = [];

      // 生成队列深度和读写模式的所有组合
      queueDepths.forEach((queueDepth) => {
        ioTypes.forEach((ioType) => {
          modelList.value.push({
            queueDepth: queueDepth.trim(),
            ioType: ioType.trim(),
            modelName: `模型-${queueDepth.trim()}-${ioType.trim()}`,
          });
        });
      });
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

    // 方法：处理模板命令
    const handleTemplateCommand = (template) => {
      // 使用模板填充表单
      dialogTitle.value = "基于模板新建测试用例";
      editingIOCase.value = null;
      resetForm();
      ioCaseForm.name = `${template.name} - 副本`;
      ioCaseForm.template_id = template.id;
      ioCaseForm.block_size = String(template.parameters?.block_size || "4");
      ioCaseForm.queue_depth = String(template.parameters?.queue_depth || "16");
      ioCaseForm.io_type = template.parameters?.io_type || "randread";
      ioCaseForm.read_write_ratio =
        template.parameters?.read_write_ratio || "100:0";
      ioCaseForm.runtime = template.parameters?.runtime || 60;
      ioCaseForm.size = template.parameters?.size || "1G";
      ioCaseForm.description = `基于模板 ${template.name} 创建的测试用例`;
      dialogVisible.value = true;
    };

    // 方法：获取IO类型
    const getIOType = (ioType) => {
      const types = {
        read: "primary",
        write: "danger",
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
        randread: "随机读",
        randwrite: "随机写",
        randrw: "混合读写",
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

    // 初始化加载数据
    onMounted(() => {
      loadIOCases();
      loadTemplates();
    });

    return {
      ioCases,
      templates,
      loading,
      searchQuery,
      currentPage,
      pageSize,
      filteredIOCases,
      dialogVisible,
      dialogTitle,
      ioCaseFormRef,
      ioCaseForm,
      formRules,
      previewIOCase,
      modelList,
      loadIOCases,
      loadTemplates,
      openCreateDialog,
      openEditDialog,
      resetForm,
      submitForm,

      deleteIOCase,
      handleTemplateCommand,
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
</style>
