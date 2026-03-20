#!/usr/bin/env python3
"""
测试IO类型参数处理修复
"""

import requests
import json

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

# 创建测试用例
def create_io_case(token, name, io_type):
    """创建IO测试用例"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    case_data = {
        "name": name,
        "description": f"测试IO类型: {io_type}",
        "parameters": {
            "block_size": "4",
            "queue_depth": "16",
            "io_type": io_type,
            "read_write_ratio": "100:0",
            "runtime": "60s",
            "size": "1G",
            "time_based": False,
            "ioengine": "libaio",
            "direct": True,
            "sync": False,
            "numjobs": "1"
        }
    }
    response = requests.post(f"{BASE_URL}/io-cases", headers=headers, json=case_data)
    return response

# 获取测试用例
def get_io_case(token, case_id):
    """获取IO测试用例"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(f"{BASE_URL}/io-cases/{case_id}", headers=headers)
    return response

# 测试不同IO类型
def test_io_types():
    """测试不同IO类型的处理"""
    token = login()
    if not token:
        return
    
    # 测试用例1：IO类型为["write"]
    print("测试1: IO类型为['write']")
    response = create_io_case(token, "测试写模式", ["write"])
    print(f"创建结果: {response.status_code}")
    if response.status_code == 201:
        case_id = response.json().get("data", {}).get("id")
        get_response = get_io_case(token, case_id)
        if get_response.status_code == 200:
            case_data = get_response.json().get("data", {})
            print(f"保存的io_type: {case_data.get('parameters', {}).get('io_type')}")
    print()
    
    # 测试用例2：IO类型为["randread", "randwrite"]
    print("测试2: IO类型为['randread', 'randwrite']")
    response = create_io_case(token, "测试随机读写", ["randread", "randwrite"])
    print(f"创建结果: {response.status_code}")
    if response.status_code == 201:
        case_id = response.json().get("data", {}).get("id")
        get_response = get_io_case(token, case_id)
        if get_response.status_code == 200:
            case_data = get_response.json().get("data", {})
            print(f"保存的io_type: {case_data.get('parameters', {}).get('io_type')}")
    print()
    
    # 测试用例3：IO类型为["rw"]
    print("测试3: IO类型为['rw']")
    response = create_io_case(token, "测试混合读写", ["rw"])
    print(f"创建结果: {response.status_code}")
    if response.status_code == 201:
        case_id = response.json().get("data", {}).get("id")
        get_response = get_io_case(token, case_id)
        if get_response.status_code == 200:
            case_data = get_response.json().get("data", {})
            print(f"保存的io_type: {case_data.get('parameters', {}).get('io_type')}")
    print()

if __name__ == "__main__":
    test_io_types()
