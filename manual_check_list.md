# 任务日志不显示 - 手动检查清单

## 问题现状
任务详情页面只显示"INFO"，没有显示具体的日志内容。

## 检查清单

### 步骤1：运行诊断脚本

```bash
cd D:\delvelop_project\ai_project\diskbench_pro2\diskbench_pro2\backend
python diagnose_log_system.py
```

查看诊断结果，确认所有项都是 ✓。

### 步骤2：重启后端服务

**必须完全停止旧进程**：

1. 如果后端在终端运行，按 `Ctrl+C` 停止
2. 或者在任务管理器中找到并结束 `python.exe` 进程
3. 确认端口5003已释放

**启动新服务**：
```bash
cd D:\delvelop_project\ai_project\diskbench_pro2\diskbench_pro2\backend
python application.py
```

**期望看到**：
```
 * Running on http://0.0.0.0:5003
```

### 步骤3：检查浏览器Console

1. 打开任务详情页面
2. 按 `F12` 打开开发者工具
3. 切换到 `Console` 标签

**期望看到**：
```javascript
WebSocket连接成功
```

**如果看到错误**：
- `WebSocket connection failed` - 后端未运行或端口错误
- `CORS error` - CORS配置问题

### 步骤4：检查WebSocket连接状态

在 `F12` → `Network` 标签：
1. 刷新页面
2. 筛选 `WS` (WebSocket)
3. 应该看到一个到 `localhost:5003` 的WebSocket连接
4. 状态应该是 `101 Switching Protocols` (成功)

### 步骤5：检查是否加入任务房间

在浏览器Console中查看：
```javascript
// 应该看到类似输出
加入任务房间响应: {message: "已加入任务 X 的日志房间"}
```

### 步骤6：启动测试任务

1. 点击任务详情页面的 "开始任务" 按钮
2. 同时观察：
   - **浏览器Console** - 查看是否收到日志
   - **后端终端** - 查看是否发送日志

### 步骤7：检查后端日志输出

启动任务后，后端应该输出：

```
INFO: -----------开始执行任务: task_id=X, execution_id=Y------------
INFO: 准备发送日志到任务 X: message=任务开始, global_socketio=True
INFO: 已发送日志到任务 X 的房间
INFO: 准备发送日志到任务 X: message=节点 192.168.1.100 - 上传工具阶段, global_socketio=True
INFO: 已发送日志到任务 X 的房间
```

**如果看到 `global_socketio=False`**：
- SocketIO未正确初始化
- 检查application.py中的注册代码

**如果没有看到这些日志**：
- 任务没有真正启动
- send_task_log函数未被调用

### 步骤8：检查浏览器收到的数据

在浏览器Console中应该看到：

```javascript
收到任务日志: {data: {timestamp: "...", level: "INFO", message: "任务开始", context: {...}}}
添加结构化日志: {timestamp: "...", level: "INFO", message: "任务开始", ...}
```

### 步骤9：手动测试前端显示

在浏览器Console中运行：

```javascript
// 手动添加一条测试日志
logs.value.push({
  id: Date.now(),
  timestamp: new Date().toLocaleString(),
  level: 'INFO',
  module: 'test',
  message: '这是一条测试日志',
  context: {}
});
```

**如果这条能显示**：
- 前端显示逻辑正常
- 问题在WebSocket接收

**如果这条也不显示**：
- 前端显示逻辑有问题
- 检查日志过滤器设置

### 步骤10：使用测试脚本验证

```bash
cd D:\delvelop_project\ai_project\diskbench_pro2\diskbench_pro2\backend
python test_real_time_log.py
```

这个脚本会：
1. 启动一个测试服务器
2. 让你输入任务ID
3. 向该任务发送测试日志
4. 你可以在前端查看是否收到

## 常见问题排查

### 问题A：WebSocket连接失败

**症状**：浏览器Console显示连接错误

**检查**：
```bash
# Windows
netstat -ano | findstr :5003

# 应该看到
TCP    0.0.0.0:5003           0.0.0.0:0              LISTENING       [PID]
```

**解决**：
- 确认后端在5003端口运行
- 检查防火墙设置
- 尝试重启后端

### 问题B：后端没有发送日志

**症状**：后端日志中没有"已发送日志到任务 X 的房间"

**检查**：
1. 任务是否真的启动了
2. send_task_log是否被调用
3. global_socketio是否为None

**解决**：
- 运行诊断脚本检查配置
- 添加print调试语句确认代码执行

### 问题C：前端收不到日志

**症状**：后端发送了，前端Console没有"收到任务日志"

**检查**：
1. WebSocket是否连接成功
2. 是否加入了任务房间
3. 任务ID是否匹配

**解决**：
- 在浏览器Console查看socket.value.connected
- 检查task_id是否正确
- 重新刷新页面重建连接

### 问题D：前端收到了但不显示

**症状**：Console显示"添加结构化日志"，但界面不显示

**检查**：
```javascript
// 在Console中运行
console.log("日志数量:", logs.value.length);
console.log("过滤后的日志:", filteredLogs.value.length);
console.log("日志过滤器:", logFilter);
```

**解决**：
- 检查日志级别过滤器
- 检查关键词过滤器
- 点击"清空"按钮重置过滤器

## 快速验证流程

1. ✅ 运行诊断脚本 - 确认配置正确
2. ✅ 重启后端 - 确保新代码生效
3. ✅ 打开任务详情 - 查看WebSocket连接
4. ✅ 启动任务 - 观察日志输出
5. ✅ 检查Console - 确认收到数据
6. ✅ 查看日志面板 - 验证显示

## 如果所有步骤都正常但仍然不显示

请收集以下信息：

1. **后端日志**（从启动到运行任务的完整日志）
2. **浏览器Console截图**（包括WebSocket连接和日志接收）
3. **Network标签截图**（WebSocket连接状态）
4. **诊断脚本输出**

然后我可以进一步分析问题。

## 相关文件

- `diagnose_log_system.py` - 配置诊断脚本
- `test_real_time_log.py` - 实时测试脚本
- `task_log_troubleshooting_guide.md` - 详细排查指南
- `task_stage_display_summary.md` - 当前实现说明
