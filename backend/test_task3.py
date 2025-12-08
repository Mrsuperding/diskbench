import sys
import os
sys.path.insert(0, os.path.abspath('.'))

# 导入app.py中的create_app函数
import importlib.util

# 指定app.py的路径
spec = importlib.util.spec_from_file_location("app", "app.py")
app_module = importlib.util.module_from_spec(spec)
sys.modules["app"] = app_module
spec.loader.exec_module(app_module)
create_app = app_module.create_app

from app.models import db, TestTask, TestResult

# 创建应用
app = create_app()

with app.app_context():
    # 检查任务ID=3是否存在
    task = TestTask.query.get(3)
    if task:
        print(f"任务ID=3存在: {task.name}")
        
        # 检查是否有相关的测试结果
        results = TestResult.query.filter_by(test_task_id=3).all()
        print(f"任务ID=3的测试结果数量: {len(results)}")
        for result in results:
            print(f"结果ID: {result.id}, 状态: {result.status}")
    else:
        print("任务ID=3不存在")
        
        # 列出所有任务
        all_tasks = TestTask.query.all()
        print(f"所有任务: {[f'Task {t.id}: {t.name}' for t in all_tasks]}")