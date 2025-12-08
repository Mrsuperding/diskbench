# 测试创建并执行新任务的脚本
import sys
import os
import requests

# 设置基础URL
base_url = "http://localhost:5000"

# 登录获取token
def login():
    login_url = f"{base_url}/api/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            return response.json().get("token")
        else:
            print(f"登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"登录请求异常: {e}")
        return None

# 创建新任务
def create_new_task(token):
    create_url = f"{base_url}/api/tasks"
    
    task_data = {
        "name": "测试任务",
        "description": "用于测试任务执行的新任务",
        "task_space_id": 1,  # 假设使用默认任务空间
        "priority": "medium",
        "nodes": [1],  # 假设使用ID为1的节点
        "io_test_cases": [1],  # 假设使用ID为1的IO测试用例
        "model_ids": [1]  # 假设使用ID为1的模型
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(create_url, json=task_data, headers=headers)
        if response.status_code == 201:
            task = response.json().get("data")
            print(f"成功创建任务: ID {task['id']}, 名称 {task['name']}, 状态 {task['status']}")
            return task
        else:
            print(f"创建任务失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"创建任务请求异常: {e}")
        return None

# 执行任务
def execute_task(token, task_id):
    execute_url = f"{base_url}/api/tasks/{task_id}/execute"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(execute_url, headers=headers)
        if response.status_code == 200:
            print(f"成功执行任务 {task_id}")
            return True
        else:
            print(f"执行任务失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"执行任务请求异常: {e}")
        return False

# 获取任务状态
def get_task_status(token, task_id):
    status_url = f"{base_url}/api/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(status_url, headers=headers)
        if response.status_code == 200:
            task = response.json().get("data")
            print(f"任务 {task_id} 状态: {task['status']}")
            return task['status']
        else:
            print(f"获取任务状态失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"获取任务状态请求异常: {e}")
        return None

# 主函数
def main():
    print("=== 测试任务执行流程 ===")
    
    # 登录
    token = login()
    if not token:
        return
    
    # 创建新任务
    task = create_new_task(token)
    if not task:
        return
    
    # 获取任务状态（应该是pending）
    status = get_task_status(token, task['id'])
    if status != "pending":
        print(f"任务状态不是预期的'pending'，而是'{status}'")
        return
    
    # 执行任务
    if execute_task(token, task['id']):
        # 获取更新后的任务状态
        get_task_status(token, task['id'])
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    main()