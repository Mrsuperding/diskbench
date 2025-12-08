import {
  createRouter,
  createWebHistory,
  createWebHashHistory,
} from "vue-router";
import { useAuthStore } from "@/store/auth";

const routes = [
  {
    path: "/login",
    name: "Login",
    component: () => import("@/views/Login.vue"),
    meta: { requiresAuth: false },
  },
  {
    path: "/register",
    name: "Register",
    component: () => import("@/views/Register.vue"),
    meta: { requiresAuth: false },
  },
  {
    path: "/",
    name: "Layout",
    component: () => import("@/views/Layout.vue"),
    redirect: "/dashboard",
    meta: { requiresAuth: true },
    children: [
      {
        path: "/dashboard",
        name: "Dashboard",
        component: () => import("@/views/Dashboard.vue"),
        meta: { title: "仪表盘", icon: "Odometer" },
      },
      {
        path: "/tasks",
        name: "Tasks",
        component: () => import("@/views/Tasks.vue"),
        redirect: "/tasks/io-task-management",
        meta: { title: "任务管理", icon: "List" },
        children: [
          {
            path: "/tasks/io-task-management",
            name: "IOTaskManagement",
            component: () => import("@/views/Tasks.vue"),
            meta: { title: "IO任务管理", icon: "List" },
          },
          {
            path: "/tasks/script-task-management",
            name: "ScriptTaskManagement",
            component: () => import("@/views/Tasks.vue"),
            meta: { title: "脚本任务管理", icon: "List" },
          },
        ],
      },
      {
        path: "/tasks/:id",
        name: "TaskDetail",
        component: () => import("@/views/TaskDetail.vue"),
        meta: { title: "任务详情", icon: "List", hidden: true },
      },
      {
        path: "/task-space",
        name: "TaskSpace",
        component: () => import("@/views/TaskSpace.vue"),
        redirect: "/task-space/manage",
        meta: { title: "任务空间", icon: "Folder" },
        children: [
          {
            path: "/task-space/manage",
            name: "TaskSpaceManage",
            component: () => import("@/views/TaskSpace.vue"),
            meta: { title: "任务空间管理", icon: "Folder" },
          },
          {
            path: "/task-space/:id",
            name: "TaskSpaceDetail",
            component: () => import("@/views/TaskSpaceDetail.vue"),
            meta: { title: "任务空间详情", icon: "Folder", hidden: true },
          },
        ],
      },
      {
        path: "/nodes",
        name: "Nodes",
        component: () => import("@/views/Nodes.vue"),
        meta: { title: "节点管理", icon: "Monitor" },
      },
      {
        path: "/login-credentials",
        name: "LoginCredentials",
        component: () => import("@/views/LoginCredentials.vue"),
        redirect: "/login-credentials/manage",
        meta: { title: "登录凭证", icon: "KeyFilled" },
        children: [
          {
            path: "/login-credentials/manage",
            name: "LoginCredentialsManage",
            component: () => import("@/views/LoginCredentials.vue"),
            meta: { title: "登录凭证管理", icon: "KeyFilled" },
          },
        ],
      },
      {
        path: "/io-cases",
        name: "IOCases",
        component: () => import("@/views/IOCases.vue"),
        redirect: "/io-cases/manage",
        meta: { title: "IO用例", icon: "Document" },
        children: [
          {
            path: "/io-cases/manage",
            name: "IOCasesManage",
            component: () => import("@/views/IOCases.vue"),
            meta: { title: "IO用例管理", icon: "Document" },
          },
        ],
      },
      {
        path: "/results",
        name: "Results",
        component: () => import("@/views/Results.vue"),
        meta: { title: "测试结果", icon: "DataAnalysis" },
      },
      {
        path: "/users",
        name: "Users",
        component: () => import("@/views/Users.vue"),
        meta: { title: "用户管理", icon: "User", adminOnly: true },
      },
      {
        path: "/settings",
        name: "Settings",
        component: () => import("@/views/Settings.vue"),
        meta: { title: "系统设置", icon: "Setting" },
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("@/views/NotFound.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();

  // 检查是否需要认证
  if (to.meta.requiresAuth === false) {
    next();
    return;
  }

  // 确保认证状态已初始化
  if (authStore.token && !authStore.isAuthenticated) {
    try {
      await authStore.getUserInfo();
    } catch (error) {
      // 如果初始化失败，清除认证信息
      authStore.clearAuth();
    }
  }

  // 检查是否已登录
  if (!authStore.isAuthenticated) {
    next("/login");
    return;
  }

  // 检查管理员权限
  if (to.meta.adminOnly && !authStore.isAdmin) {
    next("/dashboard");
    return;
  }

  next();
});

export default router;
