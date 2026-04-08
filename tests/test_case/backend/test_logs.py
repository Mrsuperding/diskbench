"""日志 API 测试

测试日志相关的所有API端点：
- GET /api/logs/<log_id> - 获取日志详情
- GET /api/logs/<log_id>/iostat-metrics - 获取IOSTAT指标数据
- GET /api/logs/<log_id>/jitter - 获取性能抖动数据
- GET /api/logs/<log_id>/fio-results - 获取FIO日志解析结果
- GET /api/logs/<log_id>/iostat-jitter - 获取IOSTAT指标抖动计算结果
- GET /api/logs/<log_id>/download - 下载日志文件
- GET /api/logs/task/<task_id> - 获取测试任务的所有日志
- GET /api/logs/task/<task_id>/realtime-metrics - 获取实时FIO日志指标数据
"""

import pytest
import requests
import random
import string
from loguru import logger


class TestLogsAPI:
    """日志 API 测试类"""

    def setup_method(self):
        """测试前的设置"""
        self.base_url = "http://localhost:5003/api"
        self.test_user = {
            "username": "test_admin_logs",
            "email": "test_admin_logs@example.com",
            "password": "test123456"
        }
        self.token = None

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

    # ==================== 日志详情测试 ====================

    def test_get_log_not_found(self, api_client):
        """测试获取不存在的日志"""
        logger.info("开始测试：获取不存在的日志")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/logs/999999",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("获取不存在日志测试通过")

    def test_get_log_unauthorized(self, api_client):
        """测试未授权访问日志"""
        logger.info("开始测试：未授权访问日志")

        response = api_client.get(f"{self.base_url}/logs/1", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问日志测试通过")

    # ==================== IOSTAT指标测试 ====================

    def test_get_iostat_metrics_not_found(self, api_client):
        """测试获取不存在日志的IOSTAT指标"""
        logger.info("开始测试：获取不存在日志的IOSTAT指标")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/logs/999999/iostat-metrics",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("获取不存在日志IOSTAT指标测试通过")

    def test_get_iostat_metrics_unauthorized(self, api_client):
        """测试未授权访问IOSTAT指标"""
        logger.info("开始测试：未授权访问IOSTAT指标")

        response = api_client.get(f"{self.base_url}/logs/1/iostat-metrics", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问IOSTAT指标测试通过")

    # ==================== 性能抖动数据测试 ====================

    def test_get_jitter_not_found(self, api_client):
        """测试获取不存在日志的抖动数据"""
        logger.info("开始测试：获取不存在日志的抖动数据")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/logs/999999/jitter",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("获取不存在日志抖动数据测试通过")

    def test_get_jitter_unauthorized(self, api_client):
        """测试未授权访问抖动数据"""
        logger.info("开始测试：未授权访问抖动数据")

        response = api_client.get(f"{self.base_url}/logs/1/jitter", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问抖动数据测试通过")

    # ==================== FIO结果测试 ====================

    def test_get_fio_results_not_found(self, api_client):
        """测试获取不存在日志的FIO结果"""
        logger.info("开始测试：获取不存在日志的FIO结果")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/logs/999999/fio-results",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("获取不存在日志FIO结果测试通过")

    def test_get_fio_results_unauthorized(self, api_client):
        """测试未授权访问FIO结果"""
        logger.info("开始测试：未授权访问FIO结果")

        response = api_client.get(f"{self.base_url}/logs/1/fio-results", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问FIO结果测试通过")

    # ==================== IOSTAT抖动计算结果测试 ====================

    def test_get_iostat_jitter_not_found(self, api_client):
        """测试获取不存在日志的IOSTAT抖动计算结果"""
        logger.info("开始测试：获取不存在日志的IOSTAT抖动计算结果")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/logs/999999/iostat-jitter",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("获取不存在日志IOSTAT抖动计算结果测试通过")

    def test_get_iostat_jitter_unauthorized(self, api_client):
        """测试未授权访问IOSTAT抖动计算结果"""
        logger.info("开始测试：未授权访问IOSTAT抖动计算结果")

        response = api_client.get(f"{self.base_url}/logs/1/iostat-jitter", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问IOSTAT抖动计算结果测试通过")

    # ==================== 下载日志文件测试 ====================

    def test_download_log_not_found(self, api_client):
        """测试下载不存在的日志文件"""
        logger.info("开始测试：下载不存在的日志文件")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/logs/999999/download",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("下载不存在日志文件测试通过")

    def test_download_log_unauthorized(self, api_client):
        """测试未授权下载日志文件"""
        logger.info("开始测试：未授权下载日志文件")

        response = api_client.get(f"{self.base_url}/logs/1/download", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权下载日志文件测试通过")

    # ==================== 任务日志测试 ====================

    def test_get_task_logs_not_found(self, api_client):
        """测试获取不存在任务的日志"""
        logger.info("开始测试：获取不存在任务的日志")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/logs/task/999999",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        # 任务不存在时应返回空列表
        assert isinstance(data["data"], list), "data应为列表"
        logger.info("获取不存在任务日志测试通过")

    def test_get_task_logs_with_node_filter(self, api_client):
        """测试按节点ID获取任务日志"""
        logger.info("开始测试：按节点ID获取任务日志")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/logs/task/1?node_id=1",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        # 任务不存在时也返回200和空列表
        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        logger.info("按节点ID获取任务日志测试通过")

    def test_get_task_logs_unauthorized(self, api_client):
        """测试未授权访问任务日志"""
        logger.info("开始测试：未授权访问任务日志")

        response = api_client.get(f"{self.base_url}/logs/task/1", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问任务日志测试通过")

    # ==================== 实时指标测试 ====================

    def test_get_realtime_metrics_not_found(self, api_client):
        """测试获取不存在任务的实时指标"""
        logger.info("开始测试：获取不存在任务的实时指标")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/logs/task/999999/realtime-metrics",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        logger.info("获取不存在任务实时指标测试通过")

    def test_get_realtime_metrics_with_filters(self, api_client):
        """测试带过滤条件的实时指标"""
        logger.info("开始测试：带过滤条件的实时指标")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/logs/task/1/realtime-metrics?node_ids=1,2&devices=sda,sdb",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        logger.info("带过滤条件的实时指标测试通过")

    def test_get_realtime_metrics_unauthorized(self, api_client):
        """测试未授权访问实时指标"""
        logger.info("开始测试：未授权访问实时指标")

        response = api_client.get(f"{self.base_url}/logs/task/1/realtime-metrics", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问实时指标测试通过")

    # ==================== 边界条件测试 ====================

    def test_log_invalid_id_type(self, api_client):
        """测试无效的日志ID类型"""
        logger.info("开始测试：无效的日志ID类型")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/logs/invalid",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [404, 400], f"预期状态码404或400，实际: {response.status_code}"
        logger.info("无效日志ID类型测试通过")

    def test_log_negative_id(self, api_client):
        """测试负数日志ID"""
        logger.info("开始测试：负数日志ID")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/logs/-1",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("负数日志ID测试通过")

    def test_task_invalid_id_type(self, api_client):
        """测试无效的任务ID类型"""
        logger.info("开始测试：无效的任务ID类型")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/logs/task/invalid",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [404, 400], f"预期状态码404或400，实际: {response.status_code}"
        logger.info("无效任务ID类型测试通过")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
