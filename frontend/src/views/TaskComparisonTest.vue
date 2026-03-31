<template>
  <div class="task-comparison-container">
    <h1>任务对比测试页面</h1>
    <p>如果您看到这个，说明页面可以正常加载</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const testData = ref('测试')
</script>

<style scoped>
.task-comparison-container {
  padding: 20px;
}
</style>
