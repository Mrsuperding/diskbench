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
    logs = TestLog.query.filter_by(log_type='fio').all()
    print(f'FIO日志总数: {len(logs)}')
    
    for log in logs[:10]:
        print(f'\nID: {log.id}, 任务ID: {log.test_task_id}, 节点ID: {log.node_id}')
        print(f'文件路径: {log.log_path}')
        print(f'文件名: {log.log_filename}')
        print(f'文件存在: {os.path.exists(log.log_path)}')
        
        if os.path.exists(log.log_path):
            print(f'文件大小: {os.path.getsize(log.log_path)} bytes')
            
            # 读取文件内容
            try:
                with open(log.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    print(f'\n文件内容 (前500字符):')
                    print(content[:500])
                    
                    # 检查是否是JSON格式
                    if log.log_filename.endswith('.json'):
                        try:
                            data = json.loads(content)
                            print(f'\nJSON解析成功，键: {list(data.keys())}')
                        except json.JSONDecodeError as e:
                            print(f'\nJSON解析失败: {e}')
            except Exception as e:
                print(f'读取文件错误: {e}')
