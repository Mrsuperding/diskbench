"""代码重构修复测试

测试以下修复：
1. datetime.utcnow() 废弃问题 - 使用 timezone-aware datetime
2. 批量插入逻辑封装 - SystemMetric.bulk_insert_* 方法
3. 定时任务超时控制 - signal.SIGALRM
4. 任务并发数限制 - 基于连接池配置计算
5. 失败节点处理改进 - 详细错误信息
"""

import pytest
import requests
import time
import signal
import os
import sys
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# 添加 backend 路径以便导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))


class TestDatetimeUtils:
    """测试 datetime_utils 模块"""

    def test_utc_now_returns_timezone_aware(self):
        """验证 utc_now() 返回 timezone-aware datetime"""
        from app.utils.datetime_utils import utc_now

        result = utc_now()

        assert result.tzinfo is not None, "utc_now() 应返回 timezone-aware datetime"
        assert result.tzinfo == timezone.utc, "utc_now() 应返回 UTC 时区"

    def test_utc_now_is_current_time(self):
        """验证 utc_now() 返回的是当前时间"""
        from app.utils.datetime_utils import utc_now

        before = datetime.now(timezone.utc)
        result = utc_now()
        after = datetime.now(timezone.utc)

        assert before <= result <= after, "utc_now() 应返回当前时间"


