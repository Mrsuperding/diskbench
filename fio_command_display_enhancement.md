# FIO命令显示和执行流程优化

## 修改概述

优化任务实时运行状态显示，增加以下功能：
1. **显示完整的FIO命令** - 让用户清楚看到执行的具体FIO参数
2. **调整执行顺序** - FIO执行完成后再显示"收集日志阶段"

## 主要改进

### 1. 显示FIO命令

**改进前：**
```
节点 192.168.1.100 - 执行IO模型：4k_randread（分区: /dev/vdb）
节点 192.168.1.100 - 执行IO模型：正在运行FIO测试（4k_randread）
```
用户不知道具体执行了什么FIO参数。

**改进后：**
```
节点 192.168.1.100 - 执行IO模型：4k_randread（分区: /dev/vdb）

节点 192.168.1.100 - 执行FIO命令：
┌────────────────────────────────────────────────────────┐
│ FIO命令：                                               │
│ fio --name=diskbench_test --rw=randread --bs=4k       │
│ --iodepth=32 --filename=/dev/vdb --runtime=60         │
│ --numjobs=1 --group_reporting                         │
└────────────────────────────────────────────────────────┘

节点 192.168.1.100 - 执行IO模型：正在运行FIO测试（4k_randread）...
```

### 2. 调整执行流程

**改进前的执行顺序：**
```
1. 执行IO模型开始
2. 收集日志阶段：开始收集iostat性能数据  ❌ 时机不对
3. 收集日志阶段：iostat后台监控已启动
4. 执行IO模型：正在运行FIO测试
5. [FIO运行中...]
6. 收集日志阶段：停止iostat监控
```

**改进后的执行顺序：**
```
1. 执行IO模型开始
2. 显示FIO命令                          ✅ 新增
3. 启动iostat后台监控（不显示日志）      ✅ 静默启动
4. 执行IO模型：正在运行FIO测试...
5. [FIO运行中...]
6. 收集日志阶段：FIO执行完成，开始收集iostat性能数据  ✅ 时机正确
7. 收集日志阶段：停止iostat监控，开始解析数据
```

## 技术实现

### 后端修改

#### 1. 构建FIO命令字符串

**文件：** `backend/app/utils/task_executor.py` (第149-176行)

```python
# 构建FIO命令字符串用于显示
fio_cmd_parts = ['fio', '--name=diskbench_test']

# 添加核心参数
for key, value in fio_params.items():
    if key in ['template_id', 'partitions', 'read_write_ratio', 'description']:
        continue
    # 参数映射
    param_mapping = {'io_type': 'rw', 'block_size': 'bs', 'queue_depth': 'iodepth'}
    mapped_key = param_mapping.get(key, key)

    if isinstance(value, bool):
        if value and key != 'time_based':
            fio_cmd_parts.append(f'--{mapped_key}')
        elif key == 'time_based' and value:
            fio_cmd_parts.append(f'--time_based')
    elif value:
        fio_cmd_parts.append(f'--{mapped_key}={value}')

# 添加默认参数
if not any('--numjobs=' in part for part in fio_cmd_parts):
    fio_cmd_parts.append('--numjobs=1')
if not any('--runtime=' in part for part in fio_cmd_parts):
    fio_cmd_parts.append('--runtime=30')
if not any('--group_reporting' in part for part in fio_cmd_parts):
    fio_cmd_parts.append('--group_reporting')

fio_command = ' '.join(fio_cmd_parts)
```

#### 2. 发送FIO命令日志

**文件：** `backend/app/utils/task_executor.py` (第178-182行)

```python
# 发送FIO命令到前端显示
send_task_log(task_id, f"节点 {node.ip_address} - 执行FIO命令：{fio_command}",
            level='INFO',
            context={
                'node_id': node.id,
                'node_ip': node.ip_address,
                'io_test_case_id': io_test_case.id,
                'io_model': io_test_case.name,
                'fio_command': fio_command,  # 完整的FIO命令
                'operation': 'fio_command',
                'stage': '执行IO模型'
            })
```

