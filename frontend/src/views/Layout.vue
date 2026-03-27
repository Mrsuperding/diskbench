<template>
  <el-container class="layout-container">
    <!-- 顶部导航栏 -->
    <el-header class="layout-header">
      <div class="header-content">
        <div class="logo-section">
          <img src="@/assets/logo.svg" alt="Logo" class="logo" />
          <span class="system-title">IO性能测试平台</span>
        </div>

        <div class="header-actions">
          <el-tooltip content="全屏" placement="bottom">
            <el-button circle @click="toggleFullscreen">
              <el-icon><FullScreen /></el-icon>
            </el-button>
          </el-tooltip>

          <el-dropdown @command="handleUserCommand">
            <span class="user-dropdown">
              <el-avatar :size="32" :src="userAvatar">
                <el-icon><UserFilled /></el-icon>
              </el-avatar>
              <span class="username">{{ authStore.username }}</span>
              <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人设置
                </el-dropdown-item>
                <el-dropdown-item command="password">
                  <el-icon><Key /></el-icon>修改密码
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-header>

    <el-container>
      <!-- 侧边菜单 -->
      <el-aside width="220px" class="layout-aside">
        <el-menu
          v-if="!isLoading"
          :default-active="activeMenu"
          router
          :collapse="isCollapse"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409eff"
          unique-opened
        >
          <template v-for="route in menuRoutes" :key="route.path">
            <el-menu-item
              v-if="!route.children"
              :index="route.path"
              :disabled="route.meta?.disabled"
            >
              <el-icon v-if="route.meta?.icon">
                <component :is="route.meta.icon" />
              </el-icon>
              <template #title>{{ route.meta?.title }}</template>
            </el-menu-item>

            <el-sub-menu v-else :index="route.path">
              <template #title>
                <el-icon v-if="route.meta?.icon">
                  <component :is="route.meta.icon" />
                </el-icon>
                <span>{{ route.meta?.title }}</span>
              </template>
              <el-menu-item
                v-for="child in getVisibleChildren(route.children)"
                :key="child.path"
                :index="child.path"
                :disabled="child.meta?.disabled"
              >
                <el-icon v-if="child.meta?.icon">
                  <component :is="child.meta.icon" />
                </el-icon>
                <template #title>{{ child.meta?.title }}</template>
              </el-menu-item>
            </el-sub-menu>
          </template>
        </el-menu>
        <div v-else class="menu-loading">
          <el-skeleton :rows="10" animated />
        </div>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="layout-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/store/auth";
import { ElMessage, ElMessageBox } from "element-plus";
// 导入所有需要的图标组件
import {
  FullScreen,
  UserFilled,
  ArrowDown,
  User,
  Key,
  SwitchButton,
  Odometer,
  List,
  Folder,
  Monitor,
  KeyFilled,
  Document,
  DataAnalysis,
  Setting,
  OfficeBuilding,
} from "@element-plus/icons-vue";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

// 加载状态
const isLoading = ref(true);

// 初始化认证状态
onMounted(async () => {
  try {
    await authStore.initAuth();
  } catch (error) {
    console.error("Failed to initialize auth:", error);
    // 如果认证初始化失败，清除认证信息
    authStore.clearAuth();
  } finally {
    isLoading.value = false;
  }
});

const isCollapse = ref(false);
const userAvatar = ref("");

const activeMenu = computed(() => {
  return route.path;
});

const menuRoutes = computed(() => {
  // 获取主路由的所有子路由
  const mainRoute = router.getRoutes().find((route) => route.path === "/");
  if (!mainRoute || !mainRoute.children) {
    return [];
  }

  // 过滤出有标题且有权限的顶层路由
  const filteredRoutes = mainRoute.children.filter((route) => {
    // 路由必须有标题
    if (!route.meta?.title) {
      return false;
    }

    // 隐藏的路由不显示在菜单
    if (route.meta?.hidden) {
      return false;
    }

    // 检查管理员权限
    if (route.meta?.adminOnly && !authStore.isAdmin) {
      return false;
    }

    return true;
  });

  return filteredRoutes;
});

// 过滤隐藏的子路由
const getVisibleChildren = (children) => {
  return children.filter((child) => !child.meta?.hidden);
};

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen();
  } else {
    document.exitFullscreen();
  }
};

const handleUserCommand = async (command) => {
  switch (command) {
    case "profile":
      router.push("/settings");
      break;
    case "password":
      // 打开修改密码对话框
      break;
    case "logout":
      try {
        await ElMessageBox.confirm("确定要退出登录吗？", "提示", {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
        });
        await authStore.logout();
        router.push("/login");
        ElMessage.success("已退出登录");
      } catch (error) {
        // 用户取消
      }
      break;
  }
};
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.layout-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0;
}

.header-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.logo-section {
  display: flex;
  align-items: center;
}

.logo {
  width: 32px;
  height: 32px;
  margin-right: 12px;
}

.system-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background-color: #f5f5f5;
}

.username {
  margin: 0 8px;
  font-size: 14px;
}

.dropdown-icon {
  font-size: 12px;
}

.layout-aside {
  background-color: #304156;
  transition: width 0.3s;
}

.layout-aside .el-menu {
  border-right: none;
}

.layout-main {
  background-color: #f5f5f5;
  padding: 20px;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
