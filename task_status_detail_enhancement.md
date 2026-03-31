# 任务实时运行状态详细显示增强

## 修改概述

增强任务详情页面的"任务实时运行状态"显示，让用户清楚地看到任务执行的每个阶段，包括：
- 哪些节点正在上传工具
- 哪些节点在执行初始化
- 正在执行哪个IO模型
- 在哪个分区上执行
- 收集日志的进度
- 任务完成和资源回收

## 增强内容

### 1. 任务开始阶段

**显示内容：**
```
【任务开始】任务开始：准备在 2 个节点上执行 3 个IO模型
  节点: test-node(192.168.1.100), prod-node(192.168.1.101)
  IO模型: 4k_randread, 4k_randwrite, 4k_mixed
```

**发送的日志：**
```python
send_task_log(task_id,
    f"任务开始：准备在 {len(nodes)} 个节点上执行 {len(io_test_cases)} 个IO模型",
    level='INFO',
    context={
        'operation': 'task_start',
        'stage': '任务开始',
        'nodes': ['test-node(192.168.1.100)', 'prod-node(192.168.1.101)'],
        'io_models': ['4k_randread', '4k_randwrite', '4k_mixed'],
        'node_count': 2,
        'io_case_count': 3
    })
```

### 2. 上传工具阶段

**显示内容：**
```
【上传工具阶段】节点 192.168.1.100 - 上传工具阶段：开始上传FIO工具
【检测分区】节点 192.168.1.100 - 检测到IO分区：/dev/vdb, /dev/vdc
【上传工具阶段】节点 192.168.1.100 - 上传工具阶段：正在上传FIO工具（架构: x86_64）
【上传工具阶段】节点 192.168.1.100 - 上传工具阶段：FIO工具上传完成
```

**发送的日志：**
```python
# 开始上传
send_task_log(task_id,
    f"节点 {node.ip_address} - 上传工具阶段：开始上传FIO工具",
    context={'operation': 'upload_tool', 'stage': '上传工具阶段'})

# 检测分区
send_task_log(task_id,
    f"节点 {node.ip_address} - 检测到IO分区：{partition_info}",
    context={'partitions': ['/dev/vdb', '/dev/vdc'], 'stage': '检测分区'})

# 上传中
send_task_log(task_id,
    f"节点 {node.ip_address} - 上传工具阶段：正在上传FIO工具（架构: {architecture}）",
    context={'architecture': 'x86_64', 'stage': '上传工具阶段'})

# 上传完成
send_task_log(task_id,
    f"节点 {node.ip_address} - 上传工具阶段：FIO工具上传完成",
    context={'operation': 'upload_complete', 'stage': '上传工具阶段'})
```

### 3. 执行IO模型阶段

**显示内容：**
```
【执行IO模型】节点 192.168.1.100 - 执行IO模型：4k_randread（分区: /dev/vdb）
  分区: /dev/vdb
【收集日志阶段】节点 192.168.1.100 - 收集日志阶段：开始收集iostat性能数据
【收集日志阶段】节点 192.168.1.100 - 收集日志阶段：iostat后台监控已启动
【执行IO模型】节点 192.168.1.100 - 执行IO模型：正在运行FIO测试（4k_randread）
```

**发送的日志：**
```python
# 开始执行IO模型
send_task_log(task_id,
    f"节点 {node.ip_address} - 执行IO模型：{io_test_case.name}（分区: {partition_str}）",
    context={
        'io_model': '4k_randread',
        'partition': '/dev/vdb',
        'stage': '执行IO模型'
    })

# 开始收集日志
send_task_log(task_id,
    f"节点 {node.ip_address} - 收集日志阶段：开始收集iostat性能数据",
    context={'stage': '收集日志阶段'})

# iostat启动
send_task_log(task_id,
    f"节点 {node.ip_address} - 收集日志阶段：iostat后台监控已启动",
    context={'iostat_log': '/tmp/iostat_xxx.log', 'stage': '收集日志阶段'})

# 正在运行FIO
send_task_log(task_id,
    f"节点 {node.ip_address} - 执行IO模型：正在运行FIO测试（{io_test_case.name}）",
    context={'io_model': '4k_randread', 'stage': '执行IO模型'})
```

