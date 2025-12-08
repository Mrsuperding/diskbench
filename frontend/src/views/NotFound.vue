<template>
  <div class="not-found-container">
    <h1>404</h1>
    <h2>页面未找到</h2>
    <el-button type="primary" @click="goHome">返回首页</el-button>
  </div>
</template>

<script>
export default {
  name: "NotFound",
  methods: {
    goHome() {
      this.$router.push("/");
    },
  },
};
</script>

<style scoped>
.not-found-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  text-align: center;
}

h1 {
  font-size: 8rem;
  margin: 0;
  color: #409eff;
}

h2 {
  font-size: 2rem;
  margin: 1rem 0;
  color: #606266;
}
</style>
