#!/usr/bin/env python3
"""
调试API更新任务功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

# 配置
BASE_URL = 'http://localhost:5000/api'
TASK_ID = 11
USERNAME = 'admin'
PASSWORD = 'adminpassword'

# 获取JWT令牌
def get_jwt_token():
    print("1. 获取JWT令牌...")
    login_url = f'{BASE_URL}/auth/login'
    data = {
        'username': USERNAME,
        'password': PASSWORD
    }
    
    response = requests.post(login_url, json=data)
    if response.status_code != 200:
        print(f"  登录失败: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    if not data.get('success'):
        print(f"  登录失败: {data.get('message')}")
        return None
    token = data.get('data', {}).get('token')
    print(f"  登录成功，获取到令牌")
    return token

# 获取任务当前信息
def get_task_info(token):
    print(f"\n2. 获取任务ID={TASK_ID}当前信息...")
    task_url = f'{BASE_URL}/tasks/{TASK_ID}'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.get(task_url, headers=headers)
    if response.status_code != 200:
        print(f"  获取任务信息失败: {response.status_code} - {response.text}")
        return None
    
    task_info = response.json().get('data')
    print(f"  任务名称: {task_info['name']}")
    print(f"  当前节点ID: {task_info['node_ids']}")
    print(f"  当前测试用例ID: {task_info['io_test_case_ids']}")
    return task_info

# 更新任务
def update_task(token, task_info):
    print(f"\n3. 尝试更新任务ID={TASK_ID}...")
    update_url = f'{BASE_URL}/tasks/{TASK_ID}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 准备更新数据（与前端发送的格式相同）
    update_data = {
        "name": task_info['name'],
        "description": task_info['description'],
        "node_ids": [1, 2],  # 保持不变
        "io_test_case_ids": [2],  # 保持不变
        "status": task_info['status'],
        "priority": task_info['priority']
    }
    
    print(f"  更新数据: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.put(update_url, headers=headers, json=update_data)
        print(f"  更新请求响应状态码: {response.status_code}")
        print(f"  更新请求响应: {response.text}")
        
        if response.status_code == 200:
            print("  任务更新成功！")
            return True
        else:
            print("  任务更新失败！")
            return False
    except Exception as e:
        print(f"  更新请求异常: {type(e).__name__}: {e}")
        return False

# 主函数
def main():
    print("=== API更新任务调试 ===")
    
    # 获取JWT令牌
    token = get_jwt_token()
    if not token:
        sys.exit(1)
    
    # 获取任务当前信息
    task_info = get_task_info(token)
    if not task_info:
        sys.exit(1)
    
    # 更新任务
    update_task(token, task_info)
    
    print("\n=== 调试完成 ===")

if __name__ == '__main__':
    main()