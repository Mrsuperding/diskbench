# 检查task 33的日志记录
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 直接导入app.py模块
import app as app_module
from app.models import db, TestTask, TaskExecution

app = app_module.create_app()

with app.app_context():
    print("检查task 33的记录...")
    
    # 检查测试任务表
    task = TestTask.query.get(33)
    if task:
        print(f"找到task 33: {task.name}")
        print(f"状态: {task.status}")
        print(f"创建时间: {task.created_at}")
        print(f"完成时间: {task.completed_at}")
        
        # 检查任务执行实例
        executions = TaskExecution.query.filter_by(task_id=33).all()
        print(f"\n找到 {len(executions)} 个执行实例:")
        for execution in executions:
            print(f"  执行ID: {execution.id}, 状态: {execution.status}")
            print(f"  开始时间: {execution.started_at}")
            print(f"  完成时间: {execution.completed_at}")
            print(f"  日志文件路径: {execution.log_file_path}")
    else:
        print("未找到task 33的记录")
    
    # 检查log相关的表
    print("\n检查可能的日志表...")
    
    # 尝试查询可能存在的log表
    try:
        # 检查是否有fio_logs或类似的表
        from app.models import FioLog
        logs = FioLog.query.filter_by(task_id=33).all()
        print(f"找到 {len(logs)} 个Fio日志记录")
        for log in logs:
            print(f"  日志ID: {log.id}, 设备: {log.device}")
            print(f"  开始时间: {log.io_start_time}")
            print(f"  结束时间: {log.io_end_time}")
    except ImportError:
        print("FioLog模型未找到")
    except Exception as e:
        print(f"查询日志表时出错: {str(e)}")
