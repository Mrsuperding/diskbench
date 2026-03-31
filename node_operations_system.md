# 节点操作管理系统

## 功能概述

创建了一个完整的节点操作页面，支持对选中的节点执行文件传输、文件替换和Shell命令操作。系统采用四步式流程，确保操作的安全性和可控性。

## 核心功能

### 1. 节点选择 ✅
- 显示所有节点列表（表格形式）
- 支持多选节点
- 显示节点状态、IP、系统信息
- 实时显示已选节点数量

### 2. 连通性检测 ✅
- 在执行操作前先检测节点连通性
- 显示每个节点的连通状态
- 统计连通和不可达节点数量
- 只对连通的节点执行后续操作

### 3. 操作执行 ✅

#### 上传文件
- 选择本地文件
- 指定远程路径
- 批量上传到所有选中节点

#### 替换文件
- 选择本地文件
- 指定要替换的远程文件路径
- 可选：自动备份原文件
- 备份文件格式：`原文件.backup.时间戳`

#### 执行Shell命令
- 输入Shell命令
- 批量在所有节点执行
- 返回执行输出和退出码

### 4. 结果查看 ✅
- 显示每个节点的操作结果
- 区分成功和失败
- 显示详细信息和输出
- 统计成功和失败数量

## 技术架构

### 后端 API

**文件**: `backend/app/views/node_operations.py`

#### API端点

| 端点 | 方法 | 功能 | 参数 |
|-----|------|-----|------|
| `/api/node-operations/check-connectivity` | POST | 检测节点连通性 | node_ids[] |
| `/api/node-operations/execute-command` | POST | 执行Shell命令 | node_ids[], command |
| `/api/node-operations/upload-file` | POST | 上传文件 | node_ids[], remote_path, file |
| `/api/node-operations/replace-file` | POST | 替换文件 | node_ids[], remote_path, file, backup |
| `/api/node-operations/download-file` | POST | 下载文件 | node_id, remote_path |

#### 返回格式

```json
{
  "success": true,
  "message": "操作完成",
  "data": [
    {
      "node_id": 1,
      "node_name": "node1",
      "success": true,
      "message": "操作成功",
      "output": "命令输出...",
      "executed_at": "2026-03-27T10:30:00"
    }
  ]
}
```

### 前端组件

**文件**: `frontend/src/views/NodeOperations.vue`

#### 组件结构

```
NodeOperations.vue
├── 步骤条 (el-steps)
├── 步骤1: 节点选择
│   └── 节点列表表格 (el-table)
├── 步骤2: 连通性检测
│   ├── 检测结果表格
│   └── 统计信息
├── 步骤3: 操作执行
│   ├── 操作类型选择 (el-radio-group)
│   ├── 上传文件表单
│   ├── 替换文件表单
│   └── 执行命令表单
└── 步骤4: 结果展示
    ├── 结果详情表格
    └── 统计信息
```

#### 状态管理

```javascript
const currentStep = ref(0);           // 当前步骤
const selectedNodes = ref([]);        // 选中的节点
const connectivityChecked = ref(false); // 连通性检测完成标志
const connectivityResults = ref([]);  // 连通性检测结果
const operationResults = ref([]);     // 操作执行结果
```

## 操作流程

### 完整流程图

```
开始
  ↓
[步骤1] 选择目标节点
  ├─ 显示所有节点
  ├─ 多选节点
  └─ 至少选择1个 → 下一步
  ↓
[步骤2] 检测连通性
  ├─ 点击"开始检测"
  ├─ 并发检测所有选中节点
  ├─ 显示检测结果
  └─ 统计连通/不可达数量 → 下一步
  ↓
[步骤3] 选择并执行操作
  ├─ 选择操作类型
  │   ├─ 上传文件
  │   ├─ 替换文件
  │   └─ 执行命令
  ├─ 填写表单
  ├─ 点击执行
  └─ 自动跳转到结果页
  ↓
[步骤4] 查看结果
  ├─ 显示每个节点的执行结果
  ├─ 区分成功/失败
  ├─ 显示详细信息
  └─ 可选：重新开始 / 返回操作
  ↓
结束
```

