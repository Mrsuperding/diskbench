import request from "./request";

// 用户管理接口
export default {
  // 获取用户列表
  getUsers() {
    return request.get("/users");
  },

  // 获取单个用户信息
  getUser(userId) {
    return request.get(`/users/${userId}`);
  },

  // 更新用户信息
  updateUser(userId, data) {
    return request.put(`/users/${userId}`, data);
  },

  // 删除用户
  deleteUser(userId) {
    return request.delete(`/users/${userId}`);
  },
};
