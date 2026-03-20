"""
IO 任务日志记录功能测试
测试用户友好的日志记录和 IO 模型名称生成
"""

import requests
import json
import time

# API 基础 URL
BASE_URL = "http://localhost:5004/api"

# 测试配置
TEST_CONFIG = {
    "username": "admin",
    "password": "adminpassword",
    "task_name": "IO 日志测试任务",
    "node_id": 1,
    "io_case_name": "测试 IO 用例"
}

def login():
    """登录获取 JWT token"""
    url = f"{BASE_URL}/auth/login"
    data = {
        "username": TEST_CONFIG["username"],
        "password": TEST_CONFIG["password"]
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]["access_token"]
    return None

def create_io_case(token):
    """创建 IO 测试用例"""
    url = f"{BASE_URL}/io-cases"
    headers = {"Authorization": f"Bearer {token}"}
    
    case_data = {
        "name": TEST_CONFIG["io_case_name"],
        "description": "测试用户友好日志功能",
        "parameters": {
            "block_size": "4,8",
            "queue_depth": "16,32",
            "io_type": ["randread"],
            "read_write_ratio": "100:0",
            "runtime": "30s",
            "size": "1G",
            "time_based": False,
            "ioengine": "libaio",
            "direct": True,
            "sync": False,
            "numjobs": "1"
        }
    }
    
    response = requests.post(url, json=case_data, headers=headers)
    print(f"创建 IO 用例响应：{response.status_code}")
    print(f"响应内容：{json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]["id"]
    return None

def create_test_task(token, io_case_id):
    """创建测试任务"""
    url = f"{BASE_URL}/tasks"
    headers = {"Authorization": f"Bearer {token}"}
    
    task_data = {
        "name": TEST_CONFIG["task_name"],
        "description": "测试用户友好的日志记录功能",
        "node_ids": [TEST_CONFIG["node_id"]],
        "io_case_ids": [io_case_id],
        "execution_mode": "serial"
    }
    
    response = requests.post(url, json=task_data, headers=headers)
    print(f"创建任务响应：{response.status_code}")
    print(f"响应内容：{json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]["id"]
    return None

def execute_task(token, task_id):
    """执行任务"""
    url = f"{BASE_URL}/tasks/{task_id}/execute"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(url, headers=headers)
    print(f"执行任务响应：{response.status_code}")
    print(f"响应内容：{json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    
    return response.status_code == 200

def get_task_logs(task_id):
    """获取任务日志"""
    url = f"{BASE_URL}/tasks/{task_id}/logs"
    
    response = requests.get(url)
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result.get("data", [])
    return []

def test_io_model_name_generation():
    """测试 IO 模型名称生成"""
    print("\n=== 测试 IO 模型名称生成 ===")
    
    # 测试不同的参数组合
    test_cases = [
        ("randread", "4k", "16", "1", "4k_16d_randread_1n"),
        ("read", "8", "32", "2", "8k_32d_read_2n"),
        ("randwrite", "128k", "64", "4", "128k_64d_randwrite_4n"),
    ]
    
    # 直接导入函数
    import sys
    sys.path.insert(0, r'd:\delvelop_project\ai_project\diskbench_pro2\diskbench_pro2\backend')
    from app.utils.task_executor import generate_io_model_name
    
    for io_type, blocksize, iodepth, numjobs, expected in test_cases:
        result = generate_io_model_name(io_type, blocksize, iodepth, numjobs)
        status = "✓" if result == expected else "✗"
        print(f"{status} IO 类型={io_type}, 块大小={blocksize}, 队列深度={iodepth}, 并发数={numjobs}")
        print(f"  期望：{expected}, 实际：{result}")
        
        if result != expected:
            print(f"  错误：IO 模型名称不匹配!")
            return False
    
    print("\nIO 模型名称生成测试通过!\n")
    return True

def test_task_execution():
    """测试任务执行和日志记录"""
    print("\n=== 测试任务执行和日志记录 ===")
    
    # 1. 登录
    print("1. 登录...")
    token = login()
    if not token:
        print("登录失败!")
        return False
    print("登录成功!\n")
    
    # 2. 创建 IO 用例
    print("2. 创建 IO 用例...")
    io_case_id = create_io_case(token)
    if not io_case_id:
        print("创建 IO 用例失败!")
        return False
    print(f"IO 用例创建成功，ID: {io_case_id}\n")
    
    # 3. 创建任务
    print("3. 创建任务...")
    task_id = create_test_task(token, io_case_id)
    if not task_id:
        print("创建任务失败!")
        return False
    print(f"任务创建成功，ID: {task_id}\n")
    
    # 4. 执行任务
    print("4. 执行任务...")
    if not execute_task(token, task_id):
        print("执行任务失败!")
        return False
    print("任务执行成功!\n")
    
    # 5. 等待任务执行完成
    print("5. 等待任务执行完成...")
    time.sleep(5)
    
    # 6. 获取任务日志
    print("6. 获取任务日志...")
    logs = get_task_logs(task_id)
    
    if logs:
        print(f"获取到 {len(logs)} 条日志:")
        for log in logs[:10]:  # 只显示前 10 条
            print(f"  - [{log.get('level')}] {log.get('message')[:100]}")
        
        # 验证日志中是否包含用户友好的信息
        user_friendly_keywords = [
            "上传 fio 工具",
            "开始执行 IO 模型",
            "执行 FIO 命令",
            "完成 IO 模型",
            "使用 IO 分区"
        ]
        
        found_keywords = []
        for keyword in user_friendly_keywords:
            for log in logs:
                if keyword in log.get('message', ''):
                    found_keywords.append(keyword)
                    break
        
        print(f"\n发现用户友好的日志关键字：{found_keywords}")
        
        if len(found_keywords) >= 3:
            print("\n✓ 用户友好的日志记录功能正常!")
            return True
        else:
            print("\n✗ 用户友好的日志记录功能不完整!")
            return False
    else:
        print("未获取到任务日志!")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("IO 任务日志记录功能测试")
    print("=" * 60)
    
    # 测试 IO 模型名称生成
    io_model_test_passed = test_io_model_name_generation()
    
    # 测试任务执行和日志记录
    # task_test_passed = test_task_execution()
    
    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"  IO 模型名称生成测试：{'通过' if io_model_test_passed else '失败'}")
    # print(f"  任务执行测试：{'通过' if task_test_passed else '失败'}")
    print("=" * 60)
