#!/usr/bin/env python3
"""
测试任务执行，验证IO类型参数处理
"""

import requests
import json
import time

# 后端API地址
BASE_URL = "http://localhost:5003/api"

# 登录获取token
def login():
    """登录获取JWT token"""
    login_data = {
        "username": "admin",
        "password": "adminpassword"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json().get("data", {}).get("token")
    else:
        print(f"登录失败: {response.text}")
        return None

# 获取所有IO测试用例
def get_all_io_cases(token):
    """获取所有IO测试用例"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(f"{BASE_URL}/io-cases", headers=headers)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"获取IO测试用例失败: {response.text}")
        return []

# 创建测试任务
def create_task(token, name, io_case_ids, node_ids):
    """创建测试任务"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    task_data = {
        "name": name,
        "description": f"测试IO类型执行: {io_case_ids}",
        "io_test_case_ids": io_case_ids,
        "node_ids": node_ids,
        "execution_mode": "parallel"
    }
    response = requests.post(f"{BASE_URL}/tasks", headers=headers, json=task_data)
    return response

# 执行测试任务
def execute_task(token, task_id):
    """执行测试任务"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.post(f"{BASE_URL}/tasks/{task_id}/execute", headers=headers)
    return response

# 获取任务执行状态
def get_task_status(token, task_id):
    """获取任务执行状态"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(f"{BASE_URL}/tasks/{task_id}", headers=headers)
    if response.status_code == 200:
        return response.json().get("data", {})
    else:
        print(f"获取任务状态失败: {response.text}")
        return {}

# 测试任务执行
def test_task_execution():
    """测试任务执行"""
    token = login()
    if not token:
        return
    
    # 获取所有IO测试用例
    io_cases = get_all_io_cases(token)
    if not io_cases:
        print("没有找到IO测试用例")
        return
    
    # 选择我们之前创建的测试用例（包含不同IO类型）
    test_case_ids = []
    for case in io_cases:
        if case.get('name', '').startswith('测试'):
            test_case_ids.append(case.get('id'))
            print(f"选择测试用例: {case.get('name')}, IO类型: {case.get('parameters', {}).get('io_type')}")
    
    if not test_case_ids:
        print("没有找到测试用例")
        return
    
    # 获取所有节点
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(f"{BASE_URL}/nodes", headers=headers)
    nodes = response.json().get("data", [])
    if not nodes:
        print("没有找到节点")
        return
    
    # 只选择节点4
    node_ids = [4]
    print(f"选择节点: {node_ids}")
    
    # 创建测试任务
    print("\n创建测试任务...")
    response = create_task(token, "测试IO类型执行", test_case_ids, node_ids)
    print(f"创建任务结果: {response.status_code}")
    if response.status_code == 201:
        task_id = response.json().get("data", {}).get("id")
        print(f"任务ID: {task_id}")
        
        # 执行测试任务
        print("\n执行测试任务...")
        response = execute_task(token, task_id)
        print(f"执行任务结果: {response.status_code}")
        if response.status_code == 200:
            print("任务开始执行")
            
            # 等待任务执行完成
            print("\n等待任务执行完成...")
            for i in range(60):  # 最多等待60秒
                task_status = get_task_status(token, task_id)
                status = task_status.get('status')
                print(f"任务状态: {status}")
                if status in ['completed', 'failed']:
                    break
                time.sleep(1)
            
            print("\n任务执行完成")
    
if __name__ == "__main__":
    test_task_execution()
