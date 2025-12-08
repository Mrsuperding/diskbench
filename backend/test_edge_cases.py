#!/usr/bin/env python3
"""
测试更新任务的各种边界情况
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

def get_jwt_token():
    login_url = f'{BASE_URL}/auth/login'
    data = {
        'username': USERNAME,
        'password': PASSWORD
    }
    response = requests.post(login_url, json=data)
    if response.status_code != 200:
        return None
    return response.json().get('data', {}).get('token')

def update_task_with_data(token, task_id, data, test_name):
    print(f"\n=== 测试: {test_name} ===")
    print(f"  测试数据: {json.dumps(data, ensure_ascii=False)}")
    
    update_url = f'{BASE_URL}/tasks/{task_id}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.put(update_url, headers=headers, json=data)
        print(f"  响应状态码: {response.status_code}")
        print(f"  响应内容: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"  请求异常: {type(e).__name__}: {e}")
        return False

def main():
    token = get_jwt_token()
    if not token:
        print("获取JWT令牌失败")
        sys.exit(1)
    
    # 获取任务当前信息
    task_url = f'{BASE_URL}/tasks/{TASK_ID}'
    headers = {"Authorization": f'Bearer {token}'}
    task_info = requests.get(task_url, headers=headers).json().get('data')
    
    # 测试用例1: 正常更新（与当前数据相同）
    update_task_with_data(
        token, TASK_ID,
        {
            "name": task_info['name'],
            "description": task_info['description'],
            "node_ids": task_info['node_ids'],
            "io_test_case_ids": task_info['io_test_case_ids'],
            "status": task_info['status'],
            "priority": task_info['priority']
        },
        "正常更新（与当前数据相同）"
    )
    
    # 测试用例2: 空数组的node_ids和io_test_case_ids
    update_task_with_data(
        token, TASK_ID,
        {
            "name": task_info['name'],
            "description": task_info['description'],
            "node_ids": [],
            "io_test_case_ids": [],
            "status": task_info['status'],
            "priority": task_info['priority']
        },
        "空数组的node_ids和io_test_case_ids"
    )
    
    # 测试用例3: 单个节点ID（非数组）
    update_task_with_data(
        token, TASK_ID,
        {
            "name": task_info['name'],
            "description": task_info['description'],
            "node_ids": task_info['node_ids'][0],  # 单个ID而非数组
            "io_test_case_ids": task_info['io_test_case_ids'],
            "status": task_info['status'],
            "priority": task_info['priority']
        },
        "单个节点ID（非数组）"
    )
    
    # 测试用例4: 单个测试用例ID（非数组）
    update_task_with_data(
        token, TASK_ID,
        {
            "name": task_info['name'],
            "description": task_info['description'],
            "node_ids": task_info['node_ids'],
            "io_test_case_ids": task_info['io_test_case_ids'][0],  # 单个ID而非数组
            "status": task_info['status'],
            "priority": task_info['priority']
        },
        "单个测试用例ID（非数组）"
    )
    
    # 测试用例5: 空字符串的task_space_id
    update_task_with_data(
        token, TASK_ID,
        {
            "name": task_info['name'],
            "description": task_info['description'],
            "node_ids": task_info['node_ids'],
            "io_test_case_ids": task_info['io_test_case_ids'],
            "task_space_id": "",  # 空字符串
            "status": task_info['status'],
            "priority": task_info['priority']
        },
        "空字符串的task_space_id"
    )
    
    # 测试用例6: 缺少某些可选字段
    update_task_with_data(
        token, TASK_ID,
        {
            "name": task_info['name'],
            "node_ids": task_info['node_ids'],
            "io_test_case_ids": task_info['io_test_case_ids']
            # 缺少description, status, priority等可选字段
        },
        "缺少某些可选字段"
    )
    
    # 测试用例7: 使用node_id而不是node_ids
    update_task_with_data(
        token, TASK_ID,
        {
            "name": task_info['name'],
            "description": task_info['description'],
            "node_id": task_info['node_ids'][0],  # 使用node_id而不是node_ids
            "io_test_case_ids": task_info['io_test_case_ids'],
            "status": task_info['status'],
            "priority": task_info['priority']
        },
        "使用node_id而不是node_ids"
    )
    
    # 测试用例8: 使用io_test_case_id而不是io_test_case_ids
    update_task_with_data(
        token, TASK_ID,
        {
            "name": task_info['name'],
            "description": task_info['description'],
            "node_ids": task_info['node_ids'],
            "io_test_case_id": task_info['io_test_case_ids'][0],  # 使用io_test_case_id而不是io_test_case_ids
            "status": task_info['status'],
            "priority": task_info['priority']
        },
        "使用io_test_case_id而不是io_test_case_ids"
    )
    
    print("\n=== 所有测试完成 ===")

if __name__ == '__main__':
    main()