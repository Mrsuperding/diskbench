import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 从app.py中导入create_app函数
from app import create_app
from app.models import TestLog
import json

# 创建应用实例
app = create_app()

# 在应用上下文中运行查询
with app.app_context():
    # 查询任务33的所有FIO日志记录
    logs = TestLog.query.filter_by(test_task_id=33, log_type='fio').all()
    print(f'Found {len(logs)} FIO logs for task 33')
    
    for log in logs:
        print(f'\nLog ID: {log.id}')
        print(f'Node ID: {log.node_id}')
        print(f'Log path: {log.log_path}')
        print(f'Log filename: {log.log_filename}')
        print(f'File exists: {os.path.exists(log.log_path)}')
        
        # 如果文件存在，检查文件大小和完整内容
        if os.path.exists(log.log_path):
            print(f'File size: {os.path.getsize(log.log_path)} bytes')
            
            # 检查文件名中的设备信息
            import re
            device_match = re.search(r'_(\w+)\.(log|json)$', log.log_filename)
            if device_match:
                device = device_match.group(1)
                print(f'Extracted device from filename: {device}')
            else:
                print(f'No device found in filename')
