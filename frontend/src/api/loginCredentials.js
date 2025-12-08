import request from "./request";

const loginCredentialsApi = {
  // 获取登录凭证列表
  getLoginCredentials() {
    return request({
      url: "/login-credentials",
      method: "get",
    });
  },

  // 获取单个登录凭证
  getLoginCredential(id) {
    return request({
      url: `/login-credentials/${id}`,
      method: "get",
    });
  },

  // 创建登录凭证
  createLoginCredential(data) {
    return request({
      url: "/login-credentials",
      method: "post",
      data,
    });
  },

  // 更新登录凭证
  updateLoginCredential(id, data) {
    return request({
      url: `/login-credentials/${id}`,
      method: "put",
      data,
    });
  },

  // 删除登录凭证
  deleteLoginCredential(id) {
    return request({
      url: `/login-credentials/${id}`,
      method: "delete",
    });
  },

  // 测试登录凭证连接
  testLoginCredential(id) {
    return request({
      url: `/login-credentials/${id}/test`,
      method: "post",
    });
  },
};

export default loginCredentialsApi;
