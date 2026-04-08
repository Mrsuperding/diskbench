"""登录凭证 API 测试

测试登录凭证相关的所有API端点：
- GET /api/login-credentials - 获取登录凭证列表
- GET /api/login-credentials/<id> - 获取单个登录凭证
- POST /api/login-credentials - 创建登录凭证
- PUT /api/login-credentials/<id> - 更新登录凭证
- DELETE /api/login-credentials/<id> - 删除登录凭证
- POST /api/login-credentials/<id>/test - 测试登录凭证连接
"""

import pytest
import requests
import random
import string
import time
from loguru import logger


class TestLoginCredentialsAPI:
    """登录凭证 API 测试类"""

    def setup_method(self):
        """测试前的设置"""
        self.base_url = "http://localhost:5003/api"
        self.test_user = {
            "username": "test_admin_cred",
            "email": "test_admin_cred@example.com",
            "password": "test123456"
        }
        self.token = None
        self.created_credentials = []

    def teardown_method(self):
        """测试后的清理"""
        if self.token:
            for cred_id in self.created_credentials:
                try:
                    requests.delete(
                        f"{self.base_url}/login-credentials/{cred_id}",
                        headers={"Authorization": f"Bearer {self.token}"},
                        timeout=5
                    )
                    logger.info(f"成功删除登录凭证: {cred_id}")
                except Exception as e:
                    logger.warning(f"删除登录凭证失败: {cred_id}, {e}")

    def _register_and_login(self):
        """注册并登录，获取token"""
        # 注册用户
        register_response = requests.post(
            f"{self.base_url}/auth/register",
            json=self.test_user,
            timeout=5
        )

        # 登录获取token
        login_response = requests.post(
            f"{self.base_url}/auth/login",
            json={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            },
            timeout=5
        )

        if login_response.status_code == 200:
            self.token = login_response.json()["data"]["token"]
            logger.info(f"登录成功，token: {self.token[:20]}...")

    def _create_credential(self, alias=None, auth_type="password"):
        """创建登录凭证"""
        if not self.token:
            self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        cred_data = {
            "alias": alias or f"test_cred_{random_str}",
            "host": "127.0.0.1",
            "port": 22,
            "username": "testuser",
            "auth_type": auth_type,
        }

        if auth_type == "password":
            cred_data["password"] = "testpass123"
        else:
            cred_data["private_key_path"] = "/home/testuser/.ssh/id_rsa"

        response = requests.post(
            f"{self.base_url}/login-credentials",
            json=cred_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        if response.status_code == 201:
            cred_id = response.json()["data"]["id"]
            self.created_credentials.append(cred_id)
            return cred_id
        return None

    # ==================== 登录凭证列表测试 ====================

    def test_get_credentials_empty(self, api_client):
        """测试获取空登录凭证列表"""
        logger.info("开始测试：获取空登录凭证列表")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/login-credentials",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert isinstance(data["data"], list), "data应为列表"
        logger.info("获取空登录凭证列表测试通过")

    def test_get_credentials_with_data(self, api_client):
        """测试获取包含数据的登录凭证列表"""
        logger.info("开始测试：获取包含数据的登录凭证列表")

        self._register_and_login()

        # 创建测试凭证
        cred_id = self._create_credential()
        assert cred_id is not None, "创建登录凭证失败"

        response = api_client.get(
            f"{self.base_url}/login-credentials",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert len(data["data"]) >= 1, "凭证列表应至少包含创建的凭证"
        logger.info("获取登录凭证列表测试通过")

    def test_get_credentials_unauthorized(self, api_client):
        """测试未授权访问登录凭证列表"""
        logger.info("开始测试：未授权访问登录凭证列表")

        response = api_client.get(f"{self.base_url}/login-credentials", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问登录凭证列表测试通过")

    # ==================== 单个登录凭证操作测试 ====================

    def test_get_credential_by_id(self, api_client):
        """测试获取单个登录凭证"""
        logger.info("开始测试：获取单个登录凭证")

        self._register_and_login()

        # 创建测试凭证
        cred_id = self._create_credential()
        assert cred_id is not None, "创建登录凭证失败"

        response = api_client.get(
            f"{self.base_url}/login-credentials/{cred_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert data["data"]["id"] == cred_id, "返回的凭证ID应匹配"
        logger.info("获取单个登录凭证测试通过")

    def test_get_credential_not_found(self, api_client):
        """测试获取不存在的登录凭证"""
        logger.info("开始测试：获取不存在的登录凭证")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/login-credentials/999999",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("获取不存在登录凭证测试通过")

    # ==================== 创建登录凭证测试 ====================

    def test_create_credential_password_auth(self, api_client):
        """测试创建密码认证登录凭证"""
        logger.info("开始测试：创建密码认证登录凭证")

        self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        cred_data = {
            "alias": f"password_cred_{random_str}",
            "host": "192.168.1.100",
            "port": 22,
            "username": "admin",
            "auth_type": "password",
            "password": "testpass123"
        }

        response = api_client.post(
            f"{self.base_url}/login-credentials",
            json=cred_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text[:200]}")

        assert response.status_code == 201, f"预期状态码201，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert data["data"]["alias"] == cred_data["alias"], "凭证别名应匹配"
        cred_id = data["data"]["id"]
        self.created_credentials.append(cred_id)
        logger.info("创建密码认证登录凭证测试通过")

    def test_create_credential_key_auth(self, api_client):
        """测试创建密钥认证登录凭证"""
        logger.info("开始测试：创建密钥认证登录凭证")

        self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        cred_data = {
            "alias": f"key_cred_{random_str}",
            "host": "192.168.1.101",
            "port": 22,
            "username": "admin",
            "auth_type": "key",
            "private_key_path": "/home/admin/.ssh/id_rsa",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"
        }

        response = api_client.post(
            f"{self.base_url}/login-credentials",
            json=cred_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 201, f"预期状态码201，实际: {response.status_code}"
        data = response.json()
        cred_id = data["data"]["id"]
        self.created_credentials.append(cred_id)
        logger.info("创建密钥认证登录凭证测试通过")

    def test_create_credential_with_all_fields(self, api_client):
        """测试创建包含所有字段的登录凭证"""
        logger.info("开始测试：创建包含所有字段的登录凭证")

        self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        cred_data = {
            "alias": f"full_cred_{random_str}",
            "host": "192.168.1.102",
            "port": 2222,
            "username": "admin",
            "auth_type": "password",
            "password": "testpass123",
            "root_password": "rootpass123",
            "base_path": "/data",
            "platform_partition": "/dev/sda1",
            "description": "Test credential with all fields"
        }

        response = api_client.post(
            f"{self.base_url}/login-credentials",
            json=cred_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 201, f"预期状态码201，实际: {response.status_code}"
        data = response.json()
        cred_id = data["data"]["id"]
        self.created_credentials.append(cred_id)
        logger.info("创建完整字段登录凭证测试通过")

    def test_create_credential_missing_alias(self, api_client):
        """测试创建登录凭证缺少别名"""
        logger.info("开始测试：创建登录凭证缺少别名")

        self._register_and_login()

        cred_data = {
            "host": "192.168.1.100",
            "port": 22,
            "username": "admin",
            "auth_type": "password",
            "password": "testpass123"
        }

        response = api_client.post(
            f"{self.base_url}/login-credentials",
            json=cred_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        logger.info("创建登录凭证缺少别名测试通过")

    def test_create_credential_missing_host(self, api_client):
        """测试创建登录凭证缺少主机"""
        logger.info("开始测试：创建登录凭证缺少主机")

        self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        cred_data = {
            "alias": f"no_host_cred_{random_str}",
            "port": 22,
            "username": "admin",
            "auth_type": "password",
            "password": "testpass123"
        }

        response = api_client.post(
            f"{self.base_url}/login-credentials",
            json=cred_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        logger.info("创建登录凭证缺少主机测试通过")

    def test_create_credential_missing_username(self, api_client):
        """测试创建登录凭证缺少用户名"""
        logger.info("开始测试：创建登录凭证缺少用户名")

        self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        cred_data = {
            "alias": f"no_user_cred_{random_str}",
            "host": "192.168.1.100",
            "port": 22,
            "auth_type": "password",
            "password": "testpass123"
        }

        response = api_client.post(
            f"{self.base_url}/login-credentials",
            json=cred_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        logger.info("创建登录凭证缺少用户名测试通过")

    def test_create_credential_missing_auth_type(self, api_client):
        """测试创建登录凭证缺少认证类型"""
        logger.info("开始测试：创建登录凭证缺少认证类型")

        self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        cred_data = {
            "alias": f"no_authtype_cred_{random_str}",
            "host": "192.168.1.100",
            "port": 22,
            "username": "admin"
        }

        response = api_client.post(
            f"{self.base_url}/login-credentials",
            json=cred_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        logger.info("创建登录凭证缺少认证类型测试通过")

    # ==================== 更新登录凭证测试 ====================

    def test_update_credential_alias(self, api_client):
        """测试更新登录凭证别名"""
        logger.info("开始测试：更新登录凭证别名")

        self._register_and_login()

        # 创建测试凭证
        cred_id = self._create_credential()
        assert cred_id is not None, "创建登录凭证失败"

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        update_data = {"alias": f"updated_alias_{random_str}"}

        response = api_client.put(
            f"{self.base_url}/login-credentials/{cred_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert data["data"]["alias"] == update_data["alias"], "别名应更新"
        logger.info("更新登录凭证别名测试通过")

    def test_update_credential_host(self, api_client):
        """测试更新登录凭证主机"""
        logger.info("开始测试：更新登录凭证主机")

        self._register_and_login()

        # 创建测试凭证
        cred_id = self._create_credential()
        assert cred_id is not None, "创建登录凭证失败"

        update_data = {"host": "192.168.1.200"}

        response = api_client.put(
            f"{self.base_url}/login-credentials/{cred_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert data["data"]["host"] == update_data["host"], "主机应更新"
        logger.info("更新登录凭证主机测试通过")

    def test_update_credential_password(self, api_client):
        """测试更新登录凭证密码"""
        logger.info("开始测试：更新登录凭证密码")

        self._register_and_login()

        # 创建测试凭证
        cred_id = self._create_credential()
        assert cred_id is not None, "创建登录凭证失败"

        update_data = {"password": "newpassword123"}

        response = api_client.put(
            f"{self.base_url}/login-credentials/{cred_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        logger.info("更新登录凭证密码测试通过")

    def test_update_credential_not_found(self, api_client):
        """测试更新不存在的登录凭证"""
        logger.info("开始测试：更新不存在的登录凭证")

        self._register_and_login()

        update_data = {"alias": "updated_alias"}

        response = api_client.put(
            f"{self.base_url}/login-credentials/999999",
            json=update_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("更新不存在登录凭证测试通过")

    # ==================== 删除登录凭证测试 ====================

    def test_delete_credential_success(self, api_client):
        """测试成功删除登录凭证"""
        logger.info("开始测试：成功删除登录凭证")

        self._register_and_login()

        # 创建测试凭证
        cred_id = self._create_credential()
        assert cred_id is not None, "创建登录凭证失败"

        response = api_client.delete(
            f"{self.base_url}/login-credentials/{cred_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"

        # 验证凭证已被删除
        get_response = api_client.get(
            f"{self.base_url}/login-credentials/{cred_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )
        assert get_response.status_code == 404, "凭证应已被删除"
        self.created_credentials.remove(cred_id)
        logger.info("删除登录凭证测试通过")

    def test_delete_credential_not_found(self, api_client):
        """测试删除不存在的登录凭证"""
        logger.info("开始测试：删除不存在的登录凭证")

        self._register_and_login()

        response = api_client.delete(
            f"{self.base_url}/login-credentials/999999",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("删除不存在登录凭证测试通过")

    # ==================== 测试登录凭证连接 ====================

    def test_test_connection_not_found(self, api_client):
        """测试连接不存在的凭证"""
        logger.info("开始测试：连接不存在的凭证")

        self._register_and_login()

        response = api_client.post(
            f"{self.base_url}/login-credentials/999999/test",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=10
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("连接不存在凭证测试通过")

    # ==================== 边界条件测试 ====================

    def test_credential_invalid_id_type(self, api_client):
        """测试无效的凭证ID类型"""
        logger.info("开始测试：无效的凭证ID类型")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/login-credentials/invalid",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [404, 400], f"预期状态码404或400，实际: {response.status_code}"
        logger.info("无效凭证ID类型测试通过")

    def test_credential_negative_id(self, api_client):
        """测试负数凭证ID"""
        logger.info("开始测试：负数凭证ID")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/login-credentials/-1",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("负数凭证ID测试通过")

    # ==================== 参数化测试 ====================

    @pytest.mark.parametrize("port", [22, 2222, 3306, 8080, 27017])
    def test_create_credential_with_different_ports(self, api_client, port):
        """测试使用不同端口创建登录凭证"""
        logger.info(f"开始测试：使用端口 {port} 创建登录凭证")

        self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        cred_data = {
            "alias": f"port_cred_{port}_{random_str}",
            "host": "192.168.1.100",
            "port": port,
            "username": "admin",
            "auth_type": "password",
            "password": "testpass123"
        }

        response = api_client.post(
            f"{self.base_url}/login-credentials",
            json=cred_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 201, f"预期状态码201，实际: {response.status_code}"
        data = response.json()
        cred_id = data["data"]["id"]
        self.created_credentials.append(cred_id)
        logger.info(f"端口 {port} 测试通过")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