#### 3. 调整iostat启动时机

**文件：** `backend/app/utils/task_executor.py` (第184-187行)

```python
# 启动iostat收集后台数据（在FIO执行之前，但不发送日志）
iostat_log = f'/tmp/iostat_{task_id}_{execution_id}_{node.id}_{io_test_case.id}.log'
ssh_client.execute_command(f"sh -c 'iostat -xdm 1 > {iostat_log} 2>&1 & echo $! > /tmp/iostat_pid.txt'")
logging.info(f"iostat后台监控已启动: {iostat_log}")
```

#### 4. FIO执行完成后再显示收集日志

**文件：** `backend/app/utils/task_executor.py` (第189-201行)

```python
# 执行IO测试
send_task_log(task_id, f"节点 {node.ip_address} - 执行IO模型：正在运行FIO测试（{io_test_case.name}）...",
            level='INFO',
            context={'node_id': node.id, 'node_ip': node.ip_address,
                    'io_test_case_id': io_test_case.id, 'io_model': io_test_case.name,
                    'operation': 'running_fio', 'stage': '执行IO模型'})
result = ssh_client.run_fio_test(fio_params)
logging.info(f"IO测试结果: success={result['success']}")

# FIO执行完成后开始收集日志阶段
send_task_log(task_id, f"节点 {node.ip_address} - 收集日志阶段：FIO执行完成，开始收集iostat性能数据",
            level='INFO',
            context={'node_id': node.id, 'node_ip': node.ip_address,
                    'io_test_case_id': io_test_case.id,
                    'operation': 'collect_logs', 'stage': '收集日志阶段',
                    'progress': 'start'})
```

### 前端修改

#### 1. 检测FIO命令并特殊显示

**文件：** `frontend/src/views/TaskDetail.vue` (第283-306行)

```vue
<div class="history-details" v-if="op.context">
  <!-- FIO命令特殊显示 -->
  <div v-if="op.context.fio_command" class="fio-command-block">
    <div class="fio-command-label">FIO命令：</div>
    <pre class="fio-command-code">{{ op.context.fio_command }}</pre>
  </div>

  <!-- 其他详细信息 -->
  <div v-if="!op.context.fio_command" class="detail-items">
    <span v-if="op.context.nodes && op.context.nodes.length > 0" class="detail-item">
      节点: {{ op.context.nodes.join(', ') }}
    </span>
    <span v-if="op.context.io_models && op.context.io_models.length > 0" class="detail-item">
      IO模型: {{ op.context.io_models.join(', ') }}
    </span>
    <span v-if="op.context.partition" class="detail-item">
      分区: {{ op.context.partition }}
    </span>
    <span v-if="op.context.duration" class="detail-item">
      耗时: {{ op.context.duration }}秒
    </span>
  </div>
</div>
```

#### 2. FIO命令代码块样式

**文件：** `frontend/src/views/TaskDetail.vue` (第1938-1975行)

```css
.fio-command-block {
  width: 100%;
  margin-top: 8px;
}

.fio-command-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
  font-weight: 600;
}

.fio-command-code {
  background-color: #2d2d2d;      /* 深色背景 */
  color: #f8f8f2;                 /* 浅色文字 */
  padding: 12px;
  border-radius: 4px;
  font-family: 'Courier New', Consolas, Monaco, monospace;  /* 等宽字体 */
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;          /* 自动换行 */
  word-wrap: break-word;
  margin: 0;
  border-left: 3px solid #409eff; /* 蓝色左边框 */
}
```

## 界面效果

### 完整的执行流程显示

