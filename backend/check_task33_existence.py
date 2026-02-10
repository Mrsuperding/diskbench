# 检查task 33的存在性
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 直接导入app.py模块
import app as app_module
from app.models import db, TestTask, TaskExecution, TestLog

app = app_module.create_app()

with app.app_context():
    print("检查task 33的存在性...")
    
    # 检查测试任务
    task = TestTask.query.get(33)
    if task:
        print(f"找到task 33: {task.name}")
        print(f"状态: {task.status}")
        print(f"创建时间: {task.created_at}")
        print(f"完成时间: {task.completed_at}")
        
        # 检查执行实例
        executions = TaskExecution.query.filter_by(task_id=33).all()
        print(f"\n执行实例: {len(executions)} 个")
        for execution in executions:
            print(f"  ID: {execution.id}, 状态: {execution.status}")
            print(f"  日志文件路径: {execution.log_file_path}")
            
            # 检查日志文件是否存在
            if execution.log_file_path:
                print(f"  文件存在: {os.path.exists(execution.log_file_path)}")
                if os.path.exists(execution.log_file_path):
                    print(f"  文件大小: {os.path.getsize(execution.log_file_path)} bytes")
    else:
        print("未找到task 33")
    
    # 检查所有测试任务
    print("\n检查所有测试任务...")
    tasks = TestTask.query.order_by(TestTask.id.desc()).limit(10).all()
    print(f"最近的10个测试任务:")
    for t in tasks:
        print(f"  ID: {t.id}, 名称: {t.name}, 状态: {t.status}")
    
    # 检查日志目录
    print("\n检查日志目录...")
    log_dirs = [
        '/tmp/io_platform_logs',
        'd:\\tmp\\io_platform_logs',
        os.path.join(os.path.expanduser('~'), 'io_platform_logs')
    ]
    
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            print(f"日志目录存在: {log_dir}")
            files = os.listdir(log_dir)
            print(f"  文件数量: {len(files)}")
            # 显示前5个文件
            for file in files[:5]:
                print(f"  - {file}")
        else:
            print(f"日志目录不存在: {log_dir}")
