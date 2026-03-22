# IO图表API导入和WebSocket端口修复报告

## 修复时间
2026-03-23

## 报告的问题
1. **IO性能抖动图表选择不了节点和设备**
2. **IOSTAT性能图表显示不了数据**

## 根本原因

### 问题1: IOJitterChart.vue - API导入错误

**错误代码**：
```javascript
import { getTask } from "@/api/tasks";
```

**问题**：tasks.js使用的是`export default`，不是命名导出(named export)

**tasks.js实际导出方式**：
```javascript
export default {
  getTasks(params = {}) { ... },
  getTask(taskId) { ... },
  // ...
}
```

### 问题2: IOJitterChart.vue - WebSocket端口错误

**错误代码**：
```javascript
socket.value = io("http://localhost:5002", {
```

**问题**：后端实际运行在5003端口，不是5002端口

**后端配置**：
```python
# backend/application.py
socketio.run(app, debug=True, host='0.0.0.0', port=5003, use_reloader=False)
```

## 修复内容

### 修复1: 修正API导入方式

**文件**：`frontend/src/views/IOJitterChart.vue`

**修改前**：
```javascript
import { getTask } from "@/api/tasks";
```

**修改后**：
```javascript
import tasksApi from "@/api/tasks";
```

**同时更新函数调用**：
```javascript
// 修改前
const response = await getTask(taskId.value);

// 修改后
const response = await tasksApi.getTask(taskId.value);
```

### 修复2: 修正WebSocket端口

**文件**：`frontend/src/views/IOJitterChart.vue`

**修改前**：
```javascript
socket.value = io("http://localhost:5002", {
```

**修改后**：
```javascript
socket.value = io("http://localhost:5003", {
```

## 为什么IOStatChart.vue正常工作

IOStatChart.vue从一开始就使用了正确的导入方式：

```javascript
// IOStatChart.vue (正确)
import tasksApi from "@/api/tasks";

// 调用
const response = await tasksApi.getTask(taskId.value);
```

并且IOStatChart.vue不使用WebSocket，所以不受端口问题影响。

## 相关API导出方式说明

### Default Export (tasks.js)
```javascript
// 导出
export default {
  getTask(taskId) { ... }
}

// 导入
import tasksApi from "@/api/tasks";
tasksApi.getTask(id);
```

### Named Export (logs.js)
```javascript
// 导出
export const getTaskLogs = (taskId, params) => { ... };
export const getIOStatMetrics = (logId, params) => { ... };

// 导入
import { getTaskLogs, getIOStatMetrics } from "@/api/logs";
getTaskLogs(id, params);
```

## 修改的文件

1. **frontend/src/views/IOJitterChart.vue**
   - 修正API导入：`import tasksApi from "@/api/tasks"`
   - 修正函数调用：`await tasksApi.getTask(taskId.value)`
   - 修正WebSocket端口：`io("http://localhost:5003")`

## 构建状态
✅ 前端成功构建
- Build Hash: 73a53d14437c063d
- Build Time: 34219ms
- 无错误，仅有格式警告

## 测试建议

### 1. IO性能抖动图表测试
- [ ] 访问任务详情页面
- [ ] 点击"查看性能抖动图表"
- [ ] **验证节点下拉框显示节点列表**（之前为空）
- [ ] **验证设备下拉框显示设备列表**（之前为空）
- [ ] 选择节点和设备，验证图表显示
- [ ] 检查浏览器控制台，确认没有API错误
- [ ] 检查WebSocket连接状态（应该显示"WebSocket连接成功"）

### 2. IOSTAT性能图表测试
- [ ] 访问任务详情页面
- [ ] 点击"查看IOSTAT性能图表"
- [ ] 验证节点下拉框显示节点列表
- [ ] 验证设备下拉框显示设备列表
- [ ] 选择节点和设备，验证图表显示数据
- [ ] 切换不同指标，验证图表更新

### 3. 控制台日志检查
在浏览器控制台应该能看到：
```
加载任务信息开始，taskId: <任务ID>
加载任务信息成功，response: {...}
任务节点信息: [...]
初始化WebSocket连接，任务ID: <任务ID>
WebSocket连接成功
```

不应该再看到：
```
❌ TypeError: Cannot read properties of undefined (reading 'getTask')
❌ WebSocket connection to 'ws://localhost:5002/' failed
```

## 技术要点

### 1. JavaScript模块导入导出
- **Default Export**: 一个模块只能有一个默认导出
  - 适合导出单个对象或类
  - 导入时可以使用任意名称

- **Named Export**: 一个模块可以有多个命名导出
  - 适合导出多个独立函数
  - 导入时必须使用相同的名称（或使用as重命名）

### 2. API一致性
- tasks.js使用default export，因为它是一个包含多个方法的API对象
- logs.js使用named export，因为每个函数都是独立的
- 导入时必须匹配导出方式

### 3. WebSocket端口配置
- 前端WebSocket连接必须指向后端实际运行的端口
- 后端运行在5003端口（application.py配置）
- 前端也通过nginx代理访问后端API（/api路径）

## 后续建议

### 1. 代码规范
建议统一所有API文件的导出方式：
- 要么全部使用default export
- 要么全部使用named export

### 2. 配置管理
WebSocket端口应该从配置文件读取，而不是硬编码：
```javascript
// 建议创建 config.js
export const API_BASE_URL = 'http://localhost:5003';
export const WS_URL = 'http://localhost:5003';

// 在组件中使用
import { WS_URL } from '@/config';
socket.value = io(WS_URL, { ... });
```

### 3. 类型检查
建议使用TypeScript或JSDoc注释，可以在开发时检测导入错误：
```javascript
/**
 * @typedef {Object} TasksAPI
 * @property {function(number): Promise} getTask
 * @property {function(Object): Promise} getTasks
 */

/** @type {TasksAPI} */
import tasksApi from "@/api/tasks";
```

## 修复状态
✅ 已修复并构建完成

## 相关文档
- 之前的修复：`session_summary_report.md`
- 多节点多设备功能：`multi_node_multi_device_jitter_chart_report.md`
