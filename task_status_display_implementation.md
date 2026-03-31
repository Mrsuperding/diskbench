# 任务实时运行状态显示实现

## 修改概述

将任务详情页面的"日志输出"面板改造成"任务实时运行状态"显示面板，实时展示任务正在执行的操作和历史操作记录。

## 功能变化

### 修改前（日志输出）
- 传统日志列表展示
- 显示时间、级别、模块、消息
- 提供日志过滤和搜索功能
- 支持加载更多日志

### 修改后（任务实时运行状态）
- ✅ **状态图标显示** - 根据任务状态显示不同图标（运行中/已完成/失败/等待中）
- ✅ **当前操作显示** - 实时显示任务正在执行的操作
- ✅ **操作历史记录** - 显示最近20条操作历史
- ✅ **只读展示** - 用户只能查看，不能编辑
- ✅ **自动滚动** - 历史记录超过一定高度时提供滚动条

## 修改的文件

### frontend/src/views/TaskDetail.vue

#### 1. 导入图标组件（第463-464行）
```javascript
import {
  Loading,
  CircleCheck,
  CircleClose,
  Clock,
} from "@element-plus/icons-vue";
```

#### 2. 添加响应式状态变量（第593-598行）
```javascript
const currentOperation = ref(""); // 当前正在执行的操作
const operationHistory = ref([]); // 操作历史记录（最多保留20条）
```

#### 3. 修改WebSocket日志处理逻辑（第653-682行）
```javascript
socket.value.on("task_log", (data) => {
  console.log("收到任务日志:", data);

  if (data && typeof data === "object" && data.data) {
    const logData = data.data;

    // 更新当前操作状态
    if (logData.message) {
      currentOperation.value = logData.message;
    }

    // 添加到操作历史
    operationHistory.value.push({
      timestamp: logData.timestamp || new Date().toISOString(),
      message: logData.message,
      level: logData.level || "INFO",
      context: logData.context || {}
    });

    // 只保留最近20条操作历史
    if (operationHistory.value.length > 20) {
      operationHistory.value.shift();
    }

    console.log("当前操作:", currentOperation.value);
    console.log("操作历史数量:", operationHistory.value.length);
  }
});
```

#### 4. 添加状态文本转换方法（第1540-1550行）
```javascript
// 获取任务状态文本
const getTaskStatusText = () => {
  const statusMap = {
    'pending': '等待中',
    'running': '正在运行',
    'completed': '已完成',
    'failed': '执行失败',
    'cancelled': '已取消',
    'paused': '已暂停'
  };
  return statusMap[taskDetail.status] || '未知状态';
};
```

#### 5. 更新return导出（第1572-1641行）
新增导出：
- `currentOperation` - 当前操作状态
- `operationHistory` - 操作历史记录
- `getTaskStatusText` - 状态文本转换方法
- `Loading`, `CircleCheck`, `CircleClose`, `Clock` - 图标组件

#### 6. 重新设计UI模板（第231-296行）

**新的状态显示界面结构：**
```vue
<el-collapse-item title="任务实时运行状态" name="4">
  <div class="task-status-display">
    <div class="current-status-box">
      <!-- 状态头部 -->
      <div class="status-header">
        <span class="status-icon">
          <!-- 根据任务状态显示不同图标 -->
          <el-icon v-if="taskDetail.status === 'running'" class="is-loading">
            <Loading />
          </el-icon>
          <el-icon v-else-if="taskDetail.status === 'completed'" style="color: #67c23a;">
            <CircleCheck />
          </el-icon>
          <el-icon v-else-if="taskDetail.status === 'failed'" style="color: #f56c6c;">
            <CircleClose />
          </el-icon>
          <el-icon v-else style="color: #909399;">
            <Clock />
          </el-icon>
        </span>
        <span class="status-text">{{ getTaskStatusText() }}</span>
      </div>

      <!-- 当前操作显示 -->
      <div v-if="currentOperation" class="current-operation">
        <div class="operation-label">当前操作：</div>
        <div class="operation-content">{{ currentOperation }}</div>
      </div>

      <!-- 操作历史记录 -->
      <div class="operation-history">
        <div class="history-label">操作历史：</div>
        <div class="history-list">
          <div v-for="(op, index) in operationHistory" :key="index" class="history-item">
            <span class="history-time">{{ formatLogTime(op.timestamp) }}</span>
            <span class="history-text">{{ op.message }}</span>
            <el-tag v-if="op.level === 'ERROR'" type="danger" size="small">失败</el-tag>
          </div>
          <div v-if="operationHistory.length === 0" class="no-logs">
            暂无操作记录
          </div>
        </div>
      </div>
    </div>
  </div>
</el-collapse-item>
```

