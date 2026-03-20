import sys
sys.path.append('.')
from app import app
from app.models import TestTask, TestLog

with app.app_context():
    # 获取所有测试任务
    tasks = TestTask.query.all()
    print(f'现有测试任务数量: {len(tasks)}')
    
    for task in tasks:
        print(f'任务ID: {task.id}, 名称: {task.name}, 状态: {task.status}')
        
        # 获取该任务的所有日志
        logs = TestLog.query.filter_by(test_task_id=task.id).all()
        print(f'  日志数量: {len(logs)}')
        for log in logs:
            print(f'  日志ID: {log.id}, 类型: {log.log_type}, 文件名: {log.log_filename}')
