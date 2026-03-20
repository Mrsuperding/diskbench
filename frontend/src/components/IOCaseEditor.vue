<template>
  <el-dialog
    v-bind:model-value="modelValue"
    v-on:update:model-value="$emit('update:modelValue', $event)"
    :title="dialogTitle"
    width="1200px"
    @close="resetForm"
  >
    <div class="io-case-edit-container">
      <!-- 左侧：编辑表单 -->
      <div class="edit-section">
        <h3>{{ formTitle }}</h3>
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
            <el-select
              v-model="ioCaseForm.io_type"
              placeholder="请选择IO类型"
              multiple
              @change="updatePreviewData"
            >
              <el-option label="顺序读" value="read" />
              <el-option label="顺序写" value="write" />
              <el-option label="顺序读写" value="rw" />
              <el-option label="随机读" value="randread" />
              <el-option label="随机写" value="randwrite" />
              <el-option label="随机顺序读写" value="randrw" />
            </el-select>
            <span class="form-item-hint">支持多选，会生成多个测试模型</span>
          </el-form-item>
          <el-form-item label="读写比例" prop="read_write_ratio">
            <el-input
              v-model="ioCaseForm.read_write_ratio"
              placeholder="例如: 70:30"
              @input="updatePreviewData"
            />
          </el-form-item>
          <el-form-item label="运行时间" prop="runtime">
            <el-input
              v-model="ioCaseForm.runtime"
              placeholder="请输入运行时间，例如：60s, 5m, 1h"
              @input="updatePreviewData"
            />
          </el-form-item>
          <el-form-item label="时间基准测试" prop="time_based">
            <el-switch
              v-model="ioCaseForm.time_based"
              @change="updatePreviewData"
            />
            <span class="form-item-hint"
              >勾选后，测试将基于时间执行，而不是基于数据量</span
            >
          </el-form-item>
          <el-form-item label="测试文件大小" prop="size">
            <el-input
              v-model="ioCaseForm.size"
              placeholder="例如: 1G"
              @input="updatePreviewData"
            />
          </el-form-item>
          <el-form-item label="IO引擎" prop="ioengine">
            <el-select
              v-model="ioCaseForm.ioengine"
              placeholder="请选择IO引擎"
              @change="updatePreviewData"
            >
              <el-option label="libaio" value="libaio" />
              <el-option label="psync" value="psync" />
              <el-option label="sync" value="sync" />
              <el-option label="native" value="native" />
            </el-select>
          </el-form-item>
          <el-form-item label="直接IO" prop="direct">
            <el-switch
              v-model="ioCaseForm.direct"
              @change="updatePreviewData"
            />
            <span class="form-item-hint"
              >勾选后使用直接IO，绕过操作系统缓存</span
            >
          </el-form-item>
          <el-form-item label="同步IO" prop="sync">
            <el-switch v-model="ioCaseForm.sync" @change="updatePreviewData" />
            <span class="form-item-hint">勾选后使用同步IO</span>
          </el-form-item>
          <el-form-item label="并发作业数" prop="numjobs">
            <el-input
              v-model="ioCaseForm.numjobs"
              placeholder="请输入并发作业数，默认值：1"
              @input="updatePreviewData"
            />
          </el-form-item>
          <el-form-item label="额外参数" prop="description">
            <el-input
              v-model="ioCaseForm.description"
              type="textarea"
              placeholder="请输入额外的fio参数，例如：--norandommap --randrepeat=0，多个参数用空格分隔"
              :rows="3"
              @input="updatePreviewData"
            />
            <span class="form-item-hint">这些参数会直接添加到fio命令后面</span>
          </el-form-item>
          <el-form-item v-if="showStatus" label="任务状态" prop="status">
            <el-select v-model="ioCaseForm.status" placeholder="请选择任务状态">
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
            <el-table-column prop="blockSize" label="块大小" width="100" />
            <el-table-column prop="queueDepth" label="队列深度" width="100" />
            <el-table-column prop="ioType" label="读写模式" width="120" />
            <el-table-column prop="modelName" label="模型名称" />
          </el-table>
        </el-card>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="$emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script>
