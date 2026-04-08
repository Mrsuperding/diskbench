"""IO测试用例 API 测试

测试IO测试用例相关的所有API端点：
- GET /api/io-cases - 获取IO测试用例列表
- GET /api/io-cases/<id> - 获取单个IO测试用例
- POST /api/io-cases - 创建IO测试用例
- PUT /api/io-cases/<id> - 更新IO测试用例
- DELETE /api/io-cases/<id> - 删除IO测试用例
- GET /api/io-cases/templates - 获取测试用例模板列表
"""

import pytest
import requests
import random
import string
import time
from loguru import logger


class TestIOCasesAPI:
    """IO测试用例 API 测试类"""

    def setup_method(self):
        """测试前的设置"""
        self.base_url = "http://localhost:5003/api"
        self.test_user = {
            "username": "test_admin_iocase",
            "email": "test_admin_iocase@example.com",
            "password": "test123456"
        }
        self.token = None
        self.created_cases = []

    def teardown_method(self):
        """测试后的清理"""
        if self.token:
            for case_id in self.created_cases:
                try:
                    requests.delete(
                        f"{self.base_url}/io-cases/{case_id}",
                        headers={"Authorization": f"Bearer {self.token}"},
                        timeout=5
                    )
                    logger.info(f"成功删除IO测试用例: {case_id}")
                except Exception as e:
                    logger.warning(f"删除IO测试用例失败: {case_id}, {e}")

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

    def _create_io_case(self, name=None, parameters=None):
        """创建IO测试用例"""
        if not self.token:
            self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        case_data = {
            "name": name or f"test_io_case_{random_str}",
            "description": f"Test IO case description {random_str}",
            "parameters": parameters or {
                "rw": "randread",
                "bs": "4k",
                "ioengine": "libaio",
                "size": "1G",
                "runtime": 60
            }
        }

        response = requests.post(
            f"{self.base_url}/io-cases",
            json=case_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        if response.status_code == 201:
            case_id = response.json()["data"]["id"]
            self.created_cases.append(case_id)
            return case_id
        return None

    # ==================== IO测试用例列表测试 ====================

    def test_get_io_cases_empty(self, api_client):
        """测试获取空IO测试用例列表"""
        logger.info("开始测试：获取空IO测试用例列表")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/io-cases",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text[:200]}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert isinstance(data["data"], list), "data应为列表"
        logger.info("获取空IO测试用例列表测试通过")

    def test_get_io_cases_with_data(self, api_client):
        """测试获取包含数据的IO测试用例列表"""
        logger.info("开始测试：获取包含数据的IO测试用例列表")

        self._register_and_login()

        # 创建测试用例
        case_id = self._create_io_case()
        assert case_id is not None, "创建测试用例失败"

        response = api_client.get(
            f"{self.base_url}/io-cases",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert len(data["data"]) >= 1, "IO测试用例列表应至少包含创建的用例"
        logger.info("获取IO测试用例列表测试通过")

    def test_get_io_cases_unauthorized(self, api_client):
        """测试未授权访问IO测试用例列表"""
        logger.info("开始测试：未授权访问IO测试用例列表")

        response = api_client.get(f"{self.base_url}/io-cases", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问IO测试用例列表测试通过")

    # ==================== 单个IO测试用例操作测试 ====================

    def test_get_io_case_by_id(self, api_client):
        """测试获取单个IO测试用例"""
        logger.info("开始测试：获取单个IO测试用例")

        self._register_and_login()

        # 创建测试用例
        case_id = self._create_io_case()
        assert case_id is not None, "创建测试用例失败"

        response = api_client.get(
            f"{self.base_url}/io-cases/{case_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert data["data"]["id"] == case_id, "返回的用例ID应匹配"
        logger.info("获取单个IO测试用例测试通过")

    def test_get_io_case_not_found(self, api_client):
        """测试获取不存在的IO测试用例"""
        logger.info("开始测试：获取不存在的IO测试用例")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/io-cases/999999",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("获取不存在IO测试用例测试通过")

    # ==================== 创建IO测试用例测试 ====================

    def test_create_io_case_success(self, api_client):
        """测试成功创建IO测试用例"""
        logger.info("开始测试：成功创建IO测试用例")

        self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        case_data = {
            "name": f"new_io_case_{random_str}",
            "description": f"Test IO case description {random_str}",
            "parameters": {
                "rw": "randread",
                "bs": "4k",
                "ioengine": "libaio",
                "size": "1G",
                "runtime": 60
            }
        }

        response = api_client.post(
            f"{self.base_url}/io-cases",
            json=case_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text[:200]}")

        assert response.status_code == 201, f"预期状态码201，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert data["data"]["name"] == case_data["name"], "用例名称应匹配"
        case_id = data["data"]["id"]
        self.created_cases.append(case_id)
        logger.info("创建IO测试用例测试通过")

    def test_create_io_case_with_minimal_params(self, api_client):
        """测试使用最小参数创建IO测试用例"""
        logger.info("开始测试：使用最小参数创建IO测试用例")

        self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        case_data = {
            "name": f"minimal_io_case_{random_str}",
            "parameters": {"rw": "read"}
        }

        response = api_client.post(
            f"{self.base_url}/io-cases",
            json=case_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 201, f"预期状态码201，实际: {response.status_code}"
        data = response.json()
        case_id = data["data"]["id"]
        self.created_cases.append(case_id)
        logger.info("使用最小参数创建IO测试用例测试通过")

    def test_create_io_case_missing_name(self, api_client):
        """测试创建IO测试用例缺少名称"""
        logger.info("开始测试：创建IO测试用例缺少名称")

        self._register_and_login()

        case_data = {
            "description": "Test description",
            "parameters": {"rw": "read"}
        }

        response = api_client.post(
            f"{self.base_url}/io-cases",
            json=case_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        logger.info("创建IO测试用例缺少名称测试通过")

    def test_create_io_case_missing_parameters(self, api_client):
        """测试创建IO测试用例缺少参数"""
        logger.info("开始测试：创建IO测试用例缺少参数")

        self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        case_data = {
            "name": f"no_params_case_{random_str}"
        }

        response = api_client.post(
            f"{self.base_url}/io-cases",
            json=case_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        logger.info("创建IO测试用例缺少参数测试通过")

    def test_create_io_case_empty_name(self, api_client):
        """测试创建IO测试用例使用空名称"""
        logger.info("开始测试：创建IO测试用例使用空名称")

        self._register_and_login()

        case_data = {
            "name": "",
            "parameters": {"rw": "read"}
        }

        response = api_client.post(
            f"{self.base_url}/io-cases",
            json=case_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        logger.info("创建IO测试用例空名称测试通过")

    # ==================== 更新IO测试用例测试 ====================

    def test_update_io_case_success(self, api_client):
        """测试成功更新IO测试用例"""
        logger.info("开始测试：成功更新IO测试用例")

        self._register_and_login()

        # 创建测试用例
        case_id = self._create_io_case()
        assert case_id is not None, "创建测试用例失败"

        # 更新用例
        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        update_data = {
            "name": f"updated_io_case_{random_str}",
            "description": f"Updated description {random_str}",
            "parameters": {"rw": "write", "bs": "8k"}
        }

        response = api_client.put(
            f"{self.base_url}/io-cases/{case_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert data["data"]["name"] == update_data["name"], "用例名称应更新"
        logger.info("更新IO测试用例测试通过")

    def test_update_io_case_partial(self, api_client):
        """测试部分更新IO测试用例"""
        logger.info("开始测试：部分更新IO测试用例")

        self._register_and_login()

        # 创建测试用例
        case_id = self._create_io_case()
        assert case_id is not None, "创建测试用例失败"

        original_name = requests.get(
            f"{self.base_url}/io-cases/{case_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        ).json()["data"]["name"]

        # 只更新description
        update_data = {"description": "Only description updated"}

        response = api_client.put(
            f"{self.base_url}/io-cases/{case_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert data["data"]["name"] == original_name, "名称应保持不变"
        assert data["data"]["description"] == update_data["description"], "描述应更新"
        logger.info("部分更新IO测试用例测试通过")

    def test_update_io_case_not_found(self, api_client):
        """测试更新不存在的IO测试用例"""
        logger.info("开始测试：更新不存在的IO测试用例")

        self._register_and_login()

        update_data = {"name": "updated_name"}

        response = api_client.put(
            f"{self.base_url}/io-cases/999999",
            json=update_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("更新不存在IO测试用例测试通过")

    # ==================== 删除IO测试用例测试 ====================

    def test_delete_io_case_success(self, api_client):
        """测试成功删除IO测试用例"""
        logger.info("开始测试：成功删除IO测试用例")

        self._register_and_login()

        # 创建测试用例
        case_id = self._create_io_case()
        assert case_id is not None, "创建测试用例失败"

        response = api_client.delete(
            f"{self.base_url}/io-cases/{case_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"

        # 验证用例已被删除
        get_response = api_client.get(
            f"{self.base_url}/io-cases/{case_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )
        assert get_response.status_code == 404, "用例应已被删除"
        self.created_cases.remove(case_id)
        logger.info("删除IO测试用例测试通过")

    def test_delete_io_case_not_found(self, api_client):
        """测试删除不存在的IO测试用例"""
        logger.info("开始测试：删除不存在的IO测试用例")

        self._register_and_login()

        response = api_client.delete(
            f"{self.base_url}/io-cases/999999",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("删除不存在IO测试用例测试通过")

    # ==================== 测试用例模板测试 ====================

    def test_get_templates(self, api_client):
        """测试获取测试用例模板列表"""
        logger.info("开始测试：获取测试用例模板列表")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/io-cases/templates",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert isinstance(data["data"], list), "data应为列表"
        logger.info("获取测试用例模板列表测试通过")

    def test_get_templates_unauthorized(self, api_client):
        """测试未授权访问模板列表"""
        logger.info("开始测试：未授权访问模板列表")

        response = api_client.get(f"{self.base_url}/io-cases/templates", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问模板列表测试通过")

    # ==================== 边界条件测试 ====================

    def test_io_case_invalid_id_type(self, api_client):
        """测试无效的用例ID类型"""
        logger.info("开始测试：无效的用例ID类型")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/io-cases/invalid",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [404, 400], f"预期状态码404或400，实际: {response.status_code}"
        logger.info("无效用例ID类型测试通过")

    def test_io_case_negative_id(self, api_client):
        """测试负数用例ID"""
        logger.info("开始测试：负数用例ID")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/io-cases/-1",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("负数用例ID测试通过")

    # ==================== 参数化测试 ====================

    @pytest.mark.parametrize("rw_mode", ["read", "write", "randread", "randwrite", "rw", "randrw"])
    def test_create_io_case_with_different_rw_modes(self, api_client, rw_mode):
        """测试使用不同读写模式创建IO测试用例"""
        logger.info(f"开始测试：使用读写模式 {rw_mode} 创建IO测试用例")

        self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        case_data = {
            "name": f"io_case_{rw_mode}_{random_str}",
            "parameters": {"rw": rw_mode, "bs": "4k"}
        }

        response = api_client.post(
            f"{self.base_url}/io-cases",
            json=case_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 201, f"预期状态码201，实际: {response.status_code}"
        data = response.json()
        case_id = data["data"]["id"]
        self.created_cases.append(case_id)
        logger.info(f"读写模式 {rw_mode} 测试通过")

    @pytest.mark.parametrize("bs_size", ["4k", "8k", "16k", "32k", "64k", "128k", "1M"])
    def test_create_io_case_with_different_block_sizes(self, api_client, bs_size):
        """测试使用不同块大小创建IO测试用例"""
        logger.info(f"开始测试：使用块大小 {bs_size} 创建IO测试用例")

        self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        case_data = {
            "name": f"io_case_bs_{bs_size}_{random_str}",
            "parameters": {"rw": "randread", "bs": bs_size}
        }

        response = api_client.post(
            f"{self.base_url}/io-cases",
            json=case_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 201, f"预期状态码201，实际: {response.status_code}"
        data = response.json()
        case_id = data["data"]["id"]
        self.created_cases.append(case_id)
        logger.info(f"块大小 {bs_size} 测试通过")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
