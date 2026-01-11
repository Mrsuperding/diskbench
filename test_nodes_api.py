import requests

# 测试节点API
try:
    # 使用正确的JWT令牌
    headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczNjU5MTY1NiwianRpIjoiNzI3NjY4NjgtNmEzNC00YjUxLTljYzAtZjI0OGNkMDUyMzlkIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6NzAsIm5iZiI6MTczNjU5MTY1NiwiZXhwIjoxNzM2Njc4MDU2fQ.mC0BmPzr0ZkRjH4pPZ8FjL5nL8mN0O1P2Q3R4S5T6U7V8W9X0Y1Z2'
    }
    
    # 发送GET请求获取节点列表
    response = requests.get('http://localhost:5002/api/nodes', headers=headers)
    
    print(f'Status code: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        print(f'Response data:')
        print(f'  Success: {data.get("success")}')
        print(f'  Message: {data.get("message")}')
        print(f'  Nodes count: {len(data.get("data", []))}')
        print(f'  Nodes:')
        for node in data.get("data", []):
            print(f'    - ID: {node.get("id")}, Name: {node.get("name")}, IP: {node.get("ip_address")}, Status: {node.get("status")}, Type: {node.get("type")}')
    else:
        print(f'Error response: {response.text}')
        
except Exception as e:
    print(f'Error: {e}')
