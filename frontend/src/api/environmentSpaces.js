import request from "./request";

export default {
  // 环境空间CRUD
  getEnvironmentSpaces(params) {
    return request.get("/environment-spaces", { params });
  },

  getEnvironmentSpace(id) {
    return request.get(`/environment-spaces/${id}`);
  },

  createEnvironmentSpace(data) {
    return request.post("/environment-spaces", data);
  },

  updateEnvironmentSpace(id, data) {
    return request.put(`/environment-spaces/${id}`, data);
  },

  deleteEnvironmentSpace(id) {
    return request.delete(`/environment-spaces/${id}`);
  },

  // 节点管理
  getEnvironmentSpaceNodes(spaceId) {
    return request.get(`/environment-spaces/${spaceId}/nodes`);
  },

  addNodesToSpace(spaceId, nodeIds) {
    // 批量添加节点
    const promises = nodeIds.map((nodeId) =>
      request.post(`/environment-spaces/${spaceId}/nodes/${nodeId}`)
    );
    return Promise.all(promises);
  },

  removeNodeFromSpace(spaceId, nodeId) {
    return request.delete(`/environment-spaces/${spaceId}/nodes/${nodeId}`);
  },

  // 监控数据
  getRealtimeMetrics(spaceId) {
    return request.get(`/environment-spaces/${spaceId}/metrics/realtime`);
  },

  getHistoryMetrics(spaceId, params) {
    return request.get(`/environment-spaces/${spaceId}/metrics/history`, {
      params,
    });
  },

  // 监控配置
  getMonitoringConfig(spaceId) {
    return request.get(`/monitoring-config/environment/${spaceId}`);
  },

  updateMonitoringConfig(spaceId, data) {
    return request.put(`/monitoring-config/environment/${spaceId}`, data);
  },

  // 手动采集环境空间的监控数据
  collectMetrics(spaceId) {
    return request.post(`/environment-spaces/${spaceId}/metrics/collect`);
  },
};
