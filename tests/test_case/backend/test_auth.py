import pytest
import requests
import json

class TestAuthBackendAPI:
    """后端认证API测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        self.base_url = "http://localhost:5003/api"
        self.test_data = {
            "username": "testuser_auth",
            "email": "test_auth@example.com",
            "password": "test123456"
        }
    
    def test_register(self, api_client):
        """测试注册API"""
        print("开始测试：注册API")
        
        # 发送注册请求
        response = api_client.post(
            f"{self.base_url}/auth/register",
            json=self.test_data
        )
        
        # 验证响应状态码
        assert response.status_code in [200, 400], f"注册请求失败，状态码: {response.status_code}"
        
        # 验证响应数据
        response_data = response.json()
        if response.status_code == 200:
            assert "message" in response_data, "响应中缺少message字段"
            assert "user" in response_data, "响应中缺少user字段"
            assert response_data["user"]["username"] == self.test_data["username"], "用户名不匹配"
            print("注册API测试通过")
        else:
            assert "message" in response_data, "响应中缺少message字段"
            print(f"注册API测试：{response_data['message']}")
    
    def test_login(self, api_client):
        """测试登录API"""
        print("开始测试：登录API")
        
        # 先注册用户（如果还没有注册）
        register_response = api_client.post(
            f"{self.base_url}/auth/register",
            json=self.test_data
        )
        
        # 发送登录请求
        login_data = {
            "username": self.test_data["username"],
            "password": self.test_data["password"]
        }
        response = api_client.post(
            f"{self.base_url}/auth/login",
            json=login_data
        )
        
        # 验证响应状态码
        assert response.status_code == 200, f"登录请求失败，状态码: {response.status_code}"
        
        # 验证响应数据
        response_data = response.json()
        assert "data" in response_data, "响应中缺少data字段"
        assert "token" in response_data["data"], "响应中缺少token字段"
        assert "user" in response_data["data"], "响应中缺少user字段"
        assert response_data["data"]["user"]["username"] == self.test_data["username"], "用户名不匹配"
        
        print("登录API测试通过")
    
    def test_login_invalid_credentials(self, api_client):
        """测试使用无效凭证登录"""
        print("开始测试：无效凭证登录")
        
        # 发送登录请求，使用错误的密码
        invalid_data = {
            "username": self.test_data["username"],
            "password": "wrong_password"
        }
        response = api_client.post(
            f"{self.base_url}/auth/login",
            json=invalid_data
        )
        
        # 验证响应状态码
        assert response.status_code == 401, f"预期状态码401，实际: {response.status_code}"
        
        # 验证响应数据
        response_data = response.json()
        assert "message" in response_data, "响应中缺少message字段"
        print("无效凭证登录测试通过")
    
    def test_register_duplicate_username(self, api_client):
        """测试注册重复的用户名"""
        print("开始测试：重复用户名注册")
        
        # 先注册用户
        api_client.post(
            f"{self.base_url}/auth/register",
            json=self.test_data
        )
        
        # 再次使用相同的用户名注册
        duplicate_data = {
            "username": self.test_data["username"],
            "email": f"different_{self.test_data['email']}",
            "password": self.test_data["password"]
        }
        response = api_client.post(
            f"{self.base_url}/auth/register",
            json=duplicate_data
        )
        
        # 验证响应状态码
        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        
        # 验证响应数据
        response_data = response.json()
        assert "message" in response_data, "响应中缺少message字段"
        print("重复用户名注册测试通过")