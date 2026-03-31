#!/usr/bin/env python3
"""
测试任务日志发送功能
用于验证send_task_log是否正常工作
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.views.socket_events import send_task_log

def test_send_task_log():
    """测试发送任务日志"""
    app = create_app('development')

    with app.app_context():
        print("测试发送任务日志...")

        # 测试发送日志
        task_id = 1  # 使用一个测试任务ID

        # 发送几条测试日志
        print(f"发送任务开始日志...")
        send_task_log(task_id, "⏳ 任务开始：测试任务",
                     level='INFO',
                     context={'operation': 'task_start', 'stage': '任务开始'})

        print(f"发送节点准备日志...")
        send_task_log(task_id, "📡 节点 192.168.1.100 - 正在准备测试环境...",
                     level='INFO',
                     context={'operation': 'node_prepare', 'stage': '节点准备'})

        print(f"发送工具上传日志...")
        send_task_log(task_id, "📡 节点 192.168.1.100 - 正在上传FIO工具...",
                     level='INFO',
                     context={'operation': 'upload_tool', 'stage': '工具上传'})

        print(f"发送完成日志...")
        send_task_log(task_id, "🎉 任务完成：所有节点测试完成",
                     level='INFO',
                     context={'operation': 'task_completed', 'stage': '任务完成'})

        print("测试完成！")
        print("如果WebSocket已连接，前端应该能看到这些日志")

if __name__ == '__main__':
    test_send_task_log()