### 4. 收集结果阶段

**显示内容：**
```
【收集日志阶段】节点 192.168.1.100 - 收集日志阶段：停止iostat监控，开始解析数据
【执行完成】节点 192.168.1.100 - IO模型执行成功：4k_randread
【保存结果】节点 192.168.1.100 - 保存测试结果到数据库
```

**发送的日志：**
```python
# 停止iostat
send_task_log(task_id,
    f"节点 {node.ip_address} - 收集日志阶段：停止iostat监控，开始解析数据",
    context={'stage': '收集日志阶段'})

# 执行成功
send_task_log(task_id,
    f"节点 {node.ip_address} - IO模型执行成功：{io_test_case.name}",
    context={'io_model': '4k_randread', 'stage': '执行完成'})

# 保存结果
send_task_log(task_id,
    f"节点 {node.ip_address} - 保存测试结果到数据库",
    context={'stage': '保存结果'})
```

### 5. 任务完成阶段

**显示内容：**
```
【任务完成】任务完成：共测试 2 个节点，执行 3 个IO模型，耗时 120 秒
  节点: test-node(192.168.1.100), prod-node(192.168.1.101)
  IO模型: 4k_randread, 4k_randwrite, 4k_mixed
  耗时: 120秒
【资源回收】终止任务：回收线程资源和清理临时文件
```

**发送的日志：**
```python
# 任务完成
send_task_log(task_id,
    f"任务完成：共测试 {node_count} 个节点，执行 {io_case_count} 个IO模型，耗时 {execution.duration} 秒",
    context={
        'operation': 'task_completed',
        'stage': '任务完成',
        'duration': 120,
        'node_count': 2,
        'io_case_count': 3
    })

# 资源回收
send_task_log(task_id,
    f"终止任务：回收线程资源和清理临时文件",
    context={'operation': 'cleanup_resources', 'stage': '资源回收'})
```

## 前端显示增强

### 1. 结构化显示

**原有显示（简单）：**
```
20:00:00  节点 192.168.1.100 - 上传工具阶段
```

**新的显示（详细）：**
```
┌────────────────────────────────────────────────┐
│ 20:00:00  【上传工具阶段】                      │
│ 节点 192.168.1.100 - 上传工具阶段：开始上传FIO工具 │
│   架构: x86_64                                  │
└────────────────────────────────────────────────┘
```

### 2. 颜色标识

- **蓝色边框** - 当前正在执行的操作
- **红色边框** - 失败的操作
- **橙色边框** - 警告信息
- **灰色边框** - 已完成的操作

### 3. 详细信息展开

操作历史条目包含两部分：
1. **主要信息**：时间、阶段、消息
2. **详细信息**：节点列表、IO模型、分区、耗时等

```vue
<div class="history-item">
  <!-- 主要信息 -->
  <div class="history-main">
    <span class="history-time">20:00:00</span>
    <span class="history-stage">【任务开始】</span>
    <span class="history-text">任务开始：准备在 2 个节点上执行 3 个IO模型</span>
  </div>

  <!-- 详细信息 -->
  <div class="history-details">
    <span class="detail-item">节点: test-node(192.168.1.100), prod-node(192.168.1.101)</span>
    <span class="detail-item">IO模型: 4k_randread, 4k_randwrite, 4k_mixed</span>
  </div>
</div>
```

## 修改的文件

### 后端

1. **backend/app/utils/task_executor.py**
   - 第555-609行：增强上传工具阶段日志
   - 第110-130行：增强IO模型执行阶段日志
   - 第143-170行：增强收集日志阶段日志
   - 第185-194行：增强结果保存日志

2. **backend/app/views/tasks.py**
   - 第119-127行：增强任务开始日志
   - 第178-186行：增强任务完成日志
   - 第213-216行：增强资源回收日志

