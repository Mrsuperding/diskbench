# 任务日志显示优化方案

## 问题描述

当前任务详情界面的"日志输出"显示的是后台技术日志（如"开始执行任务"、"查询数据库"等），这些日志对用户来说不够直观。

用户希望看到的是：
- **更清晰的任务执行阶段**
- **对哪些节点执行操作**
- **正在执行的IO模型**
- **操作进度和状态**

## 当前日志示例（不理想）

```
2026-03-23 20:00:00 INFO  开始执行任务: task_id=56, execution_id=1
2026-03-23 20:00:01 INFO  创建应用上下文，开始查询数据库
2026-03-23 20:00:02 INFO  查询任务信息: task_id=56
2026-03-23 20:00:03 INFO  获取到任务信息: task_name=性能测试, status=running
```

## 期望的日志示例（用户友好）

```
2026-03-23 20:00:00 ⏳ 任务开始：性能测试
2026-03-23 20:00:01 📡 节点 192.168.1.100 - 正在上传FIO工具...
2026-03-23 20:00:05 ✅ 节点 192.168.1.100 - FIO工具上传完成
2026-03-23 20:00:06 🔧 节点 192.168.1.100 - 执行IO模型：4k_16d_randread_1n
2026-03-23 20:00:30 📊 节点 192.168.1.100 - 正在收集性能数据...
2026-03-23 20:01:00 ✅ 节点 192.168.1.100 - IO模型执行完成
2026-03-23 20:01:01 🔧 节点 192.168.1.100 - 执行IO模型：4k_32d_randwrite_1n
2026-03-23 20:01:30 📊 节点 192.168.1.100 - 正在收集性能数据...
2026-03-23 20:02:00 ✅ 节点 192.168.1.100 - IO模型执行完成
2026-03-23 20:02:01 📡 节点 192.168.1.101 - 正在上传FIO工具...
2026-03-23 20:02:05 ✅ 节点 192.168.1.101 - FIO工具上传完成
2026-03-23 20:02:06 🔧 节点 192.168.1.101 - 执行IO模型：4k_16d_randread_1n
2026-03-23 20:03:00 ✅ 节点 192.168.1.101 - IO模型执行完成
2026-03-23 20:03:01 🎉 任务完成：所有节点测试完成
```

## 解决方案

### 1. 后端改进：优化日志消息格式

#### 修改文件：`backend/app/utils/task_executor.py`

**改进原则**：
- 使用用户友好的消息格式
- 突出关键操作阶段
- 包含节点和IO模型信息
- 清晰的开始/完成状态

**具体改进点**：

#### (1) 任务开始阶段

**当前**：
```python
logging.info(f"开始执行任务: task_id={task_id}, execution_id={execution_id}")
```

**改进为**：
```python
send_task_log(task_id, f"⏳ 任务开始：{task.name}",
              level='INFO',
              context={'operation': 'task_start', 'stage': '任务开始'})
```

#### (2) 节点准备阶段

**当前**：
```python
send_task_log(task_id, f"节点 {node.ip_address} 正在检测架构...",
              level='INFO',
              context={'node_id': node.id, 'operation': 'detect_architecture'})
```

**改进为**：
```python
send_task_log(task_id, f"📡 节点 {node.ip_address} - 正在准备测试环境...",
              level='INFO',
              context={'operation': 'node_prepare', 'stage': '节点准备', 'node_ip': node.ip_address})
```

#### (3) 工具上传阶段

**当前**：
```python
send_task_log(task_id, f"节点 {node.ip_address} 正在上传fio工具...",
              level='INFO',
              context={'node_id': node.id, 'operation': 'upload_fio'})
send_task_log(task_id, f"节点 {node.ip_address} fio工具上传完成",
              level='INFO',
              context={'node_id': node.id, 'operation': 'upload_fio'})
```

**改进为**：
```python
send_task_log(task_id, f"📡 节点 {node.ip_address} - 正在上传FIO工具...",
              level='INFO',
              context={'operation': 'upload_tool', 'stage': '工具上传', 'node_ip': node.ip_address, 'progress': 'start'})
send_task_log(task_id, f"✅ 节点 {node.ip_address} - FIO工具上传完成",
              level='INFO',
              context={'operation': 'upload_tool', 'stage': '工具上传', 'node_ip': node.ip_address, 'progress': 'complete'})
```

#### (4) IO模型执行阶段

**当前**：
```python
send_task_log(task_id, f"节点 {node.ip_address} 开始执行 IO 模型：{io_test_case.name}",
              level='INFO',
              context={'node_id': node.id, 'io_test_case_id': io_test_case.id,
                      'io_test_case_name': io_test_case.name, 'operation': 'execute_io_model'})
```

**改进为**：
```python
send_task_log(task_id, f"🔧 节点 {node.ip_address} - 执行IO模型：{io_test_case.name}",
              level='INFO',
              context={'operation': 'execute_io_model', 'stage': 'IO模型执行',
                      'node_ip': node.ip_address, 'io_model': io_test_case.name, 'progress': 'start'})
```

#### (5) 数据收集阶段

**当前**：
```python
send_task_log(task_id, f"节点 {node.ip_address} 正在收集IO性能抖动数据...",
              level='INFO',
              context={'node_id': node.id, 'io_test_case_id': io_test_case.id, 'operation': 'collect_jitter_data'})
```

**改进为**：
```python
send_task_log(task_id, f"📊 节点 {node.ip_address} - 正在收集性能数据...",
              level='INFO',
              context={'operation': 'collect_data', 'stage': '数据收集', 'node_ip': node.ip_address})
```

#### (6) IO模型完成阶段

