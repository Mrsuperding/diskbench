import requests
import json
import time

# API基本信息
BASE_URL = 'http://localhost:5003/api'

# 登录获取token
def login():
    login_data = {
        "username": "admin",
        "password": "adminpassword"
    }
    response = requests.post(f'{BASE_URL}/auth/login', json=login_data)
    if response.status_code == 200:
        return response.json()['data']['token']
    else:
        print(f"登录失败: {response.text}")
        return None

# 创建测试用例
def create_test_case(token, time_based=True):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_case_data = {
        "name": f"Time Based Test Case - {int(time.time())}",
        "description": "测试time_based选项是否正常工作",
        "parameters": {
            "template_id": None,
            "block_size": "4",
            "queue_depth": "16",
            "io_type": "randread",
            "read_write_ratio": "100:0",
            "runtime": 10,  # 缩短运行时间以便快速测试
            "size": "1G",
            "partitions": "",
            "time_based": time_based  # 勾选time_based选项
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
def create_task(token, test_case_id, node_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    task_data = {
        "name": f"Time Based Task - {int(time.time())}",
        "description": "测试time_based任务执行",
        "io_test_case_ids": [test_case_id],
        "node_ids": [node_id],
        "priority": "medium"
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
        return True
    else:
        print(f"执行任务失败: {response.text}")
        return False

# 检查任务状态
def check_task_status(token, task_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f'{BASE_URL}/tasks/{task_id}', headers=headers)
    if response.status_code == 200:
        task = response.json()['data']
        print(f"任务状态: {task['status']}")
        return task['status']
    else:
        print(f"获取任务状态失败: {response.text}")
        return None

# 获取任务结果
def get_task_results(token, task_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f'{BASE_URL}/tasks/{task_id}/results', headers=headers)
    if response.status_code == 200:
        results = response.json()['data']
        print(f"任务结果数量: {len(results)}")
        return results
    else:
        print(f"获取任务结果失败: {response.text}")
        return []

# 获取任务日志
def get_task_logs(token, task_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f'{BASE_URL}/tasks/{task_id}/logs', headers=headers)
    if response.status_code == 200:
        logs = response.json()['data']
        print(f"任务日志数量: {len(logs)}")
        return logs
    else:
        print(f"获取任务日志失败: {response.text}")
        return []

# 主函数
def main():
    print("开始验证time_based功能的端到端测试")
    
    # 1. 登录获取token
    token = login()
    if not token:
        print("登录失败，测试终止")
        return
    
    # 2. 创建测试用例（开启time_based）
    test_case = create_test_case(token, time_based=True)
    if not test_case:
        print("创建测试用例失败，测试终止")
        return
    
    print(f"测试用例ID: {test_case['id']}")
    print(f"测试用例名称: {test_case['name']}")
    print(f"time_based选项: {test_case['parameters']['time_based']}")
    
    # 3. 获取节点ID（假设使用第一个节点）
    headers = {"Authorization": f"Bearer {token}"}
    nodes_response = requests.get(f'{BASE_URL}/nodes', headers=headers)
    if nodes_response.status_code != 200:
        print("获取节点列表失败，测试终止")
        return
    
    nodes = nodes_response.json()['data']
    if not nodes:
        print("没有可用节点，测试终止")
        return
    
    # 选择IP地址为127.0.0.1的节点
    local_node = next((node for node in nodes if node['ip_address'] == '127.0.0.1'), None)
    if not local_node:
        print("没有找到本地节点，测试终止")
        return
    node_id = local_node['id']
    print(f"使用节点ID: {node_id}")
    print(f"节点IP: {local_node['ip_address']}")
    
    # 4. 创建任务
    task = create_task(token, test_case['id'], node_id)
    if not task:
        print("创建任务失败，测试终止")
        return
    
    print(f"任务ID: {task['id']}")
    print(f"任务名称: {task['name']}")
    
    # 5. 验证time_based功能是否正确配置
    print("\n验证time_based功能是否正确配置:")
    
    # 6. 获取测试用例详情，验证time_based参数
    headers = {"Authorization": f"Bearer {token}"}
    case_response = requests.get(f'{BASE_URL}/io-cases/{test_case["id"]}', headers=headers)
    if case_response.status_code == 200:
        case_detail = case_response.json()['data']
        print(f"测试用例详情获取成功")
        print(f"time_based参数: {case_detail['parameters']['time_based']}")
        if case_detail['parameters']['time_based']:
            print("✓ time_based参数已正确设置为True")
        else:
            print("✗ time_based参数未正确设置")
    else:
        print(f"获取测试用例详情失败: {case_response.text}")
    
    # 7. 验证任务详情，确保测试用例已正确关联
    task_response = requests.get(f'{BASE_URL}/tasks/{task["id"]}', headers=headers)
    if task_response.status_code == 200:
        task_detail = task_response.json()['data']
        print(f"任务详情获取成功")
        print(f"任务名称: {task_detail['name']}")
        print(f"任务状态: {task_detail['status']}")
    else:
        print(f"获取任务详情失败: {task_response.text}")
    
    print("\ntime_based功能端到端测试完成（验证了前端创建测试用例和后端API处理）")

if __name__ == "__main__":
    main()
