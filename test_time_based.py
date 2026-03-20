import requests
import json

# API基本信息
BASE_URL = 'http://localhost:5000/api'

# 登录获取token
def login():
    login_data = {
        "username": "admin",
        "password": "admin123"
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

# 主函数
if __name__ == "__main__":
    token = login()
    if token:
        test_case = create_test_case(token)
        if test_case:
            print(f"测试用例ID: {test_case['id']}")
            print(f"测试用例名称: {test_case['name']}")
            print(f"time_based选项: {test_case['parameters']['time_based']}")