#### 7. 添加CSS样式（第1732行之后）

新增样式类：
```css
/* 任务状态显示样式 */
.task-status-display { ... }           /* 外层容器 */
.current-status-box { ... }            /* 状态盒子 */
.status-header { ... }                 /* 状态头部 */
.status-icon { ... }                   /* 状态图标 */
.status-text { ... }                   /* 状态文本 */
.current-operation { ... }             /* 当前操作区域 */
.operation-label { ... }               /* 操作标签 */
.operation-content { ... }             /* 操作内容 */
.operation-history { ... }             /* 操作历史区域 */
.history-label { ... }                 /* 历史标签 */
.history-list { ... }                  /* 历史列表容器 */
.history-item { ... }                  /* 历史条目 */
.history-time { ... }                  /* 历史时间 */
.history-text { ... }                  /* 历史文本 */
```

## 界面效果

### 任务运行中
```
┌──────────────────────────────────────────┐
│ 任务实时运行状态                          │
├──────────────────────────────────────────┤
│ 🔄 正在运行                               │
│                                          │
│ 当前操作：                                │
│ 节点 192.168.1.100 - 执行IO模型: test1   │
│                                          │
│ 操作历史：                                │
│ ┌──────────────────────────────────────┐ │
│ │ 20:00:00  任务开始                    │ │
│ │ 20:00:01  节点 192.168.1.100 - 上传  │ │
│ │ 20:00:05  节点 192.168.1.100 - 执行  │ │
│ └──────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

### 任务完成
```
┌──────────────────────────────────────────┐
│ 任务实时运行状态                          │
├──────────────────────────────────────────┤
│ ✓ 已完成                                  │
│                                          │
│ 操作历史：                                │
│ ┌──────────────────────────────────────┐ │
│ │ 20:00:00  任务开始                    │ │
│ │ 20:00:01  节点 192.168.1.100 - 上传  │ │
│ │ 20:00:05  节点 192.168.1.100 - 执行  │ │
│ │ 20:10:00  任务完成                    │ │
│ └──────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

### 任务失败
```
┌──────────────────────────────────────────┐
│ 任务实时运行状态                          │
├──────────────────────────────────────────┤
│ ✗ 执行失败                                │
│                                          │
│ 操作历史：                                │
│ ┌──────────────────────────────────────┐ │
│ │ 20:00:00  任务开始                    │ │
│ │ 20:00:01  节点连接失败    [失败]     │ │
│ └──────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

## 数据流

### 后端 → 前端
1. **后端**：任务执行时调用 `send_task_log(task_id, message, level, context)`
2. **WebSocket**：通过 `task_log` 事件发送给前端
3. **前端**：监听 `task_log` 事件
4. **更新状态**：
   - 更新 `currentOperation` 显示当前操作
   - 添加到 `operationHistory` 数组
   - 保持最近20条记录

### 数据结构
```javascript
// WebSocket接收的数据
{
  data: {
    timestamp: "2026-03-24T20:00:00",
    level: "INFO",
    message: "节点 192.168.1.100 - 执行IO模型: test1",
    context: {
      node_ip: "192.168.1.100",
      operation: "execute_io_model",
      stage: "执行IO模型"
    }
  }
}

