import { defineStore } from "pinia";
import authApi from "@/api/auth";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,
    token: localStorage.getItem("token") || null,
    isAuthenticated: false,
    loading: false,
  }),

  getters: {
    isAdmin: (state) => {
      return state.user && state.user.role === "admin";
    },
    username: (state) => {
      return state.user ? state.user.username : "";
    },
  },

  actions: {
    async login(credentials) {
      this.loading = true;
      try {
        const response = await authApi.login(credentials);
        const { token, user } = response.data; // response.data 已经是后端返回的 data 字段内容

        this.token = token;
        this.user = user;
        this.isAuthenticated = true;

        localStorage.setItem("token", token);

        return Promise.resolve(response);
      } catch (error) {
        this.clearAuth(); // 使用 clearAuth 而不是 logout，避免不必要的 API 调用
        return Promise.reject(error);
      } finally {
        this.loading = false;
      }
    },

    async logout() {
      try {
        await authApi.logout();
      } catch (error) {
        console.error("Logout error:", error);
      } finally {
        this.clearAuth();
      }
    },

    async getUserInfo() {
      if (!this.token) return;

      try {
        const response = await authApi.getUserInfo();
        this.user = response.data;
        this.isAuthenticated = true;
        return Promise.resolve(response);
      } catch (error) {
        this.clearAuth();
        return Promise.reject(error);
      }
    },

    clearAuth() {
      this.user = null;
      this.token = null;
      this.isAuthenticated = false;
      localStorage.removeItem("token");
    },

    async initAuth() {
      if (this.token) {
        await this.getUserInfo();
      }
    },
  },
});
