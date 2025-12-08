import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 直接导入app.py文件
import importlib.util

# 指定app.py文件的路径
spec = importlib.util.spec_from_file_location("app_module", os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"))
app_module = importlib.util.module_from_spec(spec)
sys.modules["app_module"] = app_module
spec.loader.exec_module(app_module)

# 从app_module中获取app和db
app = app_module.app
db = app_module.db

# 导入模型
from app.models.test_task import TestTask

with app.app_context():
    # 查询任务ID为3的状态
    task = TestTask.query.get(3)
    if task:
        print(f'Task ID: {task.id}')
        print(f'Task Name: {task.name}')
        print(f'Task Status: {task.status}')
        print(f'Task Created At: {task.created_at}')
        print(f'Task Started At: {task.started_at}')
        print(f'Task Completed At: {task.completed_at}')
    else:
        print('Task with ID 3 not found')