### 前端

1. **frontend/src/views/TaskDetail.vue**
   - 第262-296行：重构操作历史显示结构
   - 第1844-1910行：增强CSS样式

## 界面效果对比

### 优化前

```
暂无操作记录
```

或者只显示简单的文本：
```
20:00:00  任务开始
20:00:01  节点 192.168.1.100 - 上传工具阶段
20:00:05  节点 192.168.1.100 - 执行IO模型：4k_randread
```

### 优化后

```
┌─────────────────────────────────────────────────────────┐
│ 任务实时运行状态                                         │
├─────────────────────────────────────────────────────────┤
│ 🔄 正在运行                                              │
│                                                         │
│ 当前操作：                                               │
│ 节点 192.168.1.100 - 执行IO模型：正在运行FIO测试（4k_randread） │
│                                                         │
│ 操作历史：                                               │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 20:00:00 【任务开始】                                │ │
│ │ 任务开始：准备在 2 个节点上执行 3 个IO模型            │ │
│ │   节点: test-node(192.168.1.100), prod-node(...)    │ │
│ │   IO模型: 4k_randread, 4k_randwrite, 4k_mixed       │ │
│ │                                                     │ │
│ │ 20:00:01 【上传工具阶段】                            │ │
│ │ 节点 192.168.1.100 - 上传工具阶段：开始上传FIO工具  │ │
│ │                                                     │ │
│ │ 20:00:02 【检测分区】                                │ │
│ │ 节点 192.168.1.100 - 检测到IO分区：/dev/vdb, /dev/vdc│ │
│ │   分区: /dev/vdb, /dev/vdc                          │ │
│ │                                                     │ │
│ │ 20:00:03 【上传工具阶段】                            │ │
│ │ 节点 192.168.1.100 - 上传工具阶段：正在上传FIO工具   │ │
│ │   架构: x86_64                                      │ │
│ │                                                     │ │
│ │ 20:00:05 【执行IO模型】                              │ │
│ │ 节点 192.168.1.100 - 执行IO模型：4k_randread        │ │
│ │   分区: /dev/vdb                                    │ │
│ │                                                     │ │
│ │ 20:00:06 【收集日志阶段】（蓝色高亮，当前进行中）     │ │
│ │ 节点 192.168.1.100 - 收集日志阶段：iostat后台监控启动 │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 数据流

### 完整执行流程

```
1. 任务开始
   ↓ send_task_log("任务开始：准备在 N 个节点...")

2. 对每个节点：
   ↓ send_task_log("节点 X - 上传工具阶段：开始上传...")
   ↓ send_task_log("节点 X - 检测到IO分区：...")
   ↓ send_task_log("节点 X - 上传工具阶段：正在上传...")
   ↓ send_task_log("节点 X - 上传工具阶段：上传完成")

3. 对每个IO模型：
   ↓ send_task_log("节点 X - 执行IO模型：模型名（分区：...）")
   ↓ send_task_log("节点 X - 收集日志阶段：开始收集...")
   ↓ send_task_log("节点 X - 收集日志阶段：iostat启动")
   ↓ send_task_log("节点 X - 执行IO模型：正在运行FIO测试...")
   ↓ FIO测试运行中...
   ↓ send_task_log("节点 X - 收集日志阶段：停止iostat...")
   ↓ send_task_log("节点 X - IO模型执行成功")
   ↓ send_task_log("节点 X - 保存测试结果到数据库")

4. 任务完成
   ↓ send_task_log("任务完成：共测试 N 个节点...")
   ↓ send_task_log("终止任务：回收线程资源...")
