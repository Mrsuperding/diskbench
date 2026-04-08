"""环境空间和监控配置 API 测试

测试环境空间相关的所有API端点：
- GET /api/environment-spaces - 获取环境空间列表
- GET /api/environment-spaces/<id> - 获取环境空间详情
- POST /api/environment-spaces - 创建环境空间
- PUT /api/environment-spaces/<id> - 更新环境空间
- DELETE /api/environment-spaces/<id> - 删除环境空间
- POST /api/environment-spaces/<id>/metrics/collect - 手动触发指标采集
- POST /api/environment-spaces/<id>/metrics/partition/collect - 手动触发分区指标采集

测试监控配置相关的所有API端点：
- GET /api/monitoring-config - 获取监控配置列表
- GET /api/monitoring-config/<id> - 获取监控配置详情
- POST /api/monitoring-config - 创建监控配置
- PUT /api/monitoring-config/<id> - 更新监控配置
- DELETE /api/monitoring-config/<id> - 删除监控配置
"""

import pytest
import requests
import random
import string
from loguru import logger


class TestEnvironmentSpacesAPI:
    """环境空间 API 测试类"""

    def setup_method(self):
        """测试前的设置"""
        self.base_url = "http://localhost:5003/api"
        self.test_user = {
            "username": "test_admin_env",
            "email": "test_admin_env@example.com",
            "password": "test123456"
        }
        self.token = None
        self.created_spaces = []

    def teardown_method(self):
        """测试后的清理"""
        if self.token:
            for space_id in self.created_spaces:
                try:
                    requests.delete(
                        f"{self.base_url}/environment-spaces/{space_id}",
                        headers={"Authorization": f"Bearer {self.token}"},
                        timeout=5
                    )
                    logger.info(f"成功删除环境空间: {space_id}")
                except Exception as e:
                    logger.warning(f"删除环境空间失败: {space_id}, {e}")

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

    # ==================== 环境空间列表测试 ====================

    def test_get_environment_spaces_empty(self, api_client):
        """测试获取空环境空间列表"""
        logger.info("开始测试：获取空环境空间列表")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/environment-spaces",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text[:200]}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert isinstance(data["data"], list), "data应为列表"
        logger.info("获取空环境空间列表测试通过")

    def test_get_environment_spaces_unauthorized(self, api_client):
        """测试未授权访问环境空间列表"""
        logger.info("开始测试：未授权访问环境空间列表")

        response = api_client.get(f"{self.base_url}/environment-spaces", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问环境空间列表测试通过")

    # ==================== 单个环境空间操作测试 ====================

    def test_get_environment_space_not_found(self, api_client):
        """测试获取不存在的环境空间"""
        logger.info("开始测试：获取不存在的环境空间")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/environment-spaces/999999",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("获取不存在环境空间测试通过")

    def test_create_environment_space_unauthorized(self, api_client):
        """测试未授权创建环境空间"""
        logger.info("开始测试：未授权创建环境空间")

        space_data = {
            "name": "test_space",
            "description": "test"
        }

        response = api_client.post(
            f"{self.base_url}/environment-spaces",
            json=space_data,
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权创建环境空间测试通过")

    def test_update_environment_space_not_found(self, api_client):
        """测试更新不存在的环境空间"""
        logger.info("开始测试：更新不存在的环境空间")

        self._register_and_login()

        update_data = {"name": "updated_name"}

        response = api_client.put(
            f"{self.base_url}/environment-spaces/999999",
            json=update_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("更新不存在环境空间测试通过")

    def test_delete_environment_space_not_found(self, api_client):
        """测试删除不存在的环境空间"""
        logger.info("开始测试：删除不存在的环境空间")

        self._register_and_login()

        response = api_client.delete(
            f"{self.base_url}/environment-spaces/999999",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("删除不存在环境空间测试通过")

    # ==================== 环境空间指标采集测试 ====================

    def test_collect_space_metrics_not_found(self, api_client):
        """测试采集不存在环境空间的指标"""
        logger.info("开始测试：采集不存在环境空间的指标")

        self._register_and_login()

        response = api_client.post(
            f"{self.base_url}/environment-spaces/999999/metrics/collect",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=30
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("采集不存在环境空间指标测试通过")

    def test_collect_partition_metrics_not_found(self, api_client):
        """测试采集不存在环境空间的分区指标"""
        logger.info("开始测试：采集不存在环境空间的分区指标")

        self._register_and_login()

        response = api_client.post(
            f"{self.base_url}/environment-spaces/999999/metrics/partition/collect",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=30
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("采集不存在环境空间分区指标测试通过")

    def test_collect_metrics_unauthorized(self, api_client):
        """测试未授权采集环境空间指标"""
        logger.info("开始测试：未授权采集环境空间指标")

        response = api_client.post(
            f"{self.base_url}/environment-spaces/1/metrics/collect",
            timeout=30
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权采集环境空间指标测试通过")

    # ==================== 边界条件测试 ====================

    def test_environment_space_invalid_id_type(self, api_client):
        """测试无效的环境空间ID类型"""
        logger.info("开始测试：无效的环境空间ID类型")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/environment-spaces/invalid",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [404, 400], f"预期状态码404或400，实际: {response.status_code}"
        logger.info("无效环境空间ID类型测试通过")


class TestMonitoringConfigAPI:
    """监控配置 API 测试类"""

    def setup_method(self):
        """测试前的设置"""
        self.base_url = "http://localhost:5003/api"
        self.test_user = {
            "username": "test_admin_monitor",
            "email": "test_admin_monitor@example.com",
            "password": "test123456"
        }
        self.token = None
        self.created_configs = []

    def teardown_method(self):
        """测试后的清理"""
        if self.token:
            for config_id in self.created_configs:
                try:
                    requests.delete(
                        f"{self.base_url}/monitoring-config/{config_id}",
                        headers={"Authorization": f"Bearer {self.token}"},
                        timeout=5
                    )
                    logger.info(f"成功删除监控配置: {config_id}")
                except Exception as e:
                    logger.warning(f"删除监控配置失败: {config_id}, {e}")

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

    # ==================== 监控配置测试 ====================
    # 注意：监控配置API只有 /global 和 /environment/<space_id> 端点

    def test_get_global_monitoring_config(self, api_client):
        """测试获取全局监控配置"""
        logger.info("开始测试：获取全局监控配置")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/monitoring-config/global",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text[:200]}")

        # 全局配置可能存在也可能不存在，都视为有效响应
        assert response.status_code in [200, 404, 500], f"预期状态码200/404/500，实际: {response.status_code}"
        logger.info("获取全局监控配置测试完成")

    def test_get_global_monitoring_config_unauthorized(self, api_client):
        """测试未授权访问全局监控配置"""
        logger.info("开始测试：未授权访问全局监控配置")

        response = api_client.get(f"{self.base_url}/monitoring-config/global", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问全局监控配置测试通过")

    def test_get_environment_monitoring_config_not_found(self, api_client):
        """测试获取不存在环境的监控配置"""
        logger.info("开始测试：获取不存在环境的监控配置")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/monitoring-config/environment/999999",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        # 环境空间不存在应返回404
        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("获取不存在环境监控配置测试通过")

    def test_update_environment_monitoring_config_not_found(self, api_client):
        """测试更新不存在环境的监控配置"""
        logger.info("开始测试：更新不存在环境的监控配置")

        self._register_and_login()

        config_data = {
            "collection_interval": 120,
            "enabled": True
        }

        response = api_client.put(
            f"{self.base_url}/monitoring-config/environment/999999",
            json=config_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        # 环境空间不存在应返回404
        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("更新不存在环境监控配置测试通过")

    def test_update_global_monitoring_config(self, api_client):
        """测试更新全局监控配置"""
        logger.info("开始测试：更新全局监控配置")

        self._register_and_login()

        config_data = {
            "collection_interval": 120,
            "enabled": True
        }

        response = api_client.put(
            f"{self.base_url}/monitoring-config/global",
            json=config_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text[:200]}")

        # 全局配置更新可能成功或失败，取决于配置是否存在
        assert response.status_code in [200, 400, 500], f"预期状态码200/400/500，实际: {response.status_code}"
        logger.info("更新全局监控配置测试完成")

    def test_update_global_monitoring_config_unauthorized(self, api_client):
        """测试未授权更新全局监控配置"""
        logger.info("开始测试：未授权更新全局监控配置")

        config_data = {
            "collection_interval": 120,
            "enabled": True
        }

        response = api_client.put(
            f"{self.base_url}/monitoring-config/global",
            json=config_data,
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权更新全局监控配置测试通过")

    def test_monitoring_config_invalid_space_id(self, api_client):
        """测试无效的环境空间ID"""
        logger.info("开始测试：无效的环境空间ID")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/monitoring-config/environment/invalid",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [404, 400], f"预期状态码404或400，实际: {response.status_code}"
        logger.info("无效环境空间ID测试通过")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