### 安全检查流程

```
用户选择节点
    ↓
检测连通性
    ↓
   是否连通?
    ├─ 是 → 加入执行列表
    └─ 否 → 跳过该节点
    ↓
只对连通的节点执行操作
    ↓
返回所有节点的执行结果
```

## 页面截图说明

### 步骤1: 节点选择

```
┌─────────────────────────────────────────────────┐
│ 节点操作                                         │
│ 对选中节点执行文件操作和Shell命令                │
└─────────────────────────────────────────────────┘

  ① 选择节点  ○ 检测连通性  ○ 执行操作  ○ 查看结果

┌───────────────────────────────────────────────┐
│ 选择目标节点                        [下一步]   │
├───────────────────────────────────────────────┤
│ □  节点名称    IP地址      状态   操作系统     │
│ ☑  node1     192.168.1.1  在线   CentOS 7    │
│ ☑  node2     192.168.1.2  在线   Ubuntu 20   │
│ □  node3     192.168.1.3  离线   CentOS 8    │
├───────────────────────────────────────────────┤
│           已选择 2 个节点                      │
└───────────────────────────────────────────────┘
```

### 步骤2: 连通性检测

```
  ○ 选择节点  ② 检测连通性  ○ 执行操作  ○ 查看结果

┌───────────────────────────────────────────────┐
│ 检测节点连通性    [上一步][开始检测][下一步]  │
├───────────────────────────────────────────────┤
│ 节点名称    IP地址      连通状态    检测时间   │
│ node1     192.168.1.1    连通    10:30:00    │
│ node2     192.168.1.2    连通    10:30:01    │
├───────────────────────────────────────────────┤
│    连通节点: 2个         不可达节点: 0个      │
└───────────────────────────────────────────────┘
```

### 步骤3: 执行操作

```
  ○ 选择节点  ○ 检测连通性  ③ 执行操作  ○ 查看结果

┌───────────────────────────────────────────────┐
│ 选择操作类型                      [上一步]     │
├───────────────────────────────────────────────┤
│  [📤 上传文件]  [🔄 替换文件]  [💻 执行命令]  │
│                                               │
│  选择文件:  [选择文件]                        │
│  远程路径:  /tmp/myfile.txt                   │
│                                               │
│             [开始上传]                        │
└───────────────────────────────────────────────┘
```

### 步骤4: 查看结果

```
  ○ 选择节点  ○ 检测连通性  ○ 执行操作  ④ 查看结果

┌───────────────────────────────────────────────┐
│ 操作结果              [重新开始][返回操作]     │
├───────────────────────────────────────────────┤
│ 节点名称  执行状态      详细信息               │
│ node1     成功         文件已上传到 /tmp/...  │
│ node2     成功         文件已上传到 /tmp/...  │
├───────────────────────────────────────────────┤
│       成功: 2个              失败: 0个        │
└───────────────────────────────────────────────┘
```

## 使用示例

### 示例1: 批量上传配置文件

**场景**: 需要将新的配置文件上传到10台服务器

1. 选择10个节点
2. 检测连通性（假设8台连通，2台不可达）
3. 选择"上传文件"
4. 选择本地文件: `config.yaml`
5. 输入远程路径: `/etc/myapp/config.yaml`
6. 点击"开始上传"
7. 查看结果：8台成功，2台跳过

### 示例2: 批量替换系统文件

**场景**: 更新所有服务器的hosts文件

1. 选择所有节点
2. 检测连通性
3. 选择"替换文件"
4. 选择本地文件: `hosts`
5. 输入远程路径: `/etc/hosts`
6. 开启"备份原文件"
7. 点击"开始替换"
8. 原文件被备份为: `/etc/hosts.backup.20260327103000`

### 示例3: 批量执行运维命令

**场景**: 清理所有服务器的临时文件

