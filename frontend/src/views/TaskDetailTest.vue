<template>
  <div class="task-detail-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">任务详情</h1>
    </div>

    <!-- 任务详情卡片 -->
    <el-card class="task-detail-card">
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
          </el-table>
        </div>
      </el-collapse-item>
    </el-card>

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
import { ref, reactive } from "vue";
import { ElMessage } from "element-plus";
import IOCaseEditor from "../components/IOCaseEditor.vue";

export default {
  name: "TaskDetailTest",
  components: {
    IOCaseEditor,
  },
  setup() {
    // IO任务列表
    const ioTasks = ref([
      {
        id: 1,
        name: "测试IO任务",
        io_cases: [
          {
            name: "测试IO用例",
            parameters: {
              block_size: "4",
              queue_depth: "16",
              io_type: ["randread"],
              runtime: "60s",
              time_based: false,
            },
          },
        ],
      },
    ]);

    // 编辑IO用例模型对话框
    const editIOTaskDialogVisible = ref(false);
    const editIOTaskDialogTitle = ref("编辑IO用例模型");
    const editingIOTask = ref(null);
    const currentIOTaskData = ref({});

    // 编辑IO用例模型
    const editIOTask = (row) => {
      console.log("编辑IO用例模型，row数据:", row);
      editIOTaskDialogTitle.value = "编辑IO用例模型";
      editingIOTask.value = row;
      // 如果row中有io_cases数组，使用第一个元素作为initialData
      // 否则直接使用row
      if (row.io_cases && row.io_cases.length > 0) {
        console.log("使用io_cases[0]作为initialData:", row.io_cases[0]);
        currentIOTaskData.value = row.io_cases[0];
      } else {
        console.log("直接使用row作为initialData:", row);
        currentIOTaskData.value = row;
      }
      console.log("最终的currentIOTaskData:", currentIOTaskData.value);
      editIOTaskDialogVisible.value = true;
    };

    // 处理IO任务表单提交
    const handleIOTaskSubmit = async (taskData) => {
      try {
        console.log("提交的任务数据:", taskData);
        ElMessage.success("IO任务更新成功");
        editIOTaskDialogVisible.value = false;
      } catch (error) {
        ElMessage.error("IO任务更新失败: " + error.message);
      }
    };

    return {
      ioTasks,
      editIOTaskDialogVisible,
      editIOTaskDialogTitle,
      editingIOTask,
      currentIOTaskData,
      handleIOTaskSubmit,
      editIOTask,
    };
  },
};
</script>

<style scoped>
.task-detail-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
}

.task-detail-card {
  margin-bottom: 20px;
}
</style>
