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
};
