#!/usr/bin/env python3
"""
实时测试任务日志发送
用于验证WebSocket是否能正常发送日志到前端
"""

import sys
import os
import time

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_real_time_log():
    """实时测试发送任务日志"""
    from flask import Flask
    from flask_socketio import SocketIO
    from app.views.socket_events import register_socket_events, send_task_log

    # 创建应用
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test_secret_key'

    # 创建SocketIO实例
    socketio = SocketIO(app, cors_allowed_origins="*")

    # 注册事件
    register_socket_events(socketio)

    @app.route('/test')
    def test():
        return 'Test Server Running'

    print("=" * 60)
    print("测试服务器已启动")
    print("地址: http://localhost:5004")
    print("=" * 60)
    print()
    print("请执行以下步骤:")
    print("1. 打开浏览器访问任务详情页面")
    print("2. 确保WebSocket已连接到 http://localhost:5003")
    print("3. 输入任务ID，按回车开始发送测试日志")
    print()

    # 在后台运行socketio服务器
    import threading
    def run_server():
        socketio.run(app, host='0.0.0.0', port=5004, debug=False, use_reloader=False)

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    time.sleep(2)  # 等待服务器启动

    while True:
        try:
            task_id = input("输入任务ID (或输入 q 退出): ").strip()
            if task_id.lower() == 'q':
                break

            if not task_id.isdigit():
                print("请输入有效的任务ID")
                continue

            task_id = int(task_id)

            print(f"\n开始向任务 {task_id} 发送测试日志...")
            print("-" * 60)

            with app.app_context():
                # 发送一系列测试日志
                logs = [
                    ("任务开始", "INFO"),
                    ("节点 192.168.1.100 - 上传工具阶段", "INFO"),
                    ("节点 192.168.1.100 - 执行IO模型：4k_16d_randread_1n", "INFO"),
                    ("节点 192.168.1.100 - 收集日志阶段", "INFO"),
                    ("节点 192.168.1.100 - 执行IO模型：4k_32d_randwrite_1n", "INFO"),
                    ("节点 192.168.1.100 - 收集日志阶段", "INFO"),
                    ("任务完成", "INFO"),
                ]

                for i, (message, level) in enumerate(logs, 1):
                    send_task_log(
                        task_id=task_id,
                        log_content=message,
                        level=level,
                        context={'operation': 'test', 'stage': f'测试阶段{i}'}
                    )
                    print(f"✓ 已发送: {message}")
                    time.sleep(0.5)  # 间隔发送

            print("-" * 60)
            print(f"✓ 已向任务 {task_id} 发送 {len(logs)} 条测试日志")
            print("请检查前端页面是否显示这些日志\n")

        except KeyboardInterrupt:
            print("\n测试中断")
            break
        except Exception as e:
            print(f"发送失败: {e}")

    print("\n测试结束")

if __name__ == '__main__':
    test_real_time_log()
