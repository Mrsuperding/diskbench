"""任务空间 API 测试

测试任务空间相关的所有API端点：
- GET /api/task-spaces - 获取任务空间列表
- GET /api/task-spaces/<id> - 获取任务空间详情
- POST /api/task-spaces - 创建任务空间
- PUT /api/task-spaces/<id> - 更新任务空间
- DELETE /api/task-spaces/<id> - 删除任务空间
- GET /api/task-spaces/<id>/members - 获取任务空间成员列表
- POST /api/task-spaces/<id>/members - 添加任务空间成员
- PUT /api/task-spaces/<id>/members/<member_id> - 更新成员角色
- DELETE /api/task-spaces/<id>/members/<member_id> - 移除成员
"""

import pytest
import requests
import random
import string
import time
from loguru import logger


class TestTaskSpacesAPI:
    """任务空间 API 测试类"""

    def setup_method(self):
        """测试前的设置"""
        self.base_url = "http://localhost:5003/api"
        self.test_user = {
            "username": "test_admin_space",
            "email": "test_admin_space@example.com",
            "password": "test123456"
        }
        self.test_user2 = {
            "username": "test_member_space",
            "email": "test_member_space@example.com",
            "password": "test123456"
        }
        self.token = None
        self.token2 = None
        self.created_spaces = []
        self.created_users = []

    def teardown_method(self):
        """测试后的清理"""
        if self.token:
            for space_id in self.created_spaces:
                try:
                    requests.delete(
                        f"{self.base_url}/task-spaces/{space_id}",
                        headers={"Authorization": f"Bearer {self.token}"},
                        timeout=5
                    )
                    logger.info(f"成功删除任务空间: {space_id}")
                except Exception as e:
                    logger.warning(f"删除任务空间失败: {space_id}, {e}")

    def _register_and_login(self, user_data=None):
        """注册并登录，获取token"""
        user = user_data or self.test_user

        # 注册用户
        register_response = requests.post(
            f"{self.base_url}/auth/register",
            json=user,
            timeout=5
        )
        self.created_users.append(user["username"])

        # 登录获取token
        login_response = requests.post(
            f"{self.base_url}/auth/login",
            json={
                "username": user["username"],
                "password": user["password"]
            },
            timeout=5
        )

        if login_response.status_code == 200:
            return login_response.json()["data"]["token"]
        return None

    def _create_task_space(self, name=None, is_public=False):
        """创建任务空间"""
        if not self.token:
            self.token = self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        space_data = {
            "name": name or f"test_space_{random_str}",
            "description": f"Test space description {random_str}",
            "is_public": is_public
        }

        response = requests.post(
            f"{self.base_url}/task-spaces",
            json=space_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        if response.status_code == 201:
            space_id = response.json()["data"]["id"]
            self.created_spaces.append(space_id)
            return space_id
        return None

    # ==================== 任务空间列表测试 ====================

    def test_get_task_spaces_empty(self, api_client):
        """测试获取空任务空间列表"""
        logger.info("开始测试：获取空任务空间列表")

        self.token = self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/task-spaces",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text[:200]}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert "items" in data["data"], "data应包含items字段"
        logger.info("获取空任务空间列表测试通过")

    def test_get_task_spaces_with_data(self, api_client):
        """测试获取包含数据的任务空间列表"""
        logger.info("开始测试：获取包含数据的任务空间列表")

        self.token = self._register_and_login()

        # 创建测试空间
        space_id = self._create_task_space()
        assert space_id is not None, "创建任务空间失败"

        response = api_client.get(
            f"{self.base_url}/task-spaces",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert len(data["data"]["items"]) >= 1, "空间列表应至少包含创建的空间"
        logger.info("获取任务空间列表测试通过")

    def test_get_task_spaces_with_pagination(self, api_client):
        """测试任务空间列表分页"""
        logger.info("开始测试：任务空间列表分页")

        self.token = self._register_and_login()

        # 创建多个测试空间
        for i in range(3):
            space_id = self._create_task_space()
            assert space_id is not None, f"创建任务空间{i}失败"

        response = api_client.get(
            f"{self.base_url}/task-spaces?page=1&per_page=2",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "per_page" in data["data"], "data应包含per_page字段"
        assert data["data"]["per_page"] == 2, "每页数量应为2"
        logger.info("任务空间列表分页测试通过")

    def test_get_task_spaces_by_name(self, api_client):
        """测试按名称搜索任务空间"""
        logger.info("开始测试：按名称搜索任务空间")

        self.token = self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        space_name = f"unique_space_name_{random_str}"

        # 创建特定名称的空间
        space_id = self._create_task_space(name=space_name)
        assert space_id is not None, "创建任务空间失败"

        # 搜索该名称
        response = api_client.get(
            f"{self.base_url}/task-spaces?name={space_name}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert len(data["data"]["items"]) >= 1, "应找到匹配的空间"
        logger.info("按名称搜索任务空间测试通过")

    def test_get_task_spaces_unauthorized(self, api_client):
        """测试未授权访问任务空间列表"""
        logger.info("开始测试：未授权访问任务空间列表")

        response = api_client.get(f"{self.base_url}/task-spaces", timeout=5)

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [401, 403], f"预期状态码401或403，实际: {response.status_code}"
        logger.info("未授权访问任务空间列表测试通过")

    # ==================== 单个任务空间操作测试 ====================

    def test_get_task_space_by_id(self, api_client):
        """测试获取单个任务空间"""
        logger.info("开始测试：获取单个任务空间")

        self.token = self._register_and_login()

        # 创建测试空间
        space_id = self._create_task_space()
        assert space_id is not None, "创建任务空间失败"

        response = api_client.get(
            f"{self.base_url}/task-spaces/{space_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert data["data"]["id"] == space_id, "返回的空间ID应匹配"
        logger.info("获取单个任务空间测试通过")

    def test_get_task_space_not_found(self, api_client):
        """测试获取不存在的任务空间"""
        logger.info("开始测试：获取不存在的任务空间")

        self.token = self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/task-spaces/999999",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("获取不存在任务空间测试通过")

    # ==================== 创建任务空间测试 ====================

    def test_create_task_space_success(self, api_client):
        """测试成功创建任务空间"""
        logger.info("开始测试：成功创建任务空间")

        self.token = self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        space_data = {
            "name": f"new_space_{random_str}",
            "description": f"Test space description {random_str}",
            "is_public": False
        }

        response = api_client.post(
            f"{self.base_url}/task-spaces",
            json=space_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text[:200]}")

        assert response.status_code == 201, f"预期状态码201，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        assert data["data"]["name"] == space_data["name"], "空间名称应匹配"
        space_id = data["data"]["id"]
        self.created_spaces.append(space_id)
        logger.info("创建任务空间测试通过")

    def test_create_public_task_space(self, api_client):
        """测试创建公共任务空间"""
        logger.info("开始测试：创建公共任务空间")

        self.token = self._register_and_login()

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        space_data = {
            "name": f"public_space_{random_str}",
            "is_public": True
        }

        response = api_client.post(
            f"{self.base_url}/task-spaces",
            json=space_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 201, f"预期状态码201，实际: {response.status_code}"
        data = response.json()
        assert data["data"]["is_public"] == True, "空间应为公共空间"
        space_id = data["data"]["id"]
        self.created_spaces.append(space_id)
        logger.info("创建公共任务空间测试通过")

    def test_create_task_space_missing_name(self, api_client):
        """测试创建任务空间缺少名称"""
        logger.info("开始测试：创建任务空间缺少名称")

        self.token = self._register_and_login()

        space_data = {
            "description": "Test description"
        }

        response = api_client.post(
            f"{self.base_url}/task-spaces",
            json=space_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        logger.info("创建任务空间缺少名称测试通过")

    def test_create_task_space_empty_name(self, api_client):
        """测试创建任务空间使用空名称"""
        logger.info("开始测试：创建任务空间使用空名称")

        self.token = self._register_and_login()

        space_data = {
            "name": ""
        }

        response = api_client.post(
            f"{self.base_url}/task-spaces",
            json=space_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        logger.info("创建任务空间空名称测试通过")

    # ==================== 更新任务空间测试 ====================

    def test_update_task_space_name(self, api_client):
        """测试更新任务空间名称"""
        logger.info("开始测试：更新任务空间名称")

        self.token = self._register_and_login()

        # 创建测试空间
        space_id = self._create_task_space()
        assert space_id is not None, "创建任务空间失败"

        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        update_data = {"name": f"updated_space_{random_str}"}

        response = api_client.put(
            f"{self.base_url}/task-spaces/{space_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert data["data"]["name"] == update_data["name"], "空间名称应更新"
        logger.info("更新任务空间名称测试通过")

    def test_update_task_space_description(self, api_client):
        """测试更新任务空间描述"""
        logger.info("开始测试：更新任务空间描述")

        self.token = self._register_and_login()

        # 创建测试空间
        space_id = self._create_task_space()
        assert space_id is not None, "创建任务空间失败"

        update_data = {"description": "Updated description"}

        response = api_client.put(
            f"{self.base_url}/task-spaces/{space_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert data["data"]["description"] == update_data["description"], "空间描述应更新"
        logger.info("更新任务空间描述测试通过")

    def test_update_task_space_not_found(self, api_client):
        """测试更新不存在的任务空间"""
        logger.info("开始测试：更新不存在的任务空间")

        self.token = self._register_and_login()

        update_data = {"name": "updated_name"}

        response = api_client.put(
            f"{self.base_url}/task-spaces/999999",
            json=update_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("更新不存在任务空间测试通过")

    # ==================== 删除任务空间测试 ====================

    def test_delete_task_space_success(self, api_client):
        """测试成功删除任务空间"""
        logger.info("开始测试：成功删除任务空间")

        self.token = self._register_and_login()

        # 创建测试空间
        space_id = self._create_task_space()
        assert space_id is not None, "创建任务空间失败"

        response = api_client.delete(
            f"{self.base_url}/task-spaces/{space_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"

        # 验证空间已被删除
        get_response = api_client.get(
            f"{self.base_url}/task-spaces/{space_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )
        assert get_response.status_code == 404, "空间应已被删除"
        self.created_spaces.remove(space_id)
        logger.info("删除任务空间测试通过")

    def test_delete_task_space_not_found(self, api_client):
        """测试删除不存在的任务空间"""
        logger.info("开始测试：删除不存在的任务空间")

        self.token = self._register_and_login()

        response = api_client.delete(
            f"{self.base_url}/task-spaces/999999",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("删除不存在任务空间测试通过")

    # ==================== 任务空间成员管理测试 ====================

    def test_get_space_members(self, api_client):
        """测试获取任务空间成员列表"""
        logger.info("开始测试：获取任务空间成员列表")

        self.token = self._register_and_login()

        # 创建测试空间
        space_id = self._create_task_space()
        assert space_id is not None, "创建任务空间失败"

        response = api_client.get(
            f"{self.base_url}/task-spaces/{space_id}/members",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        # 创建者应该是第一个成员
        assert len(data["data"]) >= 1, "应至少包含创建者"
        logger.info("获取任务空间成员列表测试通过")

    def test_add_space_member(self, api_client):
        """测试添加任务空间成员"""
        logger.info("开始测试：添加任务空间成员")

        self.token = self._register_and_login()
        self.token2 = self._register_and_login(self.test_user2)

        # 创建测试空间
        space_id = self._create_task_space()
        assert space_id is not None, "创建任务空间失败"

        member_data = {
            "username": self.test_user2["username"],
            "role": "member"
        }

        response = api_client.post(
            f"{self.base_url}/task-spaces/{space_id}/members",
            json=member_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text[:200]}")

        assert response.status_code == 201, f"预期状态码201，实际: {response.status_code}"
        data = response.json()
        assert "data" in data, "响应应包含data字段"
        logger.info("添加任务空间成员测试通过")

    def test_add_space_member_not_found_user(self, api_client):
        """测试添加不存在的用户到任务空间"""
        logger.info("开始测试：添加不存在的用户到任务空间")

        self.token = self._register_and_login()

        # 创建测试空间
        space_id = self._create_task_space()
        assert space_id is not None, "创建任务空间失败"

        member_data = {
            "username": "nonexistent_user_12345",
            "role": "member"
        }

        response = api_client.post(
            f"{self.base_url}/task-spaces/{space_id}/members",
            json=member_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("添加不存在用户到任务空间测试通过")

    def test_add_space_member_missing_username(self, api_client):
        """测试添加成员缺少用户名"""
        logger.info("开始测试：添加成员缺少用户名")

        self.token = self._register_and_login()

        # 创建测试空间
        space_id = self._create_task_space()
        assert space_id is not None, "创建任务空间失败"

        member_data = {"role": "member"}

        response = api_client.post(
            f"{self.base_url}/task-spaces/{space_id}/members",
            json=member_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 400, f"预期状态码400，实际: {response.status_code}"
        logger.info("添加成员缺少用户名测试通过")

    def test_update_member_role(self, api_client):
        """测试更新成员角色"""
        logger.info("开始测试：更新成员角色")

        self.token = self._register_and_login()
        self.token2 = self._register_and_login(self.test_user2)

        # 创建测试空间
        space_id = self._create_task_space()
        assert space_id is not None, "创建任务空间失败"

        # 添加成员
        member_data = {"username": self.test_user2["username"], "role": "member"}
        add_response = api_client.post(
            f"{self.base_url}/task-spaces/{space_id}/members",
            json=member_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )
        assert add_response.status_code == 201, "添加成员失败"
        member_id = add_response.json()["data"]["id"]

        # 更新成员角色
        update_data = {"role": "admin"}

        response = api_client.put(
            f"{self.base_url}/task-spaces/{space_id}/members/{member_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        data = response.json()
        assert data["data"]["role"] == update_data["role"], "角色应更新"
        logger.info("更新成员角色测试通过")

    def test_remove_member(self, api_client):
        """测试移除任务空间成员"""
        logger.info("开始测试：移除任务空间成员")

        self.token = self._register_and_login()
        self.token2 = self._register_and_login(self.test_user2)

        # 创建测试空间
        space_id = self._create_task_space()
        assert space_id is not None, "创建任务空间失败"

        # 添加成员
        member_data = {"username": self.test_user2["username"], "role": "member"}
        add_response = api_client.post(
            f"{self.base_url}/task-spaces/{space_id}/members",
            json=member_data,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )
        assert add_response.status_code == 201, "添加成员失败"
        member_id = add_response.json()["data"]["id"]

        # 移除成员
        response = api_client.delete(
            f"{self.base_url}/task-spaces/{space_id}/members/{member_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 200, f"预期状态码200，实际: {response.status_code}"
        logger.info("移除任务空间成员测试通过")

    # ==================== 边界条件测试 ====================

    def test_task_space_invalid_id_type(self, api_client):
        """测试无效的空间ID类型"""
        logger.info("开始测试：无效的空间ID类型")

        self.token = self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/task-spaces/invalid",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code in [404, 400], f"预期状态码404或400，实际: {response.status_code}"
        logger.info("无效空间ID类型测试通过")

    def test_task_space_negative_id(self, api_client):
        """测试负数空间ID"""
        logger.info("开始测试：负数空间ID")

        self.token = self._register_and_login()

        response = api_client.get(
            f"{self.base_url}/task-spaces/-1",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=5
        )

        logger.info(f"响应状态码: {response.status_code}")

        assert response.status_code == 404, f"预期状态码404，实际: {response.status_code}"
        logger.info("负数空间ID测试通过")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
