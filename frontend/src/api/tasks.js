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
  executeTask(taskId, executionMode = 'restart') {
    return request.post(`/tasks/run/${taskId}`, { execution_mode: executionMode });
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

  // 获取任务日志
  getTaskLogs(taskId, params = {}) {
    return request.get(`/tasks/${taskId}/logs`, { params });
  },

  // 打包任务日志
  packageTaskLogs(taskId) {
    return request.post(`/tasks/${taskId}/logs/package`);
  },

  // 下载任务日志
  downloadTaskLogs(taskId) {
    return request({
      url: `/tasks/${taskId}/logs/download`,
      method: "get",
      responseType: "blob", // 重要：设置响应类型为blob
    });
  },

  // 获取IOSTAT指标数据
  getIOStatMetrics(logId, params) {
    return request({
      url: `/logs/${logId}/iostat-metrics`,
      method: "get",
      params,
    });
  },

  // 多任务性能对比
  compareTasks(data) {
    return request.post("/tasks/compare", data);
  },
};
