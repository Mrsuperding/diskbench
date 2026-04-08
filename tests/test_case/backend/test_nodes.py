"""节点管理 API 测试

测试节点相关的所有API端点：
- GET /api/nodes - 获取节点列表
- GET /api/nodes/<id> - 获取单个节点
- POST /api/nodes - 创建节点
- PUT /api/nodes/<id> - 更新节点
- DELETE /api/nodes/<id> - 删除节点
- GET /api/nodes/<id>/status - 检查节点状态
- GET /api/nodes/<id>/metrics - 获取节点监控数据
- GET /api/nodes/<id>/metrics/history - 获取历史监控数据
- POST /api/nodes/<id>/metrics/collect - 手动采集监控数据
- POST /api/nodes/metrics/collect-all - 批量采集所有节点监控数据
"""

import pytest
import requests
import random
import string
import time
from loguru import logger


class TestNodesAPI:
    """节点管理 API 测试类"""

    def setup_method(self):
        """测试前的设置"""
        self.base_url = "http://localhost:5003/api"
        self.test_user = {
            "username": "test_admin_nodes",
            "email": "test_admin_nodes@example.com",
            "password": "test123456"
        }
        self.token = None
        self.created_nodes = []
        self.created_credentials = []

    def teardown_method(self):
        """测试后的清理"""
        if self.token:
            # 清理创建的节点
            for node_id in self.created_nodes:
                try:
                    requests.delete(
                        f"{self.base_url}/nodes/{node_id}",
                        headers={"Authorization": f"Bearer {self.token}"},
                        timeout=5
                    )
                    logger.info(f"成功删除节点: {node_id}")
                except Exception as e:
                    logger.warning(f"删除节点失败: {node_id}, {e}")

            # 清理创建的凭证
            for cred_id in self.created_credentials:
                try:
                    requests.delete(
                        f"{self.base_url}/login-credentials/{cred_id}",
                        headers={"Authorization": f"Bearer {self.token}"},
                        timeout=5
                    )
                    logger.info(f"成功删除凭证: {cred_id}")
                except Exception as e:
                    logger.warning(f"删除凭证失败: {cred_id}, {e}")

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

    def _create_login_credential(self):
        """创建登录凭证"""
        if not self.token:
            self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        credential_data = {
            "alias": f"test_cred_{random_str}",
            "host": "127.0.0.1",
            "port": 22,
            "username": "testuser",
            "password": "testpass"
        }

        response = requests.post(
            f"{self.base_url}/login-credentials",
            json=credential_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        if response.status_code == 200:
            cred_id = response.json()["data"]["id"]
            self.created_credentials.append(cred_id)
            return cred_id
        return None

    def _create_node(self, name=None, ip_address=None):
        """创建测试节点"""
        if not self.token:
            self._register_and_login()

        cred_id = self._create_login_credential()
        if not cred_id:
            return None

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        node_data = {
            "name": name or f"test_node_{random_str}",
            "ip_address": ip_address or f"192.168.1.{random.randint(1, 254)}",
            "login_credential_id": cred_id
        }

        response = requests.post(
            f"{self.base_url}/nodes",
            json=node_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        if response.status_code == 200:
            node_id = response.json()["data"]["id"]
            self.created_nodes.append(node_id)
            return node_id
        return None

    # ==================== 节点列表相关测试 ====================

    def test_get_nodes_empty(self, api_client):
        """测试获取空节点列表"""
        logger.info("开始测试：获取空节点列表")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/nodes",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert isinstance(data["data"], list), "data应为列表"
        logger.info("获取空节点列表测试通过")

    def test_get_nodes_with_data(self, api_client):
        """测试获取包含数据的节点列表"""
        logger.info("开始测试：获取包含数据的节点列表")

        self._register_and_login()

        # 创建测试节点
        node_id = self._create_node()
        assert node_id is not None, "创建测试节点失败"

        response = api_client.get(
            f"{self.base_url}/nodes",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert len(data["data"]) >= 1, "节点列表应至少包含创建的节点"
        logger.info("获取节点列表测试通过")

    def test_get_nodes_unauthorized(self, api_client):
        """测试未授权访问节点列表"""
        logger.info("开始测试：未授权访问节点列表")

        response = api_client.get(f"{self.base_url}/nodes", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问测试通过")

    # ==================== 单个节点操作测试 ====================

    def test_get_node_by_id(self, api_client):
        """测试获取单个节点信息"""
        logger.info("开始测试：获取单个节点")

        self._register_and_login()

        # 创建测试节点
        node_id = self._create_node()
        assert node_id is not None, "创建测试节点失败"

        response = api_client.get(
            f"{self.base_url}/nodes/{node_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert data["data"]["id"] == node_id, "返回的节点ID应匹配"
        logger.info("获取单个节点测试通过")

    def test_get_node_not_found(self, api_client):
        """测试获取不存在的节点"""
        logger.info("开始测试：获取不存在的节点")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/nodes/999999",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("获取不存在节点测试通过")

    # ==================== 创建节点测试 ====================

    def test_create_node_success(self, api_client):
        """测试成功创建节点"""
        logger.info("开始测试：成功创建节点")

        self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        cred_id = self._create_login_credential()
        assert cred_id is not None, "创建登录凭证失败"

        node_data = {
            "name": f"new_node_{random_str}",
            "ip_address": f"192.168.1.{random.randint(1, 254)}",
            "login_credential_id": cred_id
        }

        response = api_client.post(
            f"{self.base_url}/nodes",
            json=node_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text}")

        assert response.status_code == 201, f"预期状态码201，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert data["data"]["name"] == node_data["name"], "节点名称应匹配"
        node_id = data["data"]["id"]
        self.created_nodes.append(node_id)
        logger.info("创建节点测试通过")

    def test_create_node_missing_name(self, api_client):
        """测试创建节点缺少名称"""
        logger.info("开始测试：创建节点缺少名称")

        self._register_and_login()

        cred_id = self._create_login_credential()
        assert cred_id is not None, "创建登录凭证失败"

        node_data = {
            "ip_address": "192.168.1.100",
            "login_credential_id": cred_id
        }

        response = api_client.post(
            f"{self.base_url}/nodes",
            json=node_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        logger.info("创建节点缺少名称测试通过")

    def test_create_node_missing_ip(self, api_client):
        """测试创建节点缺少IP地址"""
        logger.info("开始测试：创建节点缺少IP地址")

        self._register_and_login()

        cred_id = self._create_login_credential()
        assert cred_id is not None, "创建登录凭证失败"

        node_data = {
            "name": "test_node_no_ip",
            "login_credential_id": cred_id
        }

        response = api_client.post(
            f"{self.base_url}/nodes",
            json=node_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        logger.info("创建节点缺少IP测试通过")

    def test_create_node_missing_credential(self, api_client):
        """测试创建节点缺少登录凭证"""
        logger.info("开始测试：创建节点缺少登录凭证")

        self._register_and_login()

        node_data = {
            "name": "test_node_no_cred",
            "ip_address": "192.168.1.100"
        }

        response = api_client.post(
            f"{self.base_url}/nodes",
            json=node_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        logger.info("创建节点缺少凭证测试通过")

    def test_create_node_duplicate_name(self, api_client):
        """测试创建重复名称的节点"""
        logger.info("开始测试：创建重复名称的节点")

        self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        cred_id = self._create_login_credential()
        node_name = f"duplicate_node_{random_str}"

        # 创建第一个节点
        node_data_1 = {
            "name": node_name,
            "ip_address": f"192.168.1.{random.randint(1, 254)}",
            "login_credential_id": cred_id
        }

        response1 = api_client.post(
            f"{self.base_url}/nodes",
            json=node_data_1,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )
        assert response1.status_code == 201, "创建第一个节点失败"

        # 尝试创建同名节点
        node_data_2 = {
            "name": node_name,
            "ip_address": f"192.168.1.{random.randint(1, 254)}",
            "login_credential_id": cred_id
        }

        response2 = api_client.post(
            f"{self.base_url}/nodes",
            json=node_data_2,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response2.status_code}")

        assert response2.status_code == 400, f"预期状态码400，实际: {response2.status_code}"
        logger.info("创建重复名称节点测试通过")

    # ==================== 更新节点测试 ====================

    def test_update_node_success(self, api_client):
        """测试成功更新节点"""
        logger.info("开始测试：成功更新节点")

        self._register_and_login()

        # 创建测试节点
        node_id = self._create_node()
        assert node_id is not None, "创建测试节点失败"

        # 更新节点
        update_data = {
            "name": f"updated_node_{''.join(random.choices(string.ascii_lowercase, k=8))}",
            "status": "offline"
        }

        response = api_client.put(
            f"{self.base_url}/nodes/{node_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert data["data"]["name"] == update_data["name"], "节点名称应更新"
        logger.info("更新节点测试通过")

    def test_update_node_not_found(self, api_client):
        """测试更新不存在的节点"""
        logger.info("开始测试：更新不存在的节点")

        self._register_and_login()

        update_data = {"name": "updated_name"}

        response = api_client.put(
            f"{self.base_url}/nodes/999999",
            json=update_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("更新不存在节点测试通过")

    # ==================== 删除节点测试 ====================

    def test_delete_node_success(self, api_client):
        """测试成功删除节点"""
        logger.info("开始测试：成功删除节点")

        self._register_and_login()

        # 创建测试节点
        node_id = self._create_node()
        assert node_id is not None, "创建测试节点失败"

        response = api_client.delete(
            f"{self.base_url}/nodes/{node_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"

        # 验证节点已被删除
        get_response = api_client.get(
            f"{self.base_url}/nodes/{node_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )
        assert get_response.status_code == 404, "节点应已被删除"
        self.created_nodes.remove(node_id)
        logger.info("删除节点测试通过")

    def test_delete_node_not_found(self, api_client):
        """测试删除不存在的节点"""
        logger.info("开始测试：删除不存在的节点")

        self._register_and_login()

        response = api_client.delete(
            f"{self.base_url}/nodes/999999",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("删除不存在节点测试通过")

    # ==================== 节点状态检查测试 ====================

    def test_check_node_status(self, api_client):
        """测试检查节点状态"""
        logger.info("开始测试：检查节点状态")

        self._register_and_login()

        # 创建测试节点
        node_id = self._create_node()
        assert node_id is not None, "创建测试节点失败"

        response = api_client.get(
            f"{self.base_url}/nodes/{node_id}/status",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert "status" in data["data"], "响应应包含status字段"
        logger.info("检查节点状态测试通过")

    # ==================== 节点监控数据测试 ====================

    def test_get_node_metrics(self, api_client):
        """测试获取节点监控数据"""
        logger.info("开始测试：获取节点监控数据")

        self._register_and_login()

        # 创建测试节点
        node_id = self._create_node()
        assert node_id is not None, "创建测试节点失败"

        response = api_client.get(
            f"{self.base_url}/nodes/{node_id}/metrics",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        logger.info("获取节点监控数据测试通过")

    def test_get_node_metrics_history(self, api_client):
        """测试获取节点历史监控数据"""
        logger.info("开始测试：获取节点历史监控数据")

        self._register_and_login()

        # 创建测试节点
        node_id = self._create_node()
        assert node_id is not None, "创建测试节点失败"

        response = api_client.get(
            f"{self.base_url}/nodes/{node_id}/metrics/history?hours=1",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        logger.info("获取节点历史监控数据测试通过")

    def test_get_node_metrics_history_with_metric_name(self, api_client):
        """测试按指标名称获取历史监控数据"""
        logger.info("开始测试：按指标名称获取历史监控数据")

        self._register_and_login()

        # 创建测试节点
        node_id = self._create_node()
        assert node_id is not None, "创建测试节点失败"

        response = api_client.get(
            f"{self.base_url}/nodes/{node_id}/metrics/history?hours=1&metric_name=cpu_usage",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        logger.info("按指标名称获取历史监控数据测试通过")

    # ==================== 节点监控数据采集测试 ====================

    def test_collect_node_metrics(self, api_client):
        """测试手动采集节点监控数据"""
        logger.info("开始测试：手动采集节点监控数据")

        self._register_and_login()

        # 创建测试节点
        node_id = self._create_node()
        assert node_id is not None, "创建测试节点失败"

        response = api_client.post(
            f"{self.base_url}/nodes/{node_id}/metrics/collect",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=30
        )

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text[:200]}")

        # 可能是200成功或500（如果节点无法连接）
        assert response.status_code in [200, 500], f"预期状态码200或500，实际: {response.status_code}"
        logger.info("手动采集节点监控数据测试通过")

    def test_collect_all_nodes_metrics(self, api_client):
        """测试批量采集所有节点监控数据"""
        logger.info("开始测试：批量采集所有节点监控数据")

        self._register_and_login()

        # 创建测试节点
        node_id = self._create_node()
        assert node_id is not None, "创建测试节点失败"

        response = api_client.post(
            f"{self.base_url}/nodes/metrics/collect-all",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=60
        )

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text[:200]}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert "total" in data["data"], "响应应包含total字段"
        assert "success" in data["data"], "响应应包含success字段"
        assert "failed" in data["data"], "响应应包含failed字段"
        logger.info("批量采集所有节点监控数据测试通过")

    # ==================== 边界条件测试 ====================

    def test_node_invalid_id_type(self, api_client):
        """测试无效的节点ID类型"""
        logger.info("开始测试：无效的节点ID类型")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/nodes/invalid",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        # Flask会对无效的路由参数返回404或400
        assert response.status_code in [404, 400], f"预期状态码404或400，实际: {response.status_code}"
        logger.info("无效节点ID类型测试通过")

    def test_node_negative_id(self, api_client):
        """测试负数节点ID"""
        logger.info("开始测试：负数节点ID")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/nodes/-1",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("负数节点ID测试通过")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
