import request from "./request";

// 测试结果接口
export default {
  // 获取测试结果列表
  getResults() {
    return request.get("/results");
  },

  // 获取单个测试结果信息
  getResult(resultId) {
    return request.get(`/results/${resultId}`);
  },

  // 删除测试结果
  deleteResult(resultId) {
    return request.delete(`/results/${resultId}`);
  },

  // 获取测试结果聚合数据
  getAggregations() {
    return request.get("/results/aggregations");
  },

  // 获取单个测试结果聚合信息
  getAggregation(aggId) {
    return request.get(`/results/aggregations/${aggId}`);
  },
};
