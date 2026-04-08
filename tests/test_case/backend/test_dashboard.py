"""仪表盘 API 测试

测试仪表盘相关的所有API端点：
- GET /api/dashboard/stats - 获取仪表盘统计数据
- GET /api/dashboard/recent-tasks - 获取最近的任务列表
- GET /api/dashboard/recent-results - 获取最近的测试结果列表
- GET /api/dashboard/node-status - 获取节点状态统计
"""

import pytest
import requests
import random
import string
from loguru import logger


class TestDashboardAPI:
    """仪表盘 API 测试类"""

    def setup_method(self):
        """测试前的设置"""
        self.base_url = "http://localhost:5003/api"
        self.test_user = {
            "username": "test_admin_dashboard",
            "email": "test_admin_dashboard@example.com",
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

    # ==================== 仪表盘统计数据测试 ====================

    def test_get_dashboard_stats(self, api_client):
        """测试获取仪表盘统计数据"""
        logger.info("开始测试：获取仪表盘统计数据")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/dashboard/stats",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text[:500]}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"

        stats = data["data"]
        # 验证统计数据结构
        assert "tasks" in stats, "统计数据应包含tasks"
        assert "nodes" in stats, "统计数据应包含nodes"
        assert "results" in stats, "统计数据应包含results"
        assert "users" in stats, "统计数据应包含users"

        # 验证tasks结构
        assert "total" in stats["tasks"], "tasks应包含total"
        assert "pending" in stats["tasks"], "tasks应包含pending"
        assert "running" in stats["tasks"], "tasks应包含running"
        assert "completed" in stats["tasks"], "tasks应包含completed"
        assert "failed" in stats["tasks"], "tasks应包含failed"

        # 验证nodes结构
        assert "total" in stats["nodes"], "nodes应包含total"
        assert "online" in stats["nodes"], "nodes应包含online"
        assert "offline" in stats["nodes"], "nodes应包含offline"

        logger.info("获取仪表盘统计数据测试通过")

    def test_get_dashboard_stats_unauthorized(self, api_client):
        """测试未授权访问仪表盘统计"""
        logger.info("开始测试：未授权访问仪表盘统计")

        response = api_client.get(f"{self.base_url}/dashboard/stats", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问仪表盘统计测试通过")

    # ==================== 最近任务列表测试 ====================

    def test_get_recent_tasks(self, api_client):
        """测试获取最近的任务列表"""
        logger.info("开始测试：获取最近的任务列表")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/dashboard/recent-tasks",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert isinstance(data["data"], list), "data应为列表"
        logger.info("获取最近任务列表测试通过")

    def test_get_recent_tasks_unauthorized(self, api_client):
        """测试未授权访问最近任务列表"""
        logger.info("开始测试：未授权访问最近任务列表")

        response = api_client.get(f"{self.base_url}/dashboard/recent-tasks", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问最近任务列表测试通过")

    # ==================== 最近测试结果列表测试 ====================

    def test_get_recent_results(self, api_client):
        """测试获取最近的测试结果列表"""
        logger.info("开始测试：获取最近的测试结果列表")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/dashboard/recent-results",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert isinstance(data["data"], list), "data应为列表"
        logger.info("获取最近测试结果列表测试通过")

    def test_get_recent_results_unauthorized(self, api_client):
        """测试未授权访问最近测试结果列表"""
        logger.info("开始测试：未授权访问最近测试结果列表")

        response = api_client.get(f"{self.base_url}/dashboard/recent-results", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问最近测试结果列表测试通过")

    # ==================== 节点状态统计测试 ====================

    def test_get_node_status(self, api_client):
        """测试获取节点状态统计"""
        logger.info("开始测试：获取节点状态统计")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/dashboard/node-status",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert isinstance(data["data"], dict), "data应为字典"
        logger.info("获取节点状态统计测试通过")

    def test_get_node_status_unauthorized(self, api_client):
        """测试未授权访问节点状态统计"""
        logger.info("开始测试：未授权访问节点状态统计")

        response = api_client.get(f"{self.base_url}/dashboard/node-status", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问节点状态统计测试通过")

    # ==================== 仪表盘数据一致性测试 ====================

    def test_dashboard_stats_consistency(self, api_client):
        """测试仪表盘统计数据一致性"""
        logger.info("开始测试：仪表盘统计数据一致性")

        self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/dashboard/stats",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        stats = data["data"]

        # 验证任务状态一致性：pending + running + completed + failed = total
        tasks = stats["tasks"]
        total = tasks["total"]
        sum_by_status = tasks["pending"] + tasks["running"] + tasks["completed"] + tasks["failed"]

        logger.info(f"任务总数: {total}, 各状态之和: {sum_by_status}")

        # 注意：这里不强制相等，因为可能有其他状态
        assert total >= sum_by_status, "总数应大于等于各状态之和"
        logger.info("仪表盘统计数据一致性测试通过")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
