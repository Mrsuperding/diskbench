import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";

import router from "./router";
import App from "./App.vue";

// 全局样式
import "./assets/css/global.css";

const app = createApp(App);
const pinia = createPinia();

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

app.use(pinia);
app.use(router);
app.use(ElementPlus);

// 初始化认证状态
import { useAuthStore } from "./store/auth";
const authStore = useAuthStore();
authStore.initAuth();

// 添加ResizeObserver错误处理，解决Element Plus表格等组件的ResizeObserver loop错误
if (window.ResizeObserver) {
  const originalResizeObserver = window.ResizeObserver;
  window.ResizeObserver = class ResizeObserver extends originalResizeObserver {
    constructor(callback) {
      super((entries, observer) => {
        // 使用setTimeout包装回调，避免ResizeObserver loop错误
        window.requestAnimationFrame(() => {
          callback(entries, observer);
        });
      });
    }
  };
}

// 挂载Vue应用并隐藏加载动画
app.mount("#app");

// 延迟隐藏加载动画，避免干扰Element Plus组件初始化
setTimeout(() => {
  // 移除加载动画
  const loadingElement = document.getElementById("app-loading");
  if (loadingElement) {
    loadingElement.style.display = "none";
  }
}, 1000);
