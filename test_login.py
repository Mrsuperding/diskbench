#!/usr/bin/env python3
# 测试登录获取JWT token

import requests
import json

# 测试登录的函数
def test_login():
    """测试登录获取JWT token"""
    # API URL
    url = "http://localhost:5004/api/auth/login"
    
    # 请求数据
    data = {
        "username": "admin",
        "password": "adminpassword"
    }
    
    # 请求头
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        # 发送POST请求
        response = requests.post(url, json=data, headers=headers)
        
        # 打印响应结果
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        return response.status_code, response.json()
    except Exception as e:
        print(f"请求出错: {str(e)}")
        return None, str(e)

if __name__ == "__main__":
    print("测试登录获取JWT token...")
    status_code, response = test_login()
    
    if status_code == 200:
        print("登录成功！")
        print(f"获取到的token: {response.get('data', {}).get('access_token')}")
    else:
        print("登录失败，需要检查用户名和密码。")
