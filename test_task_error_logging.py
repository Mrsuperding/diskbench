#!/usr/bin/env python3
"""
测试任务执行失败原因记录与返回
"""

import requests
import json
import time

BASE_URL = 'http://localhost:5003/api'
# 添加认证Token
AUTH_TOKEN = 'your_jwt_token_here'  # 需要替换为实际的JWT Token

# 测试任务执行失败的场景
def test_task_execution_failure():
    print("测试任务执行失败原因记录与返回")
    print("=" * 50)
    
    # 1. 测试节点连接失败的场景
    print("\n1. 测试节点连接失败的场景")
    test_node_connection_failure()
    
    # 2. 测试IO测试执行失败的场景
    print("\n2. 测试IO测试执行失败的场景")
    test_io_test_failure()
    
    # 3. 测试任务被取消的场景
    print("\n3. 测试任务被取消的场景")
    test_task_cancellation()

# 测试节点连接失败的场景
def test_node_connection_failure():
    try:
        # 创建一个任务，使用一个不存在的节点
        task_data = {
            "name": "测试节点连接失败",
            "node_ids": [999],  # 不存在的节点ID
            "io_test_case_ids": [1],
            "description": "测试节点连接失败的错误信息记录"
        }
        
        response = requests.post(f"{BASE_URL}/tasks", json=task_data, headers={"Content-Type": "application/json"})
        if response.status_code == 201:
            task_id = response.json()['data']['id']
            print(f"创建任务成功，任务ID: {task_id}")
            
            # 执行任务
            execute_response = requests.post(f"{BASE_URL}/tasks/{task_id}/execute")
            if execute_response.status_code == 200:
                print("任务开始执行")
                
                # 等待任务执行完成
                time.sleep(10)
                
                # 获取任务详情
                task_response = requests.get(f"{BASE_URL}/tasks/{task_id}")
                if task_response.status_code == 200:
                    task_detail = task_response.json()['data']
                    print(f"任务状态: {task_detail['status']}")
                    if task_detail['status'] == 'failed':
                        print(f"任务失败原因: {task_detail.get('error_message', '无错误信息')}")
                    else:
                        print("任务状态不是失败，可能需要更多时间执行")
                else:
                    print(f"获取任务详情失败: {task_response.text}")
            else:
                print(f"执行任务失败: {execute_response.text}")
        else:
            print(f"创建任务失败: {response.text}")
    except Exception as e:
        print(f"测试节点连接失败场景时出错: {str(e)}")

# 测试IO测试执行失败的场景
def test_io_test_failure():
    try:
        # 创建一个任务，使用一个会导致IO测试失败的IO用例
        task_data = {
            "name": "测试IO测试失败",
            "node_ids": [1],  # 假设节点1存在
            "io_test_case_ids": [1],  # 假设IO用例1存在
            "description": "测试IO测试失败的错误信息记录"
        }
        
        response = requests.post(f"{BASE_URL}/tasks", json=task_data, headers={"Content-Type": "application/json"})
        if response.status_code == 201:
            task_id = response.json()['data']['id']
            print(f"创建任务成功，任务ID: {task_id}")
            
            # 执行任务
            execute_response = requests.post(f"{BASE_URL}/tasks/{task_id}/execute")
            if execute_response.status_code == 200:
                print("任务开始执行")
                
                # 等待任务执行完成
                time.sleep(15)
                
                # 获取任务详情
                task_response = requests.get(f"{BASE_URL}/tasks/{task_id}")
                if task_response.status_code == 200:
                    task_detail = task_response.json()['data']
                    print(f"任务状态: {task_detail['status']}")
                    if task_detail['status'] == 'failed':
                        print(f"任务失败原因: {task_detail.get('error_message', '无错误信息')}")
                    else:
                        print("任务状态不是失败，可能需要更多时间执行")
                else:
                    print(f"获取任务详情失败: {task_response.text}")
            else:
                print(f"执行任务失败: {execute_response.text}")
        else:
            print(f"创建任务失败: {response.text}")
    except Exception as e:
        print(f"测试IO测试失败场景时出错: {str(e)}")

# 测试任务被取消的场景
def test_task_cancellation():
    try:
        # 创建一个任务
        task_data = {
            "name": "测试任务取消",
            "node_ids": [1],  # 假设节点1存在
            "io_test_case_ids": [1],  # 假设IO用例1存在
            "description": "测试任务被取消的错误信息记录"
        }
        
        response = requests.post(f"{BASE_URL}/tasks", json=task_data, headers={"Content-Type": "application/json"})
        if response.status_code == 201:
            task_id = response.json()['data']['id']
            print(f"创建任务成功，任务ID: {task_id}")
            
            # 执行任务
            execute_response = requests.post(f"{BASE_URL}/tasks/{task_id}/execute")
            if execute_response.status_code == 200:
                print("任务开始执行")
                
                # 等待一段时间后取消任务
                time.sleep(2)
                cancel_response = requests.post(f"{BASE_URL}/tasks/{task_id}/pause")
                if cancel_response.status_code == 200:
                    print("任务已取消")
                    
                    # 等待任务状态更新
                    time.sleep(5)
                    
                    # 获取任务详情
                    task_response = requests.get(f"{BASE_URL}/tasks/{task_id}")
                    if task_response.status_code == 200:
                        task_detail = task_response.json()['data']
                        print(f"任务状态: {task_detail['status']}")
                        if task_detail['status'] == 'cancelled':
                            print(f"任务取消原因: {task_detail.get('error_message', '无错误信息')}")
                        else:
                            print("任务状态不是取消，可能需要更多时间更新")
                    else:
                        print(f"获取任务详情失败: {task_response.text}")
                else:
                    print(f"取消任务失败: {cancel_response.text}")
            else:
                print(f"执行任务失败: {execute_response.text}")
        else:
            print(f"创建任务失败: {response.text}")
    except Exception as e:
        print(f"测试任务取消场景时出错: {str(e)}")

if __name__ == "__main__":
    test_task_execution_failure()
