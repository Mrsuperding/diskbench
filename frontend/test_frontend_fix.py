#!/usr/bin/env python3
"""
测试前端修复后的多节点更新功能
模拟前端表单提交，验证node_ids参数能正确更新任务节点
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:5000/api"

# 用户登录信息
LOGIN_DATA = {
    "username": "admin",
    "password": "adminpassword"
}

def login():
    """登录获取token"""
    print("1. 登录系统...")
    login_url = f"{BASE_URL}/auth/login"
    response = requests.post(login_url, json=LOGIN_DATA)
    
    if response.status_code != 200:
        print(f"登录失败: {response.status_code} {response.text}")
        return None
    
    result = response.json()
    if not result.get("success"):
        print(f"登录失败: {result.get('message')}")
        return None
    
    token = result.get("data", {}).get("token")
    if not token:
        print("无法获取访问令牌")
        return None
    
    print("登录成功，获取到访问令牌")
    return token

def get_nodes(headers):
    """获取节点列表"""
    print("\n2. 获取节点列表...")
    url = f"{BASE_URL}/nodes"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"获取节点列表失败: {response.status_code} {response.text}")
        return []
    
    result = response.json()
    if not result.get("success"):
        print(f"获取节点列表失败: {result.get('message')}")
        return []
    
    nodes = result.get("data", [])
    print(f"获取到 {len(nodes)} 个节点")
    
    # 打印节点信息
    for node in nodes:
        print(f"   节点 {node['id']}: {node['name']} - {node['ip_address']}")
    
    return nodes

def get_test_cases(headers):
    """获取测试用例列表"""
    print("\n3. 获取测试用例列表...")
    url = f"{BASE_URL}/io-cases"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"获取测试用例列表失败: {response.status_code} {response.text}")
        return []
    
    result = response.json()
    if not result.get("success"):
        print(f"获取测试用例列表失败: {result.get('message')}")
        return []
    
    test_cases = result.get("data", [])
    print(f"获取到 {len(test_cases)} 个测试用例")
    
    # 打印测试用例信息
    for test_case in test_cases:
        print(f"   测试用例 {test_case['id']}: {test_case['name']}")
    
    return test_cases

def create_task(headers, node_ids, io_test_case_id=1):
    """创建测试任务"""
    print("\n3. 创建测试任务...")
    
    # 模拟前端修复后的表单数据（新格式 - node_ids）
    task_data = {
        "name": "前端测试任务",
        "description": "用于测试前端修复的任务",
        "node_ids": node_ids,  # 新格式 - 复数，数组
        "io_test_case_ids": [io_test_case_id],
        "status": "pending",
        "priority": "medium"
    }
    
    print(f"提交的任务数据（新格式）: {json.dumps(task_data, indent=2, ensure_ascii=False)}")
    
    url = f"{BASE_URL}/tasks"
    response = requests.post(url, json=task_data, headers=headers)
    
    if response.status_code != 201:
        print(f"创建任务失败: {response.status_code} {response.text}")
        return None
    
    result = response.json()
    if not result.get("success"):
        print(f"创建任务失败: {result.get('message')}")
        return None
    
    task = result.get("data")
    print(f"任务创建成功: ID={task['id']}, 节点ID={task['node_ids']}")
    return task

def update_task_with_node_ids(headers, task_id, node_ids, io_test_case_id):
    """使用node_ids更新任务节点（修复后的格式）"""
    print(f"\n4. 更新任务节点 - 测试修复后的node_ids格式...")
    
    # 模拟前端修复后的表单数据（新格式 - node_ids）
    update_data = {
        "name": "更新后的前端测试任务",
        "description": "更新了节点的测试任务",
        "node_ids": node_ids,  # 新格式 - 复数，数组
        "io_test_case_ids": [io_test_case_id],  # 使用实际存在的测试用例ID
        "status": "pending",
        "priority": "medium"
    }
    
    print(f"提交的更新数据（新格式）: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
    
    url = f"{BASE_URL}/tasks/{task_id}"
    response = requests.put(url, json=update_data, headers=headers)
    
    if response.status_code != 200:
        print(f"更新任务失败: {response.status_code} {response.text}")
        return None
    
    result = response.json()
    if not result.get("success"):
        print(f"更新任务失败: {result.get('message')}")
        return None
    
    updated_task = result.get("data")
    print(f"任务更新成功: ID={updated_task['id']}, 节点ID={updated_task['node_ids']}")
    return updated_task

def main():
    """主函数"""
    print("=== 前端修复验证测试 ===")
    
    # 登录获取token
    token = login()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 获取节点列表
    nodes = get_nodes(headers)
    if len(nodes) < 2:
        print("\n❌ 错误: 需要至少2个节点才能测试多节点更新功能")
        return
    
    # 获取测试用例列表
    test_cases = get_test_cases(headers)
    if len(test_cases) == 0:
        print("\n❌ 错误: 需要至少1个测试用例才能创建任务")
        return
    
    # 创建测试任务（使用修复后的node_ids格式）
    task = create_task(headers, [nodes[0]['id']], test_cases[0]['id'])
    if not task:
        return
    
    # 测试修复后的node_ids格式更新
    updated_task = update_task_with_node_ids(headers, task['id'], [nodes[0]['id'], nodes[1]['id']], test_cases[0]['id'])
    if not updated_task:
        return
    
    # 验证结果
    print(f"\n5. 验证结果...")
    expected_nodes = [nodes[0]['id'], nodes[1]['id']]
    actual_nodes = updated_task['node_ids']
    
    if sorted(expected_nodes) == sorted(actual_nodes):
        print("✅ 验证成功！前端修复后的node_ids格式能正确更新任务节点")
        print(f"   预期节点: {sorted(expected_nodes)}")
        print(f"   实际节点: {sorted(actual_nodes)}")
    else:
        print("❌ 验证失败！节点更新未达到预期")
        print(f"   预期节点: {sorted(expected_nodes)}")
        print(f"   实际节点: {sorted(actual_nodes)}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()