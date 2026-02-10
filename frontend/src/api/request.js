import axios from "axios";
import { ElMessage } from "element-plus";
import { useAuthStore } from "@/store/auth";
import router from "@/router";

// 创建axios实例
const service = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    // 从localStorage直接获取token，避免在拦截器中使用Pinia store
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error("Request error:", error);
    return Promise.reject(error);
  },
);

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    // 如果是blob类型的响应，直接返回原始响应对象
    if (response.config.responseType === 'blob') {
      return response;
    }

    const { code, message, data, success } = response.data;

    // 检查HTTP状态码是否为成功状态
    if (response.status >= 200 && response.status < 300) {
      // 如果后端返回success字段，优先使用该字段判断
      if (typeof success !== "undefined") {
        if (success) {
          return {
            data: data || response.data,
            message: message || "Request successful",
          };
        } else {
          // 处理业务错误
          if (code === 401) {
            const authStore = useAuthStore();
            authStore.clearAuth();
            router.push("/login");
          }
          ElMessage.error(message || "Request failed");
          return Promise.reject(new Error(message || "Request failed"));
        }
      }

      // 对于没有success字段的响应，检查code是否为成功值
      if (typeof code !== "undefined") {
        if (code === 200 || code === 201) {
          return { data, message: message || "Request successful" };
        } else {
          // 处理业务错误
          if (code === 401) {
            const authStore = useAuthStore();
            authStore.clearAuth();
            router.push("/login");
          }
          ElMessage.error(message || "Request failed");
          return Promise.reject(new Error(message || "Request failed"));
        }
      }

      // 对于没有code和success字段的响应，直接返回数据
      return { data: response.data, message: message || "Request successful" };
    }

    // 处理HTTP状态码错误
    return Promise.reject(new Error(`HTTP Error: ${response.status}`));
  },
  (error) => {
    console.error("Response error:", error);

    let message = "Network error";
    if (error.response) {
      const { status, data } = error.response;
      if (status === 401) {
        const authStore = useAuthStore();
        authStore.clearAuth();
        router.push("/login");
        message = "Session expired, please login again";
      } else if (status === 403) {
        message = "Permission denied";
      } else if (status === 404) {
        message = "Resource not found";
      } else if (status >= 500) {
        message = "Server error";
      } else {
        message = data.message || "Request failed";
      }
    } else if (error.request) {
      message = "Network connection failed";
    }

    ElMessage.error(message);
    return Promise.reject(error);
  },
);

export default service;
