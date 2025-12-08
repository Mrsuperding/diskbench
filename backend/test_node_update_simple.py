import requests
import json

# 服务器地址
BASE_URL = "http://127.0.0.1:5000/api"

# 用户登录信息
LOGIN_DATA = {
    "username": "admin",
    "password": "adminpassword"
}

def main():
    """简单测试节点更新功能"""
    print("=== 简单节点更新测试 ===")
    
    # 登录获取令牌
    print("\n1. 登录...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json=LOGIN_DATA)
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.text}")
        return
    
    login_data = login_response.json()
    if not login_data.get("success"):
        print(f"登录失败: {login_data.get('message')}")
        return
    
    access_token = login_data.get("data", {}).get("token")
    if not access_token:
        print("获取令牌失败")
        return
    
    print("登录成功")
    
    # 设置请求头
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 获取节点列表
    print("\n2. 获取节点列表...")
    nodes_response = requests.get(f"{BASE_URL}/nodes", headers=headers)
    if nodes_response.status_code != 200:
        print(f"获取节点列表失败: {nodes_response.text}")
        return
    
    nodes_data = nodes_response.json()
    if not nodes_data.get("success"):
        print(f"获取节点列表失败: {nodes_data.get('message')}")
        return
    
    nodes = nodes_data.get("data", [])
    if len(nodes) < 2:
        print("需要至少2个节点进行测试")
        return
    
    print(f"可用节点: {[node['id'] for node in nodes]}")
    
    # 创建测试任务
    print("\n3. 创建测试任务...")
    create_data = {
        "name": "Simple Test Task",
        "node_ids": [nodes[0]['id']],
        "io_test_case_ids": [4]
    }
    
    create_response = requests.post(f"{BASE_URL}/tasks", json=create_data, headers=headers)
    if create_response.status_code != 201:
        print(f"创建任务失败: {create_response.text}")
        return
    
    create_result = create_response.json()
    if not create_result.get("success"):
        print(f"创建任务失败: {create_result.get('message')}")
        return
    
    task = create_result.get("data")
    task_id = task['id']
    print(f"任务创建成功: ID={task_id}, 初始节点: {task['node_ids']}")
    
    # 测试节点更新
    print("\n4. 更新节点（增加一个节点）...")
    update_data = {
        "node_ids": [nodes[0]['id'], nodes[1]['id']]
    }
    
    update_response = requests.put(f"{BASE_URL}/tasks/{task_id}", json=update_data, headers=headers)
    if update_response.status_code != 200:
        print(f"更新任务失败: {update_response.text}")
        return
    
    update_result = update_response.json()
    if not update_result.get("success"):
        print(f"更新任务失败: {update_result.get('message')}")
        return
    
    updated_task = update_result.get("data")
    print(f"任务更新成功: ID={updated_task['id']}, 更新后节点: {updated_task['node_ids']}")
    
    # 验证更新结果
    print("\n5. 验证更新结果...")
    get_response = requests.get(f"{BASE_URL}/tasks/{task_id}", headers=headers)
    if get_response.status_code != 200:
        print(f"获取任务失败: {get_response.text}")
        return
    
    get_result = get_response.json()
    if not get_result.get("success"):
        print(f"获取任务失败: {get_result.get('message')}")
        return
    
    retrieved_task = get_result.get("data")
    expected_nodes = sorted([nodes[0]['id'], nodes[1]['id']])
    actual_nodes = sorted(retrieved_task['node_ids'])
    
    if expected_nodes == actual_nodes:
        print("✅ 节点更新验证成功！")
        print(f"   预期节点: {expected_nodes}")
        print(f"   实际节点: {actual_nodes}")
    else:
        print("❌ 节点更新验证失败！")
        print(f"   预期节点: {expected_nodes}")
        print(f"   实际节点: {actual_nodes}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()