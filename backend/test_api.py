import requests
import json

# 先获取JWT令牌
def get_jwt_token():
    login_url = "http://localhost:5002/api/auth/login"
    login_data = {
        "username": "admin",
        "password": "password123"
    }
    
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        return response.json().get('data', {}).get('access_token')
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

# 测试get_realtime_metrics端点
def test_realtime_metrics():
    token = get_jwt_token()
    if not token:
        return
    
    url = "http://localhost:5002/api/logs/task/30/realtime-metrics"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {
        "node_ids": "1",
        "devices": "sda"
    }
    
    response = requests.get(url, headers=headers, params=params)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    test_realtime_metrics()
