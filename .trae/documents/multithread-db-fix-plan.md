# 多线程 db 参数传递问题修复计划

## 问题分析

### 当前代码问题

**tasks.py 第 294-301 行**:
```python
def run_task():
    try:
        run_task_execution(task_id, execution.id, app)
    except Exception as e:
        logging.error(f"执行任务时发生异常：{e}", exc_info=True)

thread = threading.Thread(target=run_task)
thread.daemon = True
thread.start()
```

**tasks.py 第 441 行** (并行执行):
```python
executor.submit(execute_node_task, node, task_id, execution_id, io_test_cases, app, db)
```

**task_executor.py 第 494 行**:
```python
def execute_node_task(node, task_id, execution_id, io_test_cases, app, db):
    try:
        with app.app_context():
            # 使用 db 对象
            db.session.commit()
```

### 核心问题

1. **db 对象不能跨线程传递**: Flask-SQLAlchemy 的 `db` 对象是与 Flask 应用上下文绑定的，不能直接从主线程传递到子线程
2. **应用上下文问题**: 虽然在 `execute_node_task` 中使用了 `with app.app_context()`,但 `db` 对象作为参数传递时可能已经失效
3. **正确的做法**: 在子线程中重新导入 `db` 对象，而不是作为参数传递

## 解决方案

### 方案 1: 移除 db 参数，在子线程中重新导入 (推荐)

**修改步骤**:

1. **修改 task_executor.py**:
   - 移除 `execute_node_task` 函数的 `db` 参数
   - 在函数内部导入 `from app.models import db`
   - 同样修改 `process_io_test_case` 函数

2. **修改 tasks.py**:
   - 移除调用时的 `db` 参数传递
   - 修改 `run_task_execution` 函数签名

### 方案 2: 传递 app 配置，在子线程中创建新的 db 绑定

不推荐，因为更复杂且容易出错。

## 需要修改的文件

1. **backend/app/utils/task_executor.py**
   - 修改 `execute_node_task` 函数签名和实现
   - 修改 `process_io_test_case` 函数签名和实现
   - 修改 `run_task_execution` 函数签名和实现

2. **backend/app/views/tasks.py**
   - 修改 `run_task_execution` 的调用
   - 修改 ThreadPoolExecutor 的 submit 调用

## 详细修改步骤

### 步骤 1: 修改 task_executor.py

#### 1.1 修改 execute_node_task 函数
```python
def execute_node_task(node, task_id, execution_id, io_test_cases, app):
    """执行节点任务"""
    # 移除 db 参数
    from app.models import db  # 在函数内部导入
    # ... 其余代码不变
```

#### 1.2 修改 process_io_test_case 函数
```python
def process_io_test_case(ssh_client, task_id, execution_id, node, io_test_case, app):
    """处理单个 IO 测试用例"""
    # 移除 db 参数
    from app.models import db  # 在函数内部导入
    # ... 其余代码不变
```

### 步骤 2: 修改 tasks.py

#### 2.1 修改 ThreadPoolExecutor 调用
```python
# 原代码:
executor.submit(execute_node_task, node, task_id, execution_id, io_test_cases, app, db)

# 修改后:
executor.submit(execute_node_task, node, task_id, execution_id, io_test_cases, app)
```

#### 2.2 修改串行执行调用
```python
# 原代码:
node_failed_flag, error_msg = execute_node_task(node, task_id, execution_id, io_test_cases, app, db)

# 修改后:
node_failed_flag, error_msg = execute_node_task(node, task_id, execution_id, io_test_cases, app)
```

## 测试验证

1. **单元测试**: 验证函数签名正确
2. **集成测试**: 执行实际任务，验证多线程执行正常
3. **日志验证**: 确认日志记录正常

## 风险评估

- **低风险**: 只是移除参数传递，在函数内部重新导入
- **向后兼容**: 需要确保所有调用处都修改正确
- **测试覆盖**: 需要验证并行和串行两种模式都正常工作

## 验收标准

1. 代码编译通过，无语法错误
2. 函数签名一致，无参数不匹配错误
3. 任务可以正常执行 (并行和串行模式)
4. 数据库操作正常 (查询、插入、提交)
5. 日志记录正常
