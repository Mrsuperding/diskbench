import requests
import json

# 测试节点API（包含登录）
try:
    # 1. 首先登录获取JWT令牌
    print("Step 1: 登录获取JWT令牌")
    login_data = {
        "username": "admin",
        "password": "adminpassword"
    }
    
    login_response = requests.post('http://localhost:5002/api/auth/login', json=login_data)
    print(f'Login status code: {login_response.status_code}')
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        if login_result.get('success'):
            access_token = login_result.get('data', {}).get('token')
            print(f'Login successful, token: {access_token}')
            
            # 2. 使用获取的令牌测试节点API
            print("\nStep 2: 测试节点API")
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # 发送GET请求获取节点列表
            nodes_response = requests.get('http://localhost:5002/api/nodes', headers=headers)
            
            print(f'Nodes API status code: {nodes_response.status_code}')
            
            if nodes_response.status_code == 200:
                nodes_data = nodes_response.json()
                print(f'Nodes API response:')
                print(f'  Success: {nodes_data.get("success")}')
                print(f'  Message: {nodes_data.get("message")}')
                print(f'  Nodes count: {len(nodes_data.get("data", []))}')
                print(f'  Nodes:')
                for node in nodes_data.get("data", []):
                    print(f'    - ID: {node.get("id")}, Name: {node.get("name")}, IP: {node.get("ip_address")}, Status: {node.get("status")}, Type: {node.get("type")}')
            else:
                print(f'Nodes API error response: {nodes_response.text}')
        else:
            print(f'Login failed: {login_result.get("message")}')
    else:
        print(f'Login error: {login_response.text}')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
