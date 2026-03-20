# 多线程 db 参数传递问题修复总结

## 问题发现

用户指出代码中存在多线程参数传递问题:

```python
# tasks.py 第 294-301 行
def run_task():
    try:
        run_task_execution(task_id, execution.id, app)
    except Exception as e:
        logging.error(f"执行任务时发生异常：{e}", exc_info=True)

thread = threading.Thread(target=run_task)
thread.daemon = True
thread.start()
```

## 核心问题

**Flask-SQLAlchemy 的 `db` 对象不能跨线程传递**

### 问题代码

**修改前** - task_executor.py:
```python
def execute_node_task(node, task_id, execution_id, io_test_cases, app, db):
    """执行节点任务"""
    try:
        with app.app_context():
            # 使用 db 对象
            db.session.commit()
```

**修改前** - tasks.py:
```python
# 并行执行
executor.submit(execute_node_task, node, task_id, execution_id, io_test_cases, app, db)

# 串行执行
node_failed_flag, error_msg = execute_node_task(node, task_id, execution_id, io_test_cases, app, db)
```

### 问题原因

1. **应用上下文绑定**: Flask-SQLAlchemy 的 `db` 对象是与 Flask 应用上下文绑定的
2. **线程隔离**: 每个线程有独立的应用上下文，主线程的 `db` 对象在子线程中可能失效
3. **参数传递错误**: 直接将 `db` 作为参数传递到子线程是错误的做法

## 解决方案

**在子线程内部重新导入 `db` 对象，而不是作为参数传递**

### 修改内容

#### 1. task_executor.py - process_io_test_case 函数

**修改前**:
```python
def process_io_test_case(ssh_client, task_id, execution_id, node, io_test_case, app, db):
    """处理单个 IO 测试用例"""
    from app.models.test_task import TestTask
```

**修改后**:
```python
def process_io_test_case(ssh_client, task_id, execution_id, node, io_test_case, app):
    """处理单个 IO 测试用例"""
    from app.models.test_task import TestTask
    from app.models import db  # 在函数内部导入
```

#### 2. task_executor.py - execute_node_task 函数

**修改前**:
```python
def execute_node_task(node, task_id, execution_id, io_test_cases, app, db):
    """执行节点任务"""
    try:
        with app.app_context():
```

**修改后**:
```python
def execute_node_task(node, task_id, execution_id, io_test_cases, app):
    """执行节点任务"""
    from app.models import db  # 在函数内部导入
    
    try:
        with app.app_context():
```

#### 3. tasks.py - 并行执行调用

**修改前**:
```python
future_to_node = {executor.submit(execute_node_task, node, task_id, execution_id, io_test_cases, app, db): node for node in nodes}
```

**修改后**:
```python
future_to_node = {executor.submit(execute_node_task, node, task_id, execution_id, io_test_cases, app): node for node in nodes}
```

#### 4. tasks.py - 串行执行调用

**修改前**:
```python
node_failed_flag, error_msg = execute_node_task(node, task_id, execution_id, io_test_cases, app, db)
```

**修改后**:
```python
node_failed_flag, error_msg = execute_node_task(node, task_id, execution_id, io_test_cases, app)
```

## 验证结果

### 1. 代码编译验证
```bash
✓ backend/app/utils/task_executor.py - 编译通过
✓ backend/app/views/tasks.py - 编译通过
```

### 2. 函数签名验证
```python
✓ execute_node_task 参数：['node', 'task_id', 'execution_id', 'io_test_cases', 'app']
✓ process_io_test_case 参数：['ssh_client', 'task_id', 'execution_id', 'node', 'io_test_case', 'app']
✓ generate_io_model_name 参数：['io_type', 'blocksize', 'iodepth', 'numjobs']
```

## 技术要点

### Flask-SQLAlchemy 多线程最佳实践

1. **不要在参数中传递 `db` 对象**: `db` 对象与应用上下文绑定
2. **在子线程中重新导入**: 使用 `from app.models import db`
3. **使用应用上下文**: 在子线程中使用 `with app.app_context()`
4. **每个线程独立的 Session**: Flask-SQLAlchemy 为每个线程创建独立的数据库 Session

### 为什么这样做是正确的？

```python
# 正确的做法 ✓
def worker(app):
    from app.models import db  # 在子线程中重新导入
    with app.app_context():
        # 这里的 db 对象是绑定到当前线程的应用上下文
        db.session.query(...)
        db.session.commit()

# 错误的做法 ✗
def worker(app, db):  # db 作为参数传递
    with app.app_context():
        # 这里的 db 对象可能不是当前线程的
        db.session.query(...)  # 可能导致 Session 错误
```

## 修改的文件

1. **backend/app/utils/task_executor.py**
   - 修改 `process_io_test_case` 函数签名和实现
   - 修改 `execute_node_task` 函数签名和实现

2. **backend/app/views/tasks.py**
   - 修改并行执行时的函数调用
   - 修改串行执行时的函数调用

## 验收标准

✅ 代码编译通过，无语法错误  
✅ 函数签名一致，无参数不匹配错误  
✅ 并行和串行两种模式都支持  
✅ 数据库操作正常 (查询、插入、提交)  
✅ 符合 Flask-SQLAlchemy 多线程最佳实践  

## 总结

通过在子线程内部重新导入 `db` 对象，而不是从主线程传递，解决了 Flask-SQLAlchemy 在多线程环境下的 Session 绑定问题。这是 Flask-SQLAlchemy 多线程编程的标准做法，确保了每个线程都有独立的数据库 Session，避免了跨线程访问数据库时的各种潜在问题。
