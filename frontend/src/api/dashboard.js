import request from "./request";

// 仪表盘接口
export default {
  // 获取仪表盘统计数据
  getStats() {
    return request.get("/dashboard/stats");
  },

  // 获取最近的任务列表
  getRecentTasks() {
    return request.get("/dashboard/recent-tasks");
  },

  // 获取最近的测试结果列表
  getRecentResults() {
    return request.get("/dashboard/recent-results");
  },

  // 获取节点状态统计
  getNodeStatus() {
    return request.get("/dashboard/node-status");
  },
};