```
┌─────────────────────────────────────────────────────────────┐
│ 任务实时运行状态                                             │
├─────────────────────────────────────────────────────────────┤
│ 🔄 正在运行                                                  │
│                                                             │
│ 当前操作：                                                   │
│ 节点 192.168.1.100 - 执行IO模型：正在运行FIO测试（4k_randread）... │
│                                                             │
│ 操作历史：                                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 20:00:00 【执行IO模型】                                  │ │
│ │ 节点 192.168.1.100 - 执行IO模型：4k_randread            │ │
│ │   分区: /dev/vdb                                        │ │
│ │                                                         │ │
│ │ 20:00:01 【执行IO模型】                                  │ │
│ │ 节点 192.168.1.100 - 执行FIO命令：                      │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ FIO命令：                                            │ │ │
│ │ │ fio --name=diskbench_test --rw=randread --bs=4k    │ │ │
│ │ │ --iodepth=32 --filename=/dev/vdb --runtime=60      │ │ │
│ │ │ --numjobs=1 --group_reporting                      │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ │                                                         │ │
│ │ 20:00:02 【执行IO模型】（蓝色高亮，当前进行中）          │ │
│ │ 节点 192.168.1.100 - 执行IO模型：正在运行FIO测试...    │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

[等待60秒FIO执行...]

┌─────────────────────────────────────────────────────────────┐
│ 任务实时运行状态                                             │
├─────────────────────────────────────────────────────────────┤
│ 🔄 正在运行                                                  │
│                                                             │
│ 当前操作：                                                   │
│ 节点 192.168.1.100 - 收集日志阶段：FIO执行完成，开始收集iostat数据 │
│                                                             │
│ 操作历史：                                                   │
│ │ ... 之前的日志 ...                                       │ │
│ │                                                         │ │
│ │ 20:01:02 【收集日志阶段】（蓝色高亮，当前进行中）        │ │
│ │ 节点 192.168.1.100 - 收集日志阶段：FIO执行完成          │ │
│ │                                                         │ │
│ │ 20:01:03 【收集日志阶段】                                │ │
│ │ 节点 192.168.1.100 - 收集日志阶段：停止iostat监控       │ │
│ │                                                         │ │
│ │ 20:01:04 【执行完成】                                    │ │
│ │ 节点 192.168.1.100 - IO模型执行成功：4k_randread       │ │
└─────────────────────────────────────────────────────────────┘
```

## FIO命令示例

### 随机读测试
```bash
fio --name=diskbench_test --rw=randread --bs=4k --iodepth=32
--filename=/dev/vdb --runtime=60 --numjobs=1 --group_reporting
```

### 随机写测试
```bash
fio --name=diskbench_test --rw=randwrite --bs=4k --iodepth=16
--filename=/dev/vdb --runtime=120 --numjobs=4 --group_reporting
```

### 混合读写测试
```bash
fio --name=diskbench_test --rw=randrw --rwmixread=70 --bs=4k
--iodepth=32 --filename=/dev/vdb --runtime=60 --numjobs=1
--group_reporting
```

### 顺序读测试
```bash
fio --name=diskbench_test --rw=read --bs=1m --iodepth=1
--filename=/dev/vdb --size=10G --direct=1 --numjobs=1
--group_reporting
```

## 用户价值

### 1. 透明度提升
- ✅ 用户清楚看到执行的FIO参数
- ✅ 便于验证测试配置是否正确
- ✅ 便于复现问题或手动执行相同测试

### 2. 调试便利
- ✅ 发现参数配置错误时，立即可见
- ✅ 可以复制FIO命令在其他机器上测试
- ✅ 便于技术支持人员排查问题

### 3. 流程清晰
- ✅ 执行顺序更符合逻辑
- ✅ FIO执行完成后才显示收集日志
- ✅ 避免用户误解执行流程

### 4. 学习价值
- ✅ 用户可以学习FIO命令的参数
- ✅ 了解不同IO模型对应的FIO配置
- ✅ 便于编写自定义测试脚本

## 修改的文件

