# 测试创建具有重复IP地址的节点
import requests
import json

# 配置
BASE_URL = "http://localhost:5002"
USERNAME = "testuser_20260111024557"
PASSWORD = "testpassword123"

# 登录获取JWT token
def login():
    print("登录获取JWT token...")
    url = f"{BASE_URL}/api/auth/login"
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    response = requests.post(url, json=data)
    
    print(f"登录响应状态码: {response.status_code}")
    print(f"登录响应内容: {response.text}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"解析响应数据: {data}")
            
            # 检查返回结构
            if data.get("data") and data.get("data").get("token"):
                token = data.get("data").get("token")
                print(f"✓ 登录成功，获取到token: {token[:20]}...")
                return token
            else:
                print(f"响应数据结构不正确: {data}")
                return None
        except Exception as e:
            print(f"解析响应失败: {e}")
            return None
    else:
        print(f"✗ 登录失败: {response.status_code} {response.text}")
        return None

# 创建节点
def create_node(token, name, ip_address, login_credential_id):
    print(f"\n创建节点: {name} (IP: {ip_address})")
    url = f"{BASE_URL}/api/nodes"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "name": name,
        "ip_address": ip_address,
        "login_credential_id": login_credential_id
    }
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 201:
        node = response.json().get("data")
        print(f"✓ 节点创建成功! ID: {node['id']}, IP: {node['ip_address']}")
        return node
    else:
        print(f"✗ 节点创建失败: {response.status_code} {response.text}")
        return None

# 获取节点列表
def get_nodes(token):
    print("\n获取所有节点...")
    url = f"{BASE_URL}/api/nodes"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        nodes = response.json().get("data", [])
        print(f"✓ 获取到 {len(nodes)} 个节点")
        for node in nodes:
            print(f"  ID: {node['id']}, 名称: {node['name']}, IP: {node['ip_address']}")
        return nodes
    else:
        print(f"✗ 获取节点列表失败: {response.status_code} {response.text}")
        return []

# 主函数
def main():
    # 登录
    token = login()
    if not token:
        return
    
    # 获取现有节点
    get_nodes(token)
    
    # 假设已经有一个具有127.0.0.1 IP的节点，现在创建另一个具有相同IP的节点
    # 注意：需要替换为实际存在的login_credential_id
    login_credential_id = 1  # 这个ID需要是数据库中实际存在的登录凭证ID
    
    # 创建第一个节点
    node1 = create_node(token, "测试节点1", "127.0.0.1", login_credential_id)
    
    # 创建第二个具有相同IP的节点
    node2 = create_node(token, "测试节点2", "127.0.0.1", login_credential_id)
    
    # 再次获取节点列表查看结果
    get_nodes(token)

if __name__ == "__main__":
    main()