import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:5000/api"

# 用户登录信息
LOGIN_DATA = {
    "username": "admin",
    "password": "adminpassword"
}

def login():
    """登录获取访问令牌"""
    print("正在登录...")
    print(f"登录URL: {BASE_URL}/auth/login")
    print(f"登录数据: {LOGIN_DATA}")
    response = requests.post(f"{BASE_URL}/auth/login", json=LOGIN_DATA)
    print(f"登录响应状态码: {response.status_code}")
    print(f"登录响应内容: {response.text}")
    if response.status_code != 200:
        print(f"登录失败: {response.status_code} {response.text}")
        return None
    
    data = response.json()
    print(f"登录响应JSON: {data}")
    if data.get("success"):
        access_token = data.get("data", {}).get("token")
        print(f"登录成功，访问令牌: {access_token}")
        return access_token
    else:
        print(f"登录失败: {data.get("message")}")
        return None

def get_task(task_id, headers):
    """获取任务详情"""
    print(f"\n获取任务详情: ID={task_id}")
    response = requests.get(f"{BASE_URL}/tasks/{task_id}", headers=headers)
    if response.status_code != 200:
        print(f"获取任务失败: {response.status_code} {response.text}")
        return None
    
    data = response.json()
    if data.get("success"):
        task = data.get("data")
        print(f"任务信息: ID={task['id']}, Name={task['name']}, Node IDs={task['node_ids']}")
        return task
    else:
        print(f"获取任务失败: {data.get("message")}")
        return None

def update_task(task_id, data, headers):
    """更新任务信息"""
    print(f"\n更新任务: ID={task_id}")
    print(f"更新数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    response = requests.put(f"{BASE_URL}/tasks/{task_id}", json=data, headers=headers)
    if response.status_code != 200:
        print(f"更新任务失败: {response.status_code} {response.text}")
        return None
    
    data = response.json()
    if data.get("success"):
        task = data.get("data")
        print(f"任务更新成功: ID={task['id']}, Name={task['name']}, Node IDs={task['node_ids']}")
        return task
    else:
        print(f"更新任务失败: {data.get("message")}")
        return None

def get_node_list(headers):
    """获取节点列表"""
    print("\n获取节点列表...")
    response = requests.get(f"{BASE_URL}/nodes", headers=headers)
    if response.status_code != 200:
        print(f"获取节点列表失败: {response.status_code} {response.text}")
        return []
    
    data = response.json()
    if data.get("success"):
        nodes = data.get("data", [])
        print(f"可用节点 ({len(nodes)}):")
        for node in nodes:
            print(f"  ID: {node['id']}, Name: {node['name']}")
        return nodes
    else:
        print(f"获取节点列表失败: {data.get("message")}")
        return []

def main():
    """主函数"""
    # 登录获取令牌
    access_token = login()
    if not access_token:
        return
    
    print("登录后，开始获取节点列表...")
    
    # 设置请求头
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 获取节点列表
    nodes = get_node_list(headers)
    print(f"获取节点列表返回: {nodes}")
    if len(nodes) < 2:
        print(f"\n需要至少2个节点来测试节点更新功能，当前有 {len(nodes)} 个节点")
        return
    
    # 创建一个测试任务（如果没有现成的）
    print("\n创建测试任务...")
    create_data = {
        "name": "Test Edit Task",
        "description": "Task for testing edit functionality",
        "node_ids": [nodes[0]['id']],  # 先只添加一个节点
        "io_test_case_ids": [4]  # 使用现有的测试用例
    }
    
    create_response = requests.post(f"{BASE_URL}/tasks", json=create_data, headers=headers)
    if create_response.status_code != 201:
        print(f"创建任务失败: {create_response.status_code} {create_response.text}")
        return
    
    create_data = create_response.json()
    if not create_data.get("success"):
        print(f"创建任务失败: {create_data.get("message")}")
        return
    
    task = create_data.get("data")
    task_id = task['id']
    print(f"任务创建成功: ID={task_id}, Node IDs={task['node_ids']}")
    
    # 测试更新任务，增加一个节点
    print("\n=== 测试1: 增加节点 ===")
    update_data = {
        "name": "Updated Test Edit Task",
        "node_ids": [nodes[0]['id'], nodes[1]['id']]  # 增加一个节点
    }
    
    updated_task = update_task(task_id, update_data, headers)
    if not updated_task:
        return
    
    # 验证更新后的任务节点信息
    print("\n=== 验证任务节点信息 ===")
    retrieved_task = get_task(task_id, headers)
    if not retrieved_task:
        return
    
    expected_node_ids = sorted([nodes[0]['id'], nodes[1]['id']])
    actual_node_ids = sorted(retrieved_task['node_ids'])
    
    if expected_node_ids == actual_node_ids:
        print("✅ 节点信息更新成功！")
        print(f"   预期节点ID: {expected_node_ids}")
        print(f"   实际节点ID: {actual_node_ids}")
    else:
        print("❌ 节点信息更新失败！")
        print(f"   预期节点ID: {expected_node_ids}")
        print(f"   实际节点ID: {actual_node_ids}")
    
    # 测试更新任务，减少节点
    print("\n=== 测试2: 减少节点 ===")
    update_data = {
        "node_ids": [nodes[1]['id']]  # 只保留第二个节点
    }
    
    updated_task = update_task(task_id, update_data, headers)
    if not updated_task:
        return
    
    # 验证更新后的任务节点信息
    print("\n=== 验证任务节点信息 ===")
    retrieved_task = get_task(task_id, headers)
    if not retrieved_task:
        return
    
    expected_node_ids = sorted([nodes[1]['id']])
    actual_node_ids = sorted(retrieved_task['node_ids'])
    
    if expected_node_ids == actual_node_ids:
        print("✅ 节点信息更新成功！")
        print(f"   预期节点ID: {expected_node_ids}")
        print(f"   实际节点ID: {actual_node_ids}")
    else:
        print("❌ 节点信息更新失败！")
        print(f"   预期节点ID: {expected_node_ids}")
        print(f"   实际节点ID: {actual_node_ids}")
    
    print("\n所有测试完成！")

if __name__ == "__main__":
    main()