```

### WebSocket传输格式

```javascript
{
  data: {
    timestamp: "2026-03-24T20:00:00",
    level: "INFO",
    message: "节点 192.168.1.100 - 执行IO模型：4k_randread（分区: /dev/vdb）",
    context: {
      node_id: 16,
      node_ip: "192.168.1.100",
      io_test_case_id: 2,
      io_model: "4k_randread",
      partition: "/dev/vdb",
      operation: "execute_io_model",
      stage: "执行IO模型",
      progress: "start"
    }
  }
}
```

### 前端处理逻辑

```javascript
socket.value.on("task_log", (data) => {
  const logData = data.data;

  // 更新当前操作
  currentOperation.value = logData.message;

  // 添加到操作历史
  operationHistory.value.push({
    timestamp: logData.timestamp,
    message: logData.message,
    level: logData.level,
    context: logData.context  // 包含详细信息
  });

  // 限制历史记录数量
  if (operationHistory.value.length > 20) {
    operationHistory.value.shift();
  }
});
```

## 用户体验提升

### 优化前的问题

1. ❌ 操作历史为空，用户不知道任务在做什么
2. ❌ 看不到执行进度
3. ❌ 不知道在哪个节点执行
4. ❌ 不知道执行哪个IO模型
5. ❌ 看不到分区信息

### 优化后的效果

1. ✅ 清楚显示每个执行阶段
2. ✅ 实时看到当前操作
3. ✅ 显示节点IP和名称
4. ✅ 显示IO模型名称
5. ✅ 显示测试分区
6. ✅ 显示任务耗时
7. ✅ 颜色区分不同状态
8. ✅ 详细信息可展开查看

## 部署步骤

### 1. 重启后端

```bash
# 停止旧服务
taskkill /F /PID <backend_pid>

# 启动新服务
cd D:\delvelop_project\ai_project\diskbench_pro2\diskbench_pro2\backend
python application.py
```

### 2. 前端已构建

前端已经重新构建完成，刷新浏览器即可。

### 3. 测试验证

1. 创建一个新任务
2. 执行任务
3. 打开任务详情页面
4. 观察"任务实时运行状态"面板
5. 应该看到详细的执行日志

## 验证清单

- [ ] 任务开始时显示节点列表和IO模型列表
- [ ] 上传工具阶段显示架构信息
- [ ] 检测分区阶段显示所有分区
- [ ] 执行IO模型时显示模型名称和分区
- [ ] 收集日志阶段显示iostat启动信息
- [ ] 任务完成显示统计信息（节点数、IO模型数、耗时）
- [ ] 资源回收显示清理信息
- [ ] 错误日志显示红色标签
- [ ] 警告日志显示橙色标签
- [ ] 当前操作高亮显示

## 故障排查

### 问题1：操作历史仍然为空

**可能原因：**
- 后端未重启
- WebSocket连接失败
- send_task_log 未被调用

**解决方法：**
```bash
# 1. 确认后端进程
netstat -ano | grep :5003

# 2. 查看后端日志
tail -f /tmp/backend_new.log

# 3. 检查浏览器Console
按F12查看是否有"收到任务日志"输出
```

### 问题2：显示的信息不够详细

**可能原因：**
- context 信息未正确传递
- 前端解析有问题

**解决方法：**
```javascript
// 在浏览器Console查看
console.log("操作历史:", operationHistory.value);
console.log("最新日志:", operationHistory.value[operationHistory.value.length - 1]);
```

### 问题3：样式显示异常

**可能原因：**
- 浏览器缓存
- CSS未正确加载

**解决方法：**
- 按 Ctrl+F5 强制刷新
- 清除浏览器缓存

## 总结

这次增强让任务实时运行状态从"空白"变成"详细可见"：

- ✅ 显示完整的执行流程
- ✅ 显示节点、分区、IO模型等关键信息
- ✅ 实时更新当前操作
- ✅ 保留最近20条操作历史
- ✅ 使用颜色和标签区分不同状态
- ✅ 结构化展示详细信息

用户现在可以清楚地看到：
- 任务在做什么
- 在哪个节点上做
- 对哪个分区操作
- 执行哪个IO模型
- 当前处于什么阶段
- 任务完成情况和耗时

## 相关文档

- `task_status_display_implementation.md` - 任务状态显示实现
- `full_stack_performance_optimization_summary.md` - 全栈性能优化总结
