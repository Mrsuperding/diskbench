import pytest
import requests
import json
from loguru import logger

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
    
    def teardown_method(self):
        """测试后的清理"""
        # 清理测试创建的用户
        try:
            # 这里需要根据实际的API或数据库操作来实现用户删除
            # 示例：发送删除用户的API请求
            import requests
            # 先登录获取token
            login_data = {
                "username": self.test_data["username"],
                "password": self.test_data["password"]
            }
            login_response = requests.post(
                f"{self.base_url}/auth/login",
                json=login_data
            )
            if login_response.status_code == 200:
                token = login_response.json()["data"]["token"]
                # 发送删除用户请求（假设API支持）
                delete_response = requests.delete(
                    f"{self.base_url}/users/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if delete_response.status_code == 200:
                    logger.info(f"成功删除测试用户: {self.test_data['username']}")
                else:
                    logger.warning(f"删除用户失败: {delete_response.status_code}")
        except Exception as e:
            logger.error(f"清理测试数据时出错: {e}")
    
    def test_register(self, api_client):
        """测试注册API"""
        logger.info("开始测试：注册API")
        logger.info(f"用户名称:  {self.test_data['username']}")
        logger.info(f"用户邮箱:  {self.test_data['email']}")
        # 发送注册请求
        response = api_client.post(
            f"{self.base_url}/auth/register",
            json=self.test_data
        )
        
        logger.info(f"注册响应状态码: {response.status_code}")
        logger.info(f"注册响应内容: {response.text}")
        
        # 验证响应状态码
        assert response.status_code in [200, 400], f"注册请求失败，状态码: {response.status_code}"
        
        # 验证响应数据
        response_data = response.json()
        if response.status_code == 200:
            assert "message" in response_data, "响应中缺少message字段"
            assert "user" in response_data, "响应中缺少user字段"
            assert response_data["user"]["username"] == self.test_data["username"], "用户名不匹配"
            logger.info("注册API测试通过")
        else:
            assert "message" in response_data, "响应中缺少message字段"
            logger.info(f"注册API测试：{response_data['message']}")
    
    def test_login(self, api_client):
        """测试登录API"""
        logger.info("开始测试：登录API")
        
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
        
        logger.info(f"登录响应状态码: {response.status_code}")
        logger.info(f"登录响应内容: {response.text}")
        
        # 验证响应状态码
        assert response.status_code == 200, f"登录请求失败，状态码: {response.status_code}"
        
        # 验证响应数据
        response_data = response.json()
        assert "data" in response_data, "响应中缺少data字段"
        assert "token" in response_data["data"], "响应中缺少token字段"
        assert "user" in response_data["data"], "响应中缺少user字段"
        assert response_data["data"]["user"]["username"] == self.test_data["username"], "用户名不匹配"
        
        logger.info("登录API测试通过")
    
    def test_login_invalid_credentials(self, api_client):
        """测试使用无效凭证登录"""
        logger.info("开始测试：无效凭证登录")
        
        # 发送登录请求，使用错误的密码
        invalid_data = {
            "username": self.test_data["username"],
            "password": "wrong_password"
        }
        response = api_client.post(
            f"{self.base_url}/auth/login",
            json=invalid_data
        )
        
        logger.info(f"登录响应状态码: {response.status_code}")
        logger.info(f"登录响应内容: {response.text}")
        
        # 验证响应状态码
        assert response.status_code == 401, f"预期状态码401，实际: {response.status_code}"
        
        # 验证响应数据
        response_data = response.json()
        assert "message" in response_data, "响应中缺少message字段"
        logger.info("无效凭证登录测试通过")
    
    def test_register_duplicate_username(self, api_client):
        """测试注册重复的用户名"""
        logger.info("开始测试：重复用户名注册")
        
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
        
        logger.info(f"注册响应状态码: {response.status_code}")
        logger.info(f"注册响应内容: {response.text}")
        
        # 验证响应状态码
        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        
        # 验证响应数据
        response_data = response.json()
        assert "message" in response_data, "响应中缺少message字段"
        logger.info("重复用户名注册测试通过")