#!/usr/bin/env python3
"""
诊断脚本 - 检查任务日志系统配置
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_configuration():
    """检查配置"""
    print("=" * 70)
    print("任务日志系统诊断")
    print("=" * 70)
    print()

    # 1. 检查导入
    print("1. 检查导入...")
    try:
        from app.views.socket_events import send_task_log, global_socketio
        print("   ✓ send_task_log 导入成功")
        print(f"   ✓ global_socketio 当前状态: {global_socketio}")
    except Exception as e:
        print(f"   ✗ 导入失败: {e}")
        return

    # 2. 检查tasks.py中是否导入了send_task_log
    print("\n2. 检查 tasks.py 导入...")
    try:
        with open('app/views/tasks.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'from app.views.socket_events import send_task_log' in content:
                print("   ✓ tasks.py 已导入 send_task_log")
            else:
                print("   ✗ tasks.py 未导入 send_task_log")

            # 检查是否有send_task_log调用
            if 'send_task_log(' in content:
                count = content.count('send_task_log(')
                print(f"   ✓ tasks.py 中有 {count} 处调用 send_task_log")
            else:
                print("   ✗ tasks.py 中没有调用 send_task_log")
    except Exception as e:
        print(f"   ✗ 检查失败: {e}")

    # 3. 检查task_executor.py
    print("\n3. 检查 task_executor.py 导入...")
    try:
        with open('app/utils/task_executor.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'from app.views.socket_events import send_task_log' in content:
                print("   ✓ task_executor.py 已导入 send_task_log")
            else:
                print("   ✗ task_executor.py 未导入 send_task_log")

            # 检查是否有send_task_log调用
            if 'send_task_log(' in content:
                count = content.count('send_task_log(')
                print(f"   ✓ task_executor.py 中有 {count} 处调用 send_task_log")
            else:
                print("   ✗ task_executor.py 中没有调用 send_task_log")
    except Exception as e:
        print(f"   ✗ 检查失败: {e}")

    # 4. 检查application.py中的SocketIO注册
    print("\n4. 检查 application.py 配置...")
    try:
        with open('application.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'socketio = SocketIO' in content:
                print("   ✓ SocketIO 已初始化")
            else:
                print("   ✗ SocketIO 未初始化")

            if 'register_socket_events(socketio)' in content:
                print("   ✓ Socket事件已注册")
            else:
                print("   ✗ Socket事件未注册")
    except Exception as e:
        print(f"   ✗ 检查失败: {e}")

    # 5. 检查前端WebSocket连接配置
    print("\n5. 检查前端 WebSocket 配置...")
    try:
        with open('../frontend/src/views/TaskDetail.vue', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'io("http://localhost:5003"' in content:
                print("   ✓ 前端 WebSocket 地址: http://localhost:5003")
            else:
                print("   ✗ 前端 WebSocket 地址配置可能有误")

            if 'socket.value.on("task_log"' in content:
                print("   ✓ 前端已监听 task_log 事件")
            else:
                print("   ✗ 前端未监听 task_log 事件")
    except Exception as e:
        print(f"   ✗ 检查失败: {e}")

    print("\n" + "=" * 70)
    print("诊断完成")
    print("=" * 70)
    print()
    print("建议:")
    print("1. 确保后端服务在 5003 端口运行")
    print("2. 重启后端服务: python application.py")
    print("3. 打开浏览器 Console (F12) 查看 WebSocket 连接状态")
    print("4. 运行测试任务，观察后端日志输出")
    print()

if __name__ == '__main__':
    check_configuration()
