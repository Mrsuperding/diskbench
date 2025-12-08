<template>
  <div class="task-space-container">
    <h1>任务空间</h1>

    <!-- 创建任务空间按钮 -->
    <div class="actions">
      <el-button type="primary" @click="showCreateDialog = true">
        <i class="el-icon-plus"></i> 创建任务空间
      </el-button>
    </div>

    <!-- 任务空间列表 -->
    <el-table :data="taskSpaces" style="width: 100%" border stripe>
      <el-table-column label="空间名称" width="200">
        <template #default="scope">
          <span class="space-name-link" @click="goToSpaceDetail(scope.row)">
            {{ scope.row.name }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" />
      <el-table-column prop="owner_name" label="所有者" width="120" />
      <el-table-column prop="member_count" label="成员数" width="80" />
      <el-table-column prop="is_public" label="是否公开" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.is_public ? 'success' : 'info'">
            {{ scope.row.is_public ? "公开" : "私有" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="scope">
          <el-button
            type="primary"
            size="small"
            @click="handleViewDetails(scope.row)"
          >
            <i class="el-icon-view"></i> 查看详情
          </el-button>
          <el-button type="warning" size="small" @click="handleEdit(scope.row)">
            <i class="el-icon-edit"></i> 编辑
          </el-button>
          <el-button
            type="danger"
            size="small"
            @click="handleDelete(scope.row)"
          >
            <i class="el-icon-delete"></i> 删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建任务空间对话框 -->
    <el-dialog title="创建任务空间" v-model="showCreateDialog" width="500px">
      <el-form :model="newTaskSpace" :rules="formRules" ref="createForm">
        <el-form-item label="空间名称" prop="name">
          <el-input v-model="newTaskSpace.name" placeholder="请输入空间名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="newTaskSpace.description"
            type="textarea"
            placeholder="请输入空间描述"
            rows="3"
          />
        </el-form-item>
        <el-form-item label="是否公开">
          <el-switch v-model="newTaskSpace.is_public" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="handleCreate">创建</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑任务空间对话框 -->
    <el-dialog title="编辑任务空间" v-model="showEditDialog" width="500px">
      <el-form :model="editingTaskSpace" :rules="formRules" ref="editForm">
        <el-form-item label="空间名称" prop="name">
          <el-input
            v-model="editingTaskSpace.name"
            placeholder="请输入空间名称"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="editingTaskSpace.description"
            type="textarea"
            placeholder="请输入空间描述"
            rows="3"
          />
        </el-form-item>
        <el-form-item label="是否公开">
          <el-switch v-model="editingTaskSpace.is_public" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="handleUpdate">更新</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 任务空间详情对话框 -->
    <el-dialog title="任务空间详情" v-model="showDetailDialog" width="800px">
      <div v-if="selectedTaskSpace">
        <h3>{{ selectedTaskSpace.name }}</h3>
        <p class="space-description">
          {{ selectedTaskSpace.description || "暂无描述" }}
        </p>
        <div class="space-info">
          <el-tag>所有者: {{ selectedTaskSpace.owner_name }}</el-tag>
          <el-tag>{{
            selectedTaskSpace.is_public ? "公开空间" : "私有空间"
          }}</el-tag>
          <el-tag>创建于: {{ selectedTaskSpace.created_at }}</el-tag>
        </div>

        <div class="members-section">
          <h4>成员列表</h4>
          <el-table :data="spaceMembers" style="width: 100%" border>
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column prop="role" label="角色" width="100">
              <template #default="scope">
                <el-tag
                  :type="scope.row.role === 'admin' ? 'danger' : 'success'"
                >
                  {{ scope.row.role === "admin" ? "管理员" : "成员" }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  getTaskSpaces,
  createTaskSpace,
  updateTaskSpace,
  deleteTaskSpace,
  getTaskSpaceMembers,
} from "@/api/taskSpaces";

export default {
  name: "TaskSpace",
  setup() {
    const router = useRouter();
    // 任务空间数据
    const taskSpaces = ref([]);
    const spaceMembers = ref([]);

    // 对话框状态
    const showCreateDialog = ref(false);
    const showEditDialog = ref(false);
    const showDetailDialog = ref(false);

    // 表单引用
    const createForm = ref(null);
    const editForm = ref(null);

    // 表单数据
    const newTaskSpace = reactive({
      name: "",
      description: "",
      is_public: false,
    });

    const editingTaskSpace = reactive({
      id: null,
      name: "",
      description: "",
      is_public: false,
    });

    const selectedTaskSpace = ref(null);

    // 表单验证规则
    const formRules = reactive({
      name: [
        { required: true, message: "请输入空间名称", trigger: "blur" },
        { min: 2, max: 50, message: "长度在 2 到 50 个字符", trigger: "blur" },
      ],
    });

    // 跳转到任务空间详情页面
    const goToSpaceDetail = (space) => {
      console.log("goToSpaceDetail called with space:", space);

      if (space && space.id) {
        // 使用vue-router进行跳转
        router.push(`/task-space/${space.id}`);
        console.log("Navigation initiated to task-space/", space.id);
      } else {
        console.error("Space object is invalid or missing id:", space);
      }
    };

    // 获取任务空间列表
    const loadTaskSpaces = async () => {
      try {
        const response = await getTaskSpaces();
        taskSpaces.value = response.data.items;
      } catch (error) {
        ElMessage.error(
          "获取任务空间列表失败: " +
            (error.response?.data?.message || error.message),
        );
      }
    };

    // 创建任务空间
    const handleCreate = async () => {
      if (!createForm.value) return;

      try {
        await createForm.value.validate();
        await createTaskSpace(newTaskSpace);
        ElMessage.success("任务空间创建成功");

        // 重置表单
        createForm.value.resetFields();
        showCreateDialog.value = false;

        // 重新加载列表
        loadTaskSpaces();
      } catch (error) {
        if (error.name === "Error" && error.message !== "Validation failed") {
          ElMessage.error(
            "创建任务空间失败: " +
              (error.response?.data?.message || error.message),
          );
        }
      }
    };

    // 编辑任务空间
    const handleEdit = (space) => {
      editingTaskSpace.id = space.id;
      editingTaskSpace.name = space.name;
      editingTaskSpace.description = space.description;
      editingTaskSpace.is_public = space.is_public;
      showEditDialog.value = true;
    };

    // 更新任务空间
    const handleUpdate = async () => {
      if (!editForm.value) return;

      try {
        await editForm.value.validate();
        await updateTaskSpace(editingTaskSpace.id, editingTaskSpace);
        ElMessage.success("任务空间更新成功");

        showEditDialog.value = false;

        // 重新加载列表
        loadTaskSpaces();
      } catch (error) {
        if (error.name === "Error" && error.message !== "Validation failed") {
          ElMessage.error(
            "更新任务空间失败: " +
              (error.response?.data?.message || error.message),
          );
        }
      }
    };

    // 删除任务空间
    const handleDelete = async (space) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除任务空间 "${space.name}" 吗？删除后将无法恢复。`,
          "删除确认",
          {
            confirmButtonText: "确定",
            cancelButtonText: "取消",
            type: "warning",
          },
        );

        await deleteTaskSpace(space.id);
        ElMessage.success("任务空间删除成功");

        // 重新加载列表
        loadTaskSpaces();
      } catch (error) {
        if (error !== "cancel") {
          ElMessage.error(
            "删除任务空间失败: " +
              (error.response?.data?.message || error.message),
          );
        }
      }
    };

    // 查看任务空间详情
    const handleViewDetails = (space) => {
      goToSpaceDetail(space);
    };

    // 初始化
    onMounted(() => {
      loadTaskSpaces();
    });

    return {
      taskSpaces,
      spaceMembers,
      showCreateDialog,
      showEditDialog,
      showDetailDialog,
      createForm,
      editForm,
      newTaskSpace,
      editingTaskSpace,
      selectedTaskSpace,
      formRules,
      handleCreate,
      handleEdit,
      handleUpdate,
      handleDelete,
      handleViewDetails,
      goToSpaceDetail,
    };
  },
};
</script>

<style scoped>
.task-space-container {
  padding: 20px;
}

.actions {
  margin-bottom: 20px;
}

.space-name-link {
  color: #409eff;
  cursor: pointer;
  text-decoration: underline;
}

.space-name-link:hover {
  color: #66b1ff;
}

.space-description {
  margin: 15px 0;
  font-size: 14px;
  color: #666;
}

.space-info {
  margin-bottom: 20px;
}

.space-info .el-tag {
  margin-right: 10px;
}

.members-section {
  margin-top: 30px;
}

.members-section h4 {
  margin-bottom: 15px;
  font-size: 16px;
  font-weight: bold;
}
</style>
