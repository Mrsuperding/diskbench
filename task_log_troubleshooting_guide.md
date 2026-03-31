# 任务日志不显示问题排查指南

## 问题描述

任务详情页面只显示"INFO"，没有显示任何日志内容。

## 可能的原因

### 1. WebSocket连接问题

**检查步骤**：

1. 打开浏览器开发者工具（F12）
2. 切换到"Console"标签
3. 查找以下日志：
   - `WebSocket连接成功` - 表示连接已建立
   - `收到任务日志: {...}` - 表示接收到日志数据

**期望看到**：
```javascript
WebSocket连接成功
收到任务日志: {data: {timestamp: "...", level: "INFO", message: "⏳ 任务开始：xxx", ...}}
添加结构化日志: {timestamp: "...", level: "INFO", message: "⏳ 任务开始：xxx", ...}
```

**如果没有看到**：
- WebSocket连接失败：检查后端是否正常运行，端口5003是否开放
- 没有收到任务日志：后端没有发送日志，需要检查后端

### 2. 后端没有正常发送日志

**检查步骤**：

1. 查看后端控制台输出
2. 查找以下日志：
   - `-----------开始执行任务: task_id=X, execution_id=Y------------`
   - `已发送日志到任务 X 的房间`

**期望看到**：
```
INFO: -----------开始执行任务: task_id=56, execution_id=1------------
INFO: 已发送日志到任务 56 的房间
INFO: 已发送日志到任务 56 的房间
INFO: 已发送日志到任务 56 的房间
```

**如果没有看到"已发送日志"**：
- `global_socketio` 未初始化
- `send_task_log` 函数执行失败

### 3. 任务未正常启动

**检查步骤**：

1. 点击"开始任务"按钮后，查看网络请求
2. F12 → Network标签
3. 查找 `/api/tasks/run/{task_id}` 请求

**期望响应**：
```json
{
  "success": true,
  "message": "任务已开始执行"
}
```

**如果失败**：
- 查看响应错误信息
- 检查任务是否配置正确（节点、IO用例）

### 4. 后端未重启

**问题**：修改代码后没有重启后端服务

**解决方案**：
```bash
cd backend
# 停止旧进程（按Ctrl+C或关闭终端窗口）
python application.py
```

## 排查步骤（按顺序）

### 步骤1：检查后端是否正常运行

```bash
cd D:\delvelop_project\ai_project\diskbench_pro2\diskbench_pro2\backend
python application.py
```

**期望输出**：
```
 * Running on http://0.0.0.0:5003
 * Restarting with stat
```

### 步骤2：检查WebSocket是否初始化

在后端启动日志中查找：
```
INFO: SocketIO initialized successfully
```

如果没有看到，检查`application.py`中是否有：
```python
socketio = SocketIO(app, cors_allowed_origins="*")
from app.views.socket_events import register_socket_events
register_socket_events(socketio)
```

### 步骤3：测试任务日志发送

运行测试脚本：
```bash
cd D:\delvelop_project\ai_project\diskbench_pro2\diskbench_pro2\backend
python test_task_log.py
```

**期望输出**：
```
测试发送任务日志...
发送任务开始日志...
发送节点准备日志...
发送工具上传日志...
发送完成日志...
测试完成！
```

### 步骤4：检查前端WebSocket连接

1. 打开任务详情页面
2. F12 → Console
3. 查找：
   ```
   WebSocket连接成功
   ```

4. 如果看到连接错误：
   ```
   WebSocket connection failed
   ```
   检查后端地址配置（应该是`http://localhost:5003`）

### 步骤5：启动任务并观察

1. 点击"开始任务"
2. 同时观察：
   - **浏览器Console**：查看是否收到WebSocket消息
   - **后端日志**：查看是否发送日志

### 步骤6：检查任务房间

在后端日志中查找：
```
INFO: 客户端加入任务 X 的日志房间: sid=xxx
```

如果没有看到，说明前端没有加入任务房间。

## 常见问题和解决方案

### 问题1：后端日志中有"全局socketio对象未初始化"

**原因**：SocketIO未正确注册

**解决方案**：
确保`application.py`中正确调用了`register_socket_events`：
```python
from app.views.socket_events import register_socket_events
register_socket_events(socketio)
```

### 问题2：前端控制台没有"WebSocket连接成功"

**原因**：WebSocket连接失败

**解决方案**：
1. 检查后端是否在5003端口运行
2. 检查`frontend/src/main.js`中的WebSocket地址配置
3. 检查CORS配置

### 问题3：后端日志中没有"已发送日志到任务 X 的房间"

**原因**：
- `send_task_log`未被调用
- `global_socketio`为None

**解决方案**：
1. 添加调试日志：
```python
def send_task_log(task_id, log_content, level='INFO', module='tasks', context=None):
    print(f"DEBUG: send_task_log called, task_id={task_id}, global_socketio={global_socketio}")
    # ... 原有代码
```

2. 重启后端并查看调试输出

### 问题4：只显示"INFO"，没有具体内容

**可能原因**：
- 前端日志解析错误
- 日志格式不正确

**解决方案**：
在浏览器Console中执行：
```javascript
console.log("当前日志数量:", logs.value.length);
console.log("日志内容:", logs.value);
```

查看是否有日志数据，以及日志格式是否正确。

## 快速验证脚本

在浏览器Console中运行：
```javascript
// 测试手动添加日志
logs.value.push({
  id: Date.now(),
  timestamp: new Date().toLocaleString(),
  level: 'INFO',
  module: 'test',
  message: '⏳ 这是一条测试日志',
  context: {}
});
```

如果这条日志能显示，说明前端显示逻辑正常，问题在于WebSocket接收。

## 修复总结

已修改的文件：
1. `backend/app/views/tasks.py` - 添加了`send_task_log`导入和调用
2. `backend/app/utils/task_executor.py` - 优化了所有日志消息

需要做的事情：
1. ✅ 重启后端服务
2. 📝 检查WebSocket连接
3. 📝 启动测试任务验证

## 联系点

如果以上步骤都检查了还是不行，请提供：
1. 浏览器Console的完整输出（截图）
2. 后端启动后的日志输出（文本）
3. 点击"开始任务"后的后端日志（文本）
4. Network标签中的WebSocket连接状态（截图）