### 后端
1. **backend/app/utils/task_executor.py**
   - 第149-176行：构建FIO命令字符串
   - 第178-182行：发送FIO命令日志
   - 第184-187行：静默启动iostat监控
   - 第189-201行：调整收集日志阶段时机

### 前端
1. **frontend/src/views/TaskDetail.vue**
   - 第283-306行：FIO命令特殊显示逻辑
   - 第1938-1975行：FIO命令代码块样式

## 部署状态

- ✅ 前端已构建
- ✅ 后端已重启（进程 26480，端口 5003）

## 验证方法

1. 刷新浏览器（Ctrl+F5）
2. 创建一个新任务
3. 执行任务
4. 打开任务详情页面
5. 查看"任务实时运行状态"面板
6. 应该看到：
   - ✅ FIO命令以代码块形式显示
   - ✅ 黑色背景，白色文字，蓝色左边框
   - ✅ FIO执行完成后才显示"收集日志阶段"
   - ✅ 命令可以自动换行，不会超出边界

## 示例数据

### 发送的WebSocket日志

```javascript
{
  data: {
    timestamp: "2026-03-24T20:00:01",
    level: "INFO",
    message: "节点 192.168.1.100 - 执行FIO命令：fio --name=diskbench_test --rw=randread --bs=4k --iodepth=32 --filename=/dev/vdb --runtime=60 --numjobs=1 --group_reporting",
    context: {
      node_id: 16,
      node_ip: "192.168.1.100",
      io_test_case_id: 2,
      io_model: "4k_randread",
      fio_command: "fio --name=diskbench_test --rw=randread --bs=4k --iodepth=32 --filename=/dev/vdb --runtime=60 --numjobs=1 --group_reporting",
      operation: "fio_command",
      stage: "执行IO模型"
    }
  }
}
```

### 前端接收和显示

前端检测到 `op.context.fio_command` 存在时，会使用特殊的代码块样式显示：

```vue
<div class="fio-command-block">
  <div class="fio-command-label">FIO命令：</div>
  <pre class="fio-command-code">
    fio --name=diskbench_test --rw=randread --bs=4k
    --iodepth=32 --filename=/dev/vdb --runtime=60
    --numjobs=1 --group_reporting
  </pre>
</div>
```

## 技术细节

### 参数映射

```python
param_mapping = {
    'io_type': 'rw',        # IO类型 -> rw
    'block_size': 'bs',     # 块大小 -> bs
    'queue_depth': 'iodepth' # 队列深度 -> iodepth
}
```

### 默认参数

如果用户未指定，系统会自动添加：
- `--numjobs=1` - 默认1个作业
- `--runtime=30` - 默认运行30秒
- `--group_reporting` - 默认启用组报告

### 参数过滤

以下参数不会出现在FIO命令中：
- `template_id` - 模板ID（内部使用）
- `partitions` - 分区列表（已转换为filename）
- `read_write_ratio` - 读写比例（已转换为rwmixread）
- `description` - 描述信息（内部使用）

## 注意事项

1. **命令显示与实际执行可能略有差异**
   - 显示的命令是简化版本
   - 实际执行时SSH客户端可能添加额外参数
   - 但核心参数是一致的

2. **长命令自动换行**
   - 使用 `white-space: pre-wrap`
   - 避免水平滚动
   - 保持可读性

3. **样式兼容性**
   - 使用标准CSS属性
   - 支持所有现代浏览器
   - 等宽字体自动回退

## 总结

这次优化让用户可以：
- ✅ 看到完整的FIO执行命令
- ✅ 理解任务的执行流程
- ✅ 在正确的时机看到收集日志阶段
- ✅ 便于问题排查和命令复现

界面更加专业、透明，提升了用户信任度和系统可调试性。

## 相关文档

- `task_status_detail_enhancement.md` - 任务状态详细显示增强
- `full_stack_performance_optimization_summary.md` - 全栈性能优化总结
