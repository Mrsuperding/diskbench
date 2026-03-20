import requests
import json
import time

# API基本信息
BASE_URL = 'http://localhost:5003/api'

# 登录获取token
def login():
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    response = requests.post(f'{BASE_URL}/auth/login', json=login_data)
    if response.status_code == 200:
        return response.json()['data']['access_token']
    else:
        print(f"登录失败: {response.text}")
        return None

# 创建测试用例
def create_test_case(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_case_data = {
        "name": "Time Based Test Case",
        "description": "测试time_based选项是否正常工作",
        "parameters": {
            "template_id": None,
            "block_size": "4",
            "queue_depth": "16",
            "io_type": "randread",
            "read_write_ratio": "100:0",
            "runtime": 30,
            "size": "1G",
            "partitions": "",
            "time_based": True  # 勾选time_based选项
        }
    }
    
    response = requests.post(f'{BASE_URL}/io-cases', json=test_case_data, headers=headers)
    if response.status_code == 201:
        print("测试用例创建成功")
        return response.json()['data']
    else:
        print(f"创建测试用例失败: {response.text}")
        return None

# 创建任务
def create_task(token, test_case_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    task_data = {
        "name": "Time Based Test Task",
        "description": "测试time_based选项的任务",
        "io_test_case_ids": [test_case_id],
        "node_ids": []  # 空节点列表，仅测试参数传递
    }
    
    response = requests.post(f'{BASE_URL}/tasks', json=task_data, headers=headers)
    if response.status_code == 201:
        print("任务创建成功")
        return response.json()['data']
    else:
        print(f"创建任务失败: {response.text}")
        return None

# 执行任务
def execute_task(token, task_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f'{BASE_URL}/tasks/{task_id}/execute', headers=headers)
    if response.status_code == 200:
        print("任务开始执行")
        return response.json()['data']
    else:
        print(f"执行任务失败: {response.text}")
        return None

# 获取任务日志
def get_task_logs(token, task_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f'{BASE_URL}/tasks/{task_id}/logs', headers=headers)
    if response.status_code == 200:
        return response.json()['data']
    else:
        print(f"获取任务日志失败: {response.text}")
        return []

# 主函数
if __name__ == "__main__":
    token = login()
    if token:
        # 创建测试用例
        test_case = create_test_case(token)
        if test_case:
            print(f"测试用例ID: {test_case['id']}")
            print(f"测试用例名称: {test_case['name']}")
            print(f"time_based选项: {test_case['parameters']['time_based']}")
            
            # 创建任务
            task = create_task(token, test_case['id'])
            if task:
                print(f"任务ID: {task['id']}")
                print(f"任务名称: {task['name']}")
                
                # 执行任务
                execute_result = execute_task(token, task['id'])
                if execute_result:
                    print(f"任务执行状态: {execute_result['status']}")
                    
                    # 等待一段时间，让任务开始执行
                    print("等待任务执行...")
                    time.sleep(5)
                    
                    # 获取任务日志
                    logs = get_task_logs(token, task['id'])
                    print(f"获取到 {len(logs)} 条日志")
                    
                    # 检查日志中是否包含time_based参数
                    found_time_based = False
                    for log in logs:
                        if 'fio' in log['content'] and 'time_based' in log['content']:
                            print("找到time_based参数在日志中:")
                            print(log['content'])
                            found_time_based = True
                            break
                    
                    if found_time_based:
                        print("测试成功: time_based参数正确添加到fio命令中")
                    else:
                        print("测试失败: 未在日志中找到time_based参数")
                        # 打印所有日志，便于调试
                        print("所有日志:")
                        for log in logs:
                            print(log['content'])