**当前**：
```python
send_task_log(task_id, f"节点 {node.ip_address} 完成IO模型: {io_test_case.name}",
              level='INFO',
              context={'node_id': node.id, 'io_test_case_id': io_test_case.id,
                      'io_test_case_name': io_test_case.name, 'operation': 'complete_io_model'})
```

**改进为**：
```python
send_task_log(task_id, f"✅ 节点 {node.ip_address} - IO模型执行完成：{io_test_case.name}",
              level='INFO',
              context={'operation': 'execute_io_model', 'stage': 'IO模型执行',
                      'node_ip': node.ip_address, 'io_model': io_test_case.name, 'progress': 'complete'})
```

#### (7) 任务完成阶段

**当前**：
```python
send_task_log(task_id, f"任务执行完成", level='INFO', context={'operation': 'task_completed'})
```

**改进为**：
```python
send_task_log(task_id, f"🎉 任务完成：所有节点测试完成",
              level='INFO',
              context={'operation': 'task_complete', 'stage': '任务完成'})
```

#### (8) 错误处理

**改进为**：
```python
send_task_log(task_id, f"❌ 节点 {node.ip_address} - 执行失败：{error_message}",
              level='ERROR',
              context={'operation': 'node_error', 'stage': '执行失败', 'node_ip': node.ip_address})
```

### 2. 前端改进：优化日志显示样式

#### 修改文件：`frontend/src/views/TaskDetail.vue`

**改进点**：

#### (1) 为不同操作阶段添加图标

```vue
<template>
  <div class="log-item">
    <span class="log-icon">{{ getLogIcon(log.context?.stage) }}</span>
    <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
    <span class="log-content">{{ log.message }}</span>
  </div>
</template>

<script>
const getLogIcon = (stage) => {
  const iconMap = {
    '任务开始': '⏳',
    '节点准备': '📡',
    '工具上传': '📡',
    'IO模型执行': '🔧',
    '数据收集': '📊',
    '任务完成': '🎉',
    '执行失败': '❌',
  };
  return iconMap[stage] || '•';
};
</script>
```

#### (2) 为不同阶段添加不同颜色

```css
.log-stage-任务开始 { color: #409EFF; font-weight: bold; }
.log-stage-节点准备 { color: #67C23A; }
.log-stage-工具上传 { color: #67C23A; }
.log-stage-IO模型执行 { color: #E6A23C; font-weight: 500; }
.log-stage-数据收集 { color: #909399; }
.log-stage-任务完成 { color: #67C23A; font-weight: bold; }
.log-stage-执行失败 { color: #F56C6C; font-weight: bold; }
```

#### (3) 折叠技术细节日志

为用户提供选项，可以显示/隐藏技术详情：

```vue
<el-switch
  v-model="showTechnicalLogs"
  active-text="显示技术日志"
  inactive-text="简化显示"
/>
```

### 3. 实施步骤

#### 阶段1：后端日志优化（必须）

1. 修改 `backend/app/utils/task_executor.py` 中的所有 `send_task_log` 调用
2. 使用用户友好的消息格式
3. 添加emoji图标
4. 统一 context 中的 stage 字段

#### 阶段2：前端样式优化（可选）

1. 修改 `frontend/src/views/TaskDetail.vue`
2. 添加日志图标显示
3. 添加阶段颜色区分
4. 添加技术日志过滤选项

## 日志消息格式规范

### 消息模板

```
{icon} 节点 {node_ip} - {action_description}
```

### Icon 使用规范

- ⏳ - 任务开始
- 📡 - 网络操作（上传工具、连接节点）
- 🔧 - 执行操作（运行IO模型）
- 📊 - 数据收集
- ✅ - 成功完成
- ❌ - 错误失败
- ⚠️  - 警告
- 🎉 - 任务完成

### Context 字段规范

```python
context = {
    'operation': 'upload_tool',  # 操作类型（用于过滤）
    'stage': '工具上传',          # 阶段名称（用于显示和样式）
    'node_ip': '192.168.1.100',  # 节点IP（用于筛选）
    'io_model': '4k_16d_randread_1n',  # IO模型（可选）
    'progress': 'start/complete'  # 进度状态（可选）
}
```

## 预期效果

### 优化前
```
2026-03-23 20:00:00 INFO  开始执行任务: task_id=56
2026-03-23 20:00:01 INFO  创建应用上下文
2026-03-23 20:00:02 INFO  查询任务信息
2026-03-23 20:00:03 INFO  获取节点信息
...（大量技术日志）
```

### 优化后
```
⏳ 任务开始：性能测试
📡 节点 192.168.1.100 - 正在上传FIO工具...
✅ 节点 192.168.1.100 - FIO工具上传完成
🔧 节点 192.168.1.100 - 执行IO模型：4k_16d_randread_1n
📊 节点 192.168.1.100 - 正在收集性能数据...
✅ 节点 192.168.1.100 - IO模型执行完成
🎉 任务完成：所有节点测试完成
```

## 注意事项

1. **保留技术日志**：在 Python logging 中仍然输出技术日志，但通过 `send_task_log` 发送的是用户友好消息
2. **日志级别**：保持 INFO/WARNING/ERROR 的级别划分
3. **向后兼容**：前端应该同时支持新旧日志格式
4. **性能考虑**：不要发送过多的实时日志，重要阶段即可

## 相关文件

- `backend/app/utils/task_executor.py` - 任务执行器，包含所有日志发送点
- `backend/app/views/tasks.py` - 任务视图，包含任务启动逻辑
- `frontend/src/views/TaskDetail.vue` - 任务详情页面，包含日志显示逻辑
- `backend/app/views/socket_events.py` - WebSocket事件处理，包含 `send_task_log` 函数
