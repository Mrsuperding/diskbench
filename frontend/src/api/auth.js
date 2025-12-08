import request from "./request";

const authApi = {
  login(data) {
    return request({
      url: "/auth/login",
      method: "post",
      data,
    });
  },

  register(data) {
    return request({
      url: "/auth/register",
      method: "post",
      data,
    });
  },

  logout() {
    return request({
      url: "/auth/logout",
      method: "post",
    });
  },

  getUserInfo() {
    return request({
      url: "/auth/userinfo",
      method: "get",
    });
  },

  refreshToken() {
    return request({
      url: "/auth/refresh",
      method: "post",
    });
  },

  updatePassword(data) {
    return request({
      url: "/auth/password",
      method: "put",
      data,
    });
  },
};

export default authApi;
