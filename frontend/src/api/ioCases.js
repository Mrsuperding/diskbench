import request from "./request";

// IO测试用例接口
export default {
  // 获取IO测试用例列表
  getIOCases() {
    return request.get("/io-cases");
  },

  // 获取单个IO测试用例信息
  getIOCase(caseId) {
    return request.get(`/io-cases/${caseId}`);
  },

  // 创建新IO测试用例
  createIOCase(data) {
    return request.post("/io-cases", data);
  },

  // 更新IO测试用例信息
  updateIOCase(caseId, data) {
    return request.put(`/io-cases/${caseId}`, data);
  },

  // 删除IO测试用例
  deleteIOCase(caseId) {
    return request.delete(`/io-cases/${caseId}`);
  },

  // 获取测试用例模板列表
  getTemplates() {
    return request.get("/io-cases/templates");
  },
};