// operationHistory 数组项
{
  timestamp: "2026-03-24T20:00:00",
  message: "节点 192.168.1.100 - 执行IO模型: test1",
  level: "INFO",
  context: { ... }
}
```

## 状态图标映射

| 任务状态 | 图标 | 颜色 | 动画 |
|---------|------|------|------|
| running | Loading (旋转) | 蓝色 #409eff | 旋转动画 |
| completed | CircleCheck (对勾) | 绿色 #67c23a | 无 |
| failed | CircleClose (叉号) | 红色 #f56c6c | 无 |
| pending/其他 | Clock (时钟) | 灰色 #909399 | 无 |

## 特性

### 1. 实时更新
- WebSocket连接保持实时性
- 任务状态变化立即反映在界面
- 操作历史自动追加新记录

### 2. 自动管理
- 操作历史自动限制在20条
- 超过20条时自动删除最旧的记录
- 避免内存占用过大

### 3. 用户友好
- 图标直观显示任务状态
- 当前操作高亮显示
- 操作历史提供完整上下文
- 失败操作显示红色标签

### 4. 性能优化
- 只保留必要的数据
- 使用虚拟滚动（如果需要可以升级）
- CSS动画使用GPU加速

## 部署步骤

### 1. 前端构建
```bash
cd D:\delvelop_project\ai_project\diskbench_pro2\diskbench_pro2\frontend
npm run build
```

### 2. 重启后端（如果需要）
```bash
cd D:\delvelop_project\ai_project\diskbench_pro2\diskbench_pro2\backend
python application.py
```

### 3. 刷新浏览器
- 按 `Ctrl+F5` 强制刷新
- 或清除缓存后重新打开

## 验证步骤

1. **打开任务详情页面**
   - 点击任务列表中的任务
   - 查看"任务实时运行状态"面板

2. **检查状态显示**
   - 确认状态图标正确显示
   - 确认状态文本正确（等待中/正在运行/已完成等）

3. **启动任务**
   - 点击"开始任务"按钮
   - 观察当前操作是否实时更新
   - 观察操作历史是否自动追加

4. **查看操作历史**
   - 确认历史记录按时间顺序显示
   - 确认最多显示20条记录
   - 确认失败操作有红色标签

5. **检查WebSocket连接**
   - 打开浏览器Console（F12）
   - 查看是否有"收到任务日志"输出
   - 查看是否有"当前操作"和"操作历史数量"输出

## 与后端集成

### 后端无需修改
当前后端已经通过 `send_task_log()` 发送日志，前端直接使用这些数据：

```python
# backend/app/utils/task_executor.py
send_task_log(
    task_id,
    f"节点 {node.ip_address} - 执行IO模型：{io_test_case.name}",
    level='INFO',
    context={
        'node_ip': node.ip_address,
        'operation': 'execute_io_model',
        'stage': '执行IO模型'
    }
)
```

### 前端自动处理
前端接收到日志后：
1. 提取 `message` 作为当前操作
2. 添加完整记录到操作历史
3. 自动管理历史记录数量

## 未来可能的改进

1. **操作分类**
   - 按操作类型分组显示
   - 提供操作类型过滤

2. **性能优化**
   - 使用虚拟滚动处理大量历史
   - 提供"查看完整日志"链接

3. **交互增强**
   - 点击历史记录显示详细信息
   - 支持导出操作历史

4. **可视化增强**
   - 添加进度条显示任务完成度
   - 使用时间轴展示操作历史

## 总结

这次修改：
- ✅ 将日志输出改造为实时状态显示
- ✅ 提供更直观的任务执行状态展示
- ✅ 保持只读展示，用户不可编辑
- ✅ 保留操作历史记录供查看
- ✅ 使用图标和颜色增强视觉效果
- ✅ 优化用户体验和界面美观度

修改后的界面更符合"任务监控"的场景，用户可以清晰地看到：
- 任务当前在做什么
- 任务之前做过什么
- 任务的整体执行状态
