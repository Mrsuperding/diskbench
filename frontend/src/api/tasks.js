import request from "./request";

// 任务管理接口
export default {
  // 获取任务列表
  getTasks(params = {}) {
    return request.get("/tasks", { params });
  },

  // 获取单个任务信息
  getTask(taskId) {
    return request.get(`/tasks/${taskId}`);
  },

  // 创建新任务
  createTask(data) {
    return request.post("/tasks", data);
  },

  // 更新任务信息
  updateTask(taskId, data) {
    return request.put(`/tasks/${taskId}`, data);
  },

  // 删除任务
  deleteTask(taskId) {
    return request.delete(`/tasks/${taskId}`);
  },

  // 执行任务
  executeTask(taskId) {
    return request.post(`/tasks/${taskId}/execute`);
  },

  // 暂停任务
  pauseTask(taskId) {
    return request.post(`/tasks/${taskId}/pause`);
  },

  // 获取任务的测试结果
  getTaskResults(taskId) {
    return request.get(`/tasks/${taskId}/results`);
  },

  // 克隆任务
  cloneTask(taskId) {
    return request.post(`/tasks/${taskId}/clone`);
  },
};