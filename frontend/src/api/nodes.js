import request from "./request";

// 节点管理接口
export default {
  // 获取节点列表
  getNodes() {
    return request.get("/nodes");
  },

  // 获取单个节点信息
  getNode(nodeId) {
    return request.get(`/nodes/${nodeId}`);
  },

  // 创建新节点
  createNode(data) {
    return request.post("/nodes", data);
  },

  // 更新节点信息
  updateNode(nodeId, data) {
    return request.put(`/nodes/${nodeId}`, data);
  },

  // 删除节点
  deleteNode(nodeId) {
    return request.delete(`/nodes/${nodeId}`);
  },

  // 检查节点状态
  checkNodeStatus(nodeId) {
    return request.get(`/nodes/${nodeId}/status`);
  },

  // 获取节点监控数据
  getNodeMetrics(nodeId) {
    return request.get(`/nodes/${nodeId}/metrics`);
  },

  // 获取节点历史监控数据
  getNodeMetricsHistory(nodeId, params) {
    return request.get(`/nodes/${nodeId}/metrics/history`, { params });
  },

  // 手动触发节点监控数据采集
  collectNodeMetrics(nodeId) {
    return request.post(`/nodes/${nodeId}/metrics/collect`);
  },

  // 批量采集所有节点监控数据
  collectAllMetrics() {
    return request.post("/nodes/metrics/collect-all");
  },
};