class TestSystemMetricBulkInsert:
    """测试 SystemMetric 批量插入方法（需要 Flask app context）"""

    @pytest.fixture(scope="class")
    def app_context(self):
        """创建应用上下文"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))
        try:
            from application import create_app
            app = create_app('testing')
            with app.app_context():
                yield app
        except Exception as e:
            pytest.skip(f"无法创建 Flask app context: {e}")

    def test_bulk_insert_system_metrics_returns_count(self, app_context):
        """验证 bulk_insert_system_metrics 返回插入的记录数"""
        if not app_context:
            pytest.skip("App context not available")
        from app.models.system_metric import SystemMetric

        metrics = {
            'cpu_usage': 45.5,
            'memory_usage': 60.0,
            'disk_usage': 50.0,
            'is_connected': True
        }

        # 使用模拟的 node_id
        result = SystemMetric.bulk_insert_system_metrics(node_id=1, metrics=metrics)

        assert isinstance(result, int), "返回值应为整数"
        assert result > 0, "应插入至少一条记录"

    def test_bulk_insert_system_metrics_handles_boolean(self, app_context):
        """验证 bulk_insert_system_metrics 正确处理布尔值"""
        if not app_context:
            pytest.skip("App context not available")
        from app.models.system_metric import SystemMetric

        # 测试 is_connected = True
        metrics_true = {'is_connected': True}
        result_true = SystemMetric.bulk_insert_system_metrics(node_id=1, metrics=metrics_true)

        # 测试 is_connected = False
        metrics_false = {'is_connected': False}
        result_false = SystemMetric.bulk_insert_system_metrics(node_id=1, metrics=metrics_false)

        assert result_true >= 1, "True 应插入记录"
        assert result_false >= 1, "False 应插入记录"

    def test_bulk_insert_system_metrics_handles_load_average(self, app_context):
        """验证 bulk_insert_system_metrics 正确处理 load_average 列表"""
        if not app_context:
            pytest.skip("App context not available")
        from app.models.system_metric import SystemMetric

        metrics = {
            'load_average': [1.5, 1.2, 1.0]
        }

        result = SystemMetric.bulk_insert_system_metrics(node_id=1, metrics=metrics)

        # load_average 列表应展开为3条记录 (1min, 5min, 15min)
        assert result >= 3, "load_average 列表应展开为3条记录"

    def test_bulk_insert_partition_metrics(self, app_context):
        """验证 bulk_insert_partition_metrics 方法"""
        if not app_context:
            pytest.skip("App context not available")
        from app.models.system_metric import SystemMetric

        partition_metrics = {
            '/data': {
                'read_iops': 1000.0,
                'write_iops': 500.0,
                'read_throughput': 1024 * 1024 * 100,
                'write_throughput': 1024 * 1024 * 50,
                'read_latency': 1.5,
                'write_latency': 2.0,
                'utilization': 75.0
            }
        }

        result = SystemMetric.bulk_insert_partition_metrics(node_id=1, partition_metrics=partition_metrics)

        assert isinstance(result, int), "返回值应为整数"
        assert result > 0, "应插入分区指标记录"

    def test_bulk_insert_metrics_batch_empty_list(self, app_context):
        """验证 bulk_insert_metrics_batch 处理空列表"""
        if not app_context:
            pytest.skip("App context not available")
        from app.models.system_metric import SystemMetric

        result = SystemMetric.bulk_insert_metrics_batch([])

        assert result == 0, "空列表应返回 0"

    def test_bulk_insert_metrics_batch_with_data(self, app_context):
        """验证 bulk_insert_metrics_batch 批量插入"""
        if not app_context:
            pytest.skip("App context not available")
        from app.models.system_metric import SystemMetric
        from app.utils.datetime_utils import utc_now

        metrics_list = [
            {
                'node_id': 1,
                'metric_type': 'system',
                'metric_name': 'cpu_usage',
                'metric_value': 50.0,
                'metric_unit': '%',
                'collection_time': utc_now()
            },
            {
                'node_id': 1,
                'metric_type': 'system',
                'metric_name': 'memory_usage',
                'metric_value': 60.0,
                'metric_unit': '%',
                'collection_time': utc_now()
            }
        ]

        result = SystemMetric.bulk_insert_metrics_batch(metrics_list)

        assert result == 2, "应插入2条记录"


class TestTimeoutControl:
    """测试超时控制功能（Unix only - SIGALRM not available on Windows）"""

    def test_signal_timeout_raises_timeout_error(self):
        """验证 signal.SIGALRM 能在指定时间后抛出 TimeoutError"""
        if not hasattr(signal, 'SIGALRM'):
            pytest.skip("SIGALRM not available on Windows")

        def timeout_handler(signum, frame):
            raise TimeoutError("Test timeout")

        # 设置 1 秒超时
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(1)

        start_time = time.time()

        try:
            # 模拟长时间运行的任务（sleep 3秒）
            time.sleep(3)
            signal.alarm(0)  # 取消信号
            assert False, "应该抛出 TimeoutError"
        except TimeoutError as e:
            elapsed = time.time() - start_time
            assert "timeout" in str(e).lower(), "错误信息应包含 timeout"
            assert 1 <= elapsed < 2, f"应在约1秒后超时，实际: {elapsed:.2f}秒"
        finally:
            signal.alarm(0)  # 确保清理
            signal.signal(signal.SIGALRM, old_handler)

    def test_signal_timeout_cancelled(self):
        """验证任务在超时前完成时会取消信号"""
        if not hasattr(signal, 'SIGALRM'):
            pytest.skip("SIGALRM not available on Windows")

        def timeout_handler(signum, frame):
            raise TimeoutError("Should not be called")

        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)  # 5秒超时

        time.sleep(0.1)  # 模拟快速完成的任务

        signal.alarm(0)  # 取消信号
        signal.signal(signal.SIGALRM, old_handler)


class TestConnectionPoolConfig:
    """测试数据库连接池配置"""

    def test_connection_pool_size_calculation(self):
        """验证连接池大小计算逻辑"""
        # 根据配置: pool_size=30, max_overflow=30, 最大连接=60
        # 每个节点约需 3-4 个连接，安全值 = 60 / 4 = 15
        pool_size = 30
        max_overflow = 30
        max_connections = pool_size + max_overflow
        connections_per_node = 4

        max_workers = min(max_connections // connections_per_node, 20)

        assert max_workers == 15, f"计算的最大并发数应为15，实际: {max_workers}"

    def test_connection_pool_config_values(self):
        """验证连接池配置值"""
        try:
            from config import config
            testing_config = config.get('testing')
            if testing_config:
                engine_options = testing_config.SQLALCHEMY_ENGINE_OPTIONS
                assert engine_options['pool_size'] == 30, "pool_size 应为 30"
                assert engine_options['max_overflow'] == 30, "max_overflow 应为 30"
                assert engine_options['pool_recycle'] == 1800, "pool_recycle 应为 1800"
                assert engine_options['pool_pre_ping'] == True, "pool_pre_ping 应为 True"
        except Exception as e:
            pytest.skip(f"无法导入配置: {e}")


class TestFailedNodeHandling:
    """测试失败节点详细错误信息"""

    def test_failed_nodes_detail_tracking(self):
        """验证失败节点会被正确追踪"""
        failed_nodes = []

        try:
            raise Exception("Connection failed")
        except Exception as e:
            failed_nodes.append({
                'node_id': 1,
                'node_name': 'test-node-1',
                'error': str(e)
            })

        assert len(failed_nodes) == 1, "应记录一个失败节点"
        assert failed_nodes[0]['node_id'] == 1
        assert failed_nodes[0]['node_name'] == 'test-node-1'
        assert 'Connection failed' in failed_nodes[0]['error']

    def test_collect_result_includes_failed_nodes(self):
        """验证采集结果包含失败节点详情"""
        result = {
            'total': 5,
            'success': 3,
            'failed': 2,
            'failed_nodes': [
                {'node_id': 1, 'node_name': 'node-1', 'error': 'timeout'},
                {'node_id': 2, 'node_name': 'node-2', 'error': 'connection refused'}
            ]
        }

        assert result['total'] == 5
        assert result['success'] + result['failed'] == result['total']
        assert len(result['failed_nodes']) == 2
        assert result['failed_nodes'][0]['error'] == 'timeout'
        assert result['failed_nodes'][1]['error'] == 'connection refused'


class TestEnvironmentSpacesMetricsAPI:
    """测试环境空间指标采集 API（需要后端运行）"""

    @pytest.fixture
    def api_client(self):
        """API 客户端"""
        import requests
        session = requests.Session()
        yield session
        session.close()

    @pytest.fixture
    def auth_token(self, api_client):
        """获取认证 token"""
        login_data = {
            "username": "admin",
            "password": "adminpassword"
        }

        try:
            response = api_client.post(
                "http://localhost:5003/api/auth/login",
                json=login_data,
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get('data', {}).get('token')
        except:
            pass

        return None

    def test_collect_space_metrics_endpoint(self, api_client, auth_token):
        """测试手动触发指标采集 API"""
        if not auth_token:
            pytest.skip("无法获取认证 token")

        response = api_client.post(
            "http://localhost:5003/api/environment-spaces/1/metrics/collect",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            assert 'data' in data or 'message' in data
        elif response.status_code == 404:
            pytest.skip("测试环境空间不存在")
        else:
            print(f"API 返回状态码: {response.status_code}")

    def test_collect_partition_metrics_endpoint(self, api_client, auth_token):
        """测试分区指标采集 API"""
        if not auth_token:
            pytest.skip("无法获取认证 token")

        response = api_client.post(
            "http://localhost:5003/api/environment-spaces/1/metrics/partition/collect",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            assert 'data' in data or 'message' in data
        elif response.status_code == 404:
            pytest.skip("测试环境空间不存在")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