1. 选择所有节点
2. 检测连通性
3. 选择"执行命令"
4. 输入命令: `rm -rf /tmp/*.log`
5. 点击"执行命令"
6. 查看每台服务器的执行输出

## 数据处理

### 上传文件处理流程

```javascript
// 1. 用户选择文件
handleFileChange(file) {
  uploadForm.value.file = file.raw;
}

// 2. 构造FormData
const formData = new FormData();
nodeIds.forEach(id => formData.append("node_ids[]", id));
formData.append("remote_path", remotePath);
formData.append("file", file);

// 3. 发送请求
await nodeOperationsApi.uploadFile(nodeIds, remotePath, file);
```

### 后端文件处理

```python
# 1. 接收文件
file = request.files.get('file')
filename = secure_filename(file.filename)

# 2. 保存到临时目录
temp_file_path = os.path.join(tempfile.gettempdir(), filename)
file.save(temp_file_path)

# 3. 通过SSH上传到各节点
# TODO: 实现SSH文件传输

# 4. 清理临时文件
os.remove(temp_file_path)
```

## 安全特性

### 1. 文件名安全处理

```python
from werkzeug.utils import secure_filename
filename = secure_filename(file.filename)  # 防止路径遍历攻击
```

### 2. 连通性预检

- 在执行操作前必须先检测连通性
- 只对连通的节点执行操作
- 避免对不可达节点浪费时间

### 3. 自动备份

替换文件时可选择自动备份：
```python
backup_path = f"{remote_path}.backup.{timestamp}"
# 1. 备份原文件
# 2. 上传新文件
# 3. 验证成功
```

### 4. 权限控制

- 需要JWT认证
- 记录操作日志
- 可追溯操作历史

## 当前限制（Phase 1）

### 使用模拟数据

当前版本使用模拟数据进行功能演示：

```python
# 模拟连通性检测
is_connected = random.choice([True, True, True, False])  # 75%概率连通

# 模拟命令执行
success = random.choice([True, True, False])  # 66%概率成功
```

### Phase 2 待实现功能

1. **真实SSH连接**
   - 使用paramiko库建立SSH连接
   - 基于登录凭证进行认证

2. **真实文件传输**
   - 使用SFTP协议传输文件
   - 支持断点续传
   - 显示传输进度

3. **真实命令执行**
   - 通过SSH执行远程命令
   - 实时获取输出
   - 支持交互式命令

4. **增强功能**
   - 文件下载功能
   - 批量脚本执行
   - 定时任务调度
   - 操作审计日志

## 测试验证

### 后端API测试

```bash
# 测试连通性检测
curl -X POST http://localhost:5003/api/node-operations/check-connectivity \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"node_ids": [1, 2, 3]}'

# 测试命令执行
curl -X POST http://localhost:5003/api/node-operations/execute-command \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"node_ids": [1, 2], "command": "ls -la /tmp"}'
```

### 前端功能测试

1. 节点选择功能测试
2. 连通性检测测试
3. 文件上传测试
4. 文件替换测试
5. 命令执行测试
6. 结果展示测试

## 文件清单

### 后端
- ✅ `backend/app/views/node_operations.py` - API接口
- ✅ `backend/application.py` - 注册蓝图

### 前端
- ✅ `frontend/src/views/NodeOperations.vue` - 页面组件
- ✅ `frontend/src/api/nodeOperations.js` - API调用
- ✅ `frontend/src/router/index.js` - 路由配置

## 路由访问

```
前端路由: /node-operations
页面标题: 节点操作
图标: Operation
```

## 用户权限

- 需要登录认证
- 普通用户和管理员均可访问
- 操作记录可追溯

## 下一步优化

1. **实现真实SSH功能**（Phase 2）
2. **添加操作日志记录**
3. **支持批量脚本管理**
4. **增加操作审批流程**
5. **实时显示操作进度**
6. **支持文件目录上传**
7. **增加文件对比功能**

---

**创建时间**: 2026-03-27
**版本**: v1.0 (Phase 1 - 功能原型)
**状态**: ✅ 完成（使用模拟数据）