import { ref, reactive, watch } from "vue";
import { ElMessage } from "element-plus";

export default {
  name: "IOCaseEditor",
  props: {
    modelValue: {
      type: Boolean,
      default: false,
    },
    dialogTitle: {
      type: String,
      default: "编辑IO用例模型",
    },
    formTitle: {
      type: String,
      default: "编辑信息",
    },
    showStatus: {
      type: Boolean,
      default: false,
    },
    initialData: {
      type: Object,
      default: () => ({}),
    },
  },
  emits: ["update:modelValue", "submit"],
  setup(props, { emit }) {
    // 表单
    const ioCaseFormRef = ref(null);
    const ioCaseForm = reactive({
      name: "",
      block_size: "4",
      queue_depth: "16",
      io_type: ["randread"],
      read_write_ratio: "100:0",
      runtime: "60s",
      size: "1G",
      time_based: false,
      ioengine: "libaio",
      direct: true,
      sync: false,
      numjobs: "1",
      description: "",
      status: "pending",
    });

    // 预览数据
    const previewIOCase = reactive({});

    // 模型列表
    const modelList = ref([]);

    // 方法：生成模型列表
    function generateModelList(ioCase) {
      const parameters = ioCase.parameters || {};
      const blockSizes = parameters.block_size
        ? parameters.block_size.split(",")
        : ["4"];
      const queueDepths = parameters.queue_depth
        ? parameters.queue_depth.split(",")
        : ["1"];
      const ioTypes = Array.isArray(parameters.io_type)
        ? parameters.io_type
        : parameters.io_type
          ? parameters.io_type.split(",")
          : ["randread"];
      const numjobsList = parameters.numjobs
        ? parameters.numjobs.split(",")
        : ["1"];

      // 清空模型列表
      modelList.value = [];

      // 生成块大小、队列深度、读写模式和并发作业数量的所有组合
      blockSizes.forEach((blockSize) => {
        queueDepths.forEach((queueDepth) => {
          ioTypes.forEach((ioType) => {
            numjobsList.forEach((numjobs) => {
              // 处理块大小，确保格式正确
              let processedBlockSize = blockSize.trim();
              // 如果块大小是纯数字，添加'k'单位
              if (/^\d+$/.test(processedBlockSize)) {
                processedBlockSize = `${processedBlockSize}k`;
              }

              modelList.value.push({
                blockSize: processedBlockSize,
                queueDepth: queueDepth.trim(),
                ioType: ioType.trim(),
                modelName: `${processedBlockSize}_${queueDepth.trim()}d_${ioType.trim()}_${numjobs.trim()}n`,
              });
            });
          });
        });
      });
    }

    // 方法：更新预览数据
    function updatePreviewData() {
      // 更新预览数据
      Object.assign(previewIOCase, {
        name: ioCaseForm.name,
        description: ioCaseForm.description,
        parameters: {
          block_size: ioCaseForm.block_size,
          queue_depth: ioCaseForm.queue_depth,
          io_type: ioCaseForm.io_type,
          read_write_ratio: ioCaseForm.read_write_ratio,
          runtime: ioCaseForm.runtime,
          size: ioCaseForm.size,
          time_based: ioCaseForm.time_based,
          ioengine: ioCaseForm.ioengine,
          direct: ioCaseForm.direct,
          sync: ioCaseForm.sync,
          numjobs: ioCaseForm.numjobs,
        },
        status: ioCaseForm.status,
      });

      // 生成模型列表
      generateModelList(previewIOCase);
    }

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
      runtime: [{ required: true, message: "请输入运行时间", trigger: "blur" }],
    });

    // 方法：重置表单
    function resetForm() {
      if (ioCaseFormRef.value) {
        ioCaseFormRef.value.resetFields();
      }
      Object.assign(ioCaseForm, {
        name: "",
        block_size: "4",
        queue_depth: "16",
        io_type: ["randread"],
        read_write_ratio: "100:0",
        runtime: "60s",
        size: "1G",
        time_based: false,
        ioengine: "libaio",
        direct: true,
        sync: false,
        numjobs: "1",
        description: "",
        status: "pending",
      });

      // 更新预览数据
      updatePreviewData();

      // 通知父组件对话框已关闭
      emit("update:modelValue", false);
    }

    // 方法：提交表单
    async function submitForm() {
      if (!ioCaseFormRef.value) return;

      try {
        await ioCaseFormRef.value.validate();

        // 构建parameters JSON对象
        const caseData = {
          name: ioCaseForm.name,
          description: ioCaseForm.description,
          parameters: {
            block_size: ioCaseForm.block_size,
            queue_depth: ioCaseForm.queue_depth,
            io_type: ioCaseForm.io_type,
            read_write_ratio: ioCaseForm.read_write_ratio,
            runtime: ioCaseForm.runtime,
            size: ioCaseForm.size,
            time_based: ioCaseForm.time_based,
            ioengine: ioCaseForm.ioengine,
            direct: ioCaseForm.direct,
            sync: ioCaseForm.sync,
            numjobs: ioCaseForm.numjobs,
          },
          status: ioCaseForm.status,
        };

        // 通知父组件提交数据
        emit("submit", caseData);
      } catch (error) {
        if (error.name !== "Error") {
          // 表单验证错误
          return;
        }
        ElMessage.error("操作失败: " + error.message);
      }
    }

    // 监听initialData变化，更新表单
    watch(
      () => props.initialData,
      (newData) => {
        console.log("IOCaseEditor接收到的initialData:", newData);
        if (newData) {
          console.log("newData.name:", newData.name);
          // 直接使用newData的数据，如果没有parameters则使用默认值
          Object.assign(ioCaseForm, {
            name: newData.name || "",
            description: newData.description || "",
            block_size:
              newData.block_size || newData.parameters?.block_size || "4",
            queue_depth:
              newData.queue_depth || newData.parameters?.queue_depth || "16",
            io_type: Array.isArray(newData.io_type)
              ? newData.io_type
              : Array.isArray(newData.parameters?.io_type)
                ? newData.parameters.io_type
                : newData.io_type || newData.parameters?.io_type
                  ? [newData.io_type || newData.parameters.io_type]
                  : ["randread"],
            read_write_ratio:
              newData.read_write_ratio ||
              newData.parameters?.read_write_ratio ||
              "100:0",
            runtime: newData.runtime || newData.parameters?.runtime || "60s",
            size: newData.size || newData.parameters?.size || "1G",
            time_based:
              newData.time_based || newData.parameters?.time_based || false,
            ioengine:
              newData.ioengine || newData.parameters?.ioengine || "libaio",
            direct:
              newData.direct !== undefined
                ? newData.direct
                : newData.parameters?.direct !== undefined
                  ? newData.parameters.direct
                  : true,
            sync: newData.sync || newData.parameters?.sync || false,
            numjobs: newData.numjobs || newData.parameters?.numjobs || "1",
            status: newData.status || "pending",
          });
          console.log("更新后的ioCaseForm:", ioCaseForm);
          updatePreviewData();
        }
      },
      { deep: true, immediate: true },
    );

    return {
      ioCaseFormRef,
      ioCaseForm,
      formRules,
      previewIOCase,
      modelList,
      updatePreviewData,
      generateModelList,
      resetForm,
      submitForm,
    };
  },
};
</script>

<style scoped>
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

.model-list-card {
  margin-bottom: 20px;
  max-height: 400px;
  overflow-y: auto;
}

/* 表单提示文本 */
.form-item-hint {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}
</style>
