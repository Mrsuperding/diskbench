# 节点监控图表可视化增强

## 功能概述

为节点监控页面添加了图表视图功能，用户可以在表格视图和图表视图之间切换，并选择要观察的监控指标，以更直观的方式查看节点性能数据。

## 主要改进

### 1. 双视图模式

**表格视图（默认）**
- 保留原有的表格展示方式
- 显示所有节点的实时监控数据
- 包含详细的数值和状态信息

**图表视图（新增）**
- 使用 ECharts 柱状图展示数据
- 横向对比多个节点的指标
- 可视化程度更高，趋势更明显

### 2. 指标选择器

用户可以自由选择要查看的监控指标：

- ✅ **CPU使用率** - 显示百分比，根据使用率着色（绿色/橙色/红色）
- ✅ **内存使用率** - 显示百分比，根据使用率着色
- ✅ **磁盘使用率** - 显示百分比，根据使用率着色
- ✅ **网络上行** - 显示 MB/s，实时上行流量
- ✅ **网络下行** - 显示 MB/s，实时下行流量
- ✅ **系统负载** - 显示1分钟平均负载

### 3. 智能配色方案

根据指标数值自动调整颜色：
- **绿色 (#409EFF)**: 正常范围 (0-70%)
- **橙色 (#E6A23C)**: 警告范围 (70-90%)
- **红色 (#F56C6C)**: 危险范围 (90-100%)

### 4. 响应式布局

- 图表采用 2 列布局
- 每个图表高度 350px
- 自动适应容器大小变化
- 支持图表自动缩放

## 技术实现

### 使用的技术栈

```javascript
// ECharts 相关
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart, BarChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from "echarts/components";
```

### 核心功能

1. **视图切换**
   ```vue
   <el-radio-group v-model="viewMode" size="large">
     <el-radio-button label="table">表格视图</el-radio-button>
     <el-radio-button label="chart">图表视图</el-radio-button>
   </el-radio-group>
   ```

2. **指标选择**
   ```vue
   <el-checkbox-group v-model="selectedMetrics">
     <el-checkbox label="cpu_usage">CPU使用率</el-checkbox>
     <el-checkbox label="memory_usage">内存使用率</el-checkbox>
     <!-- 更多指标... -->
   </el-checkbox-group>
   ```

3. **动态图表生成**
   ```javascript
   const getChartOption = (metric) => {
     // 根据指标类型动态生成 ECharts 配置
     // 自动处理数据格式化
     // 智能配色方案
   }
   ```

## 用户体验改进

### 优势

1. **直观对比** - 柱状图可以快速对比多个节点的性能差异
2. **灵活定制** - 用户可以只关注需要的指标
3. **视觉突出** - 颜色编码帮助快速识别问题节点
4. **数据密度** - 图表视图可以在屏幕上展示更多信息

### 使用场景

- **性能巡检**: 快速扫描所有节点状态，找出性能瓶颈
- **容量规划**: 通过可视化了解资源使用情况
- **故障排查**: 对比异常节点和正常节点的指标差异
- **报告展示**: 导出图表用于性能报告

## 保留功能

所有原有功能均得到保留：

- ✅ 概览统计卡片（总节点数、活跃节点、离线节点、异常节点）
- ✅ 自动刷新功能（手动/30秒/1分钟/5分钟）
- ✅ 实时数据更新
- ✅ 节点详情查看
- ✅ 导航面包屑

## 下一步优化建议

1. **历史趋势图** - 显示指标的时间序列变化
2. **对比模式** - 选择多个节点进行详细对比
3. **告警阈值线** - 在图表上显示告警阈值
4. **图表导出** - 支持导出为图片或 PDF
5. **实时推送** - 使用 WebSocket 实现数据实时更新

## 测试检查清单

- [ ] 视图切换功能正常
- [ ] 指标选择器工作正常
- [ ] 图表数据准确显示
- [ ] 颜色方案正确应用
- [ ] 自动刷新在图表模式下工作
- [ ] 响应式布局适配不同屏幕
- [ ] 无指标选中时显示空状态提示

## 文件修改

### 修改的文件
- `frontend/src/views/NodeMonitoring.vue` - 添加图表视图和指标选择功能

### 依赖项
- 已存在于 package.json：
  - `echarts: ^5.4.3`
  - `vue-echarts: ^6.6.1`

## 部署说明

1. 确保前端依赖已安装：
   ```bash
   cd frontend
   npm install
   ```

2. 启动开发服务器测试：
   ```bash
   npm run serve
   ```

3. 生产环境构建：
   ```bash
   npm run build
   ```

## 效果展示

### 表格视图
- 传统表格展示
- 详细数值信息
- 进度条可视化

### 图表视图
- 2x3 网格布局（最多6个指标）
- 柱状图对比
- 智能配色提示
- 标签值显示

---

**创建时间**: 2026-03-26
**修改人**: Claude
**版本**: v1.0
