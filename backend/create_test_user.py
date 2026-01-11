# 创建测试用户
import requests
import json

# 配置
BASE_URL = "http://localhost:5002"

# 注册新用户
def register_user():
    print("创建测试用户...")
    url = f"{BASE_URL}/api/auth/register"
    
    # 生成唯一的用户名
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    username = f"testuser_{timestamp}"
    email = f"{username}@example.com"
    password = "testpassword123"
    
    data = {
        "username": username,
        "email": email,
        "password": password,
        "role": "user"
    }
    
    response = requests.post(url, json=data)
    
    if response.status_code == 201:
        user = response.json().get("data")
        print(f"✓ 用户创建成功! 用户名: {username}, 密码: {password}")
        return username, password
    else:
        print(f"✗ 用户创建失败: {response.status_code} {response.text}")
        return None, None

# 主函数
def main():
    username, password = register_user()
    if username and password:
        print(f"\n请使用以下凭据登录:")
        print(f"用户名: {username}")
        print(f"密码: {password}")

if __name__ == "__main__":
    main()