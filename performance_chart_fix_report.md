# 性能图表修复报告

## 问题描述
性能图表（IOSTAT性能图表和IO抖动图表）无法选择节点和设备，下拉框为空。

## 根本原因
IOStatChart.vue文件缺少必要的API函数导入：
- 使用了`getTaskLogs()`和`getIOStatMetrics()`函数
- 但没有从`@/api/logs`导入这些函数
- 导致这些函数在运行时为undefined
- `taskNodes.value`无法被正确赋值，节点下拉框为空

## 修复内容

### 文件: frontend/src/views/IOStatChart.vue
**修改位置**: 第66-70行

**修改前**:
```javascript
<script setup>
import { ref, onMounted, onUnmounted, reactive } from "vue";
import { useRouter, useRoute } from "vue-router";
import * as echarts from "echarts";
import tasksApi from "@/api/tasks";
```

**修改后**:
```javascript
<script setup>
import { ref, onMounted, onUnmounted, reactive } from "vue";
import { useRouter, useRoute } from "vue-router";
import * as echarts from "echarts";
import tasksApi from "@/api/tasks";
import { getTaskLogs, getIOStatMetrics } from "@/api/logs";
```

### 文件: frontend/src/views/IOJitterChart.vue
**说明**: 此文件在之前已修复，使用了正确的导入语句：
```javascript
import tasksApi from "@/api/tasks";
import {
  getTaskLogs,
  getIOStatMetrics,
  getJitterData,
  getIOStatJitter,
} from "@/api/logs";
```

## 修复步骤
1. 检查IOStatChart.vue的导入语句
2. 添加缺失的logs API导入
3. 重新构建前端项目 (`npm run build`)
4. 构建成功，无错误

## 预期效果
修复后，性能图表页面应该能够：
1. ✅ 正常加载任务的节点列表
2. ✅ 在节点下拉框中显示所有节点
3. ✅ 选择节点后加载对应的设备列表
4. ✅ 在设备下拉框中显示所有设备
5. ✅ 选择设备和指标后正常渲染图表

## 测试建议
1. 访问任务详情页面，点击"查看IOSTAT性能图表"或"查看性能抖动图表"
2. 验证节点下拉框是否显示节点列表
3. 选择一个节点
4. 验证设备下拉框是否显示设备列表
5. 选择设备和指标
6. 验证图表是否正确渲染

## 构建结果
- ✅ 构建成功
- ⚠️  54个prettier格式警告（不影响功能）
- ⚠️  部分资源文件超过推荐大小（不影响功能）

## 相关文件
- frontend/src/views/IOStatChart.vue
- frontend/src/views/IOJitterChart.vue
- frontend/src/api/logs.js
- frontend/src/api/tasks.js

## 修复时间
2026-03-23

## 状态
✅ 已修复并构建完成，等待用户测试验证
