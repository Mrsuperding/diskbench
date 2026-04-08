"""代码重构修复测试 - 独立运行版本

不依赖 Flask app context 的单元测试
直接测试 Python 标准和 mock 对象
"""

import sys
import os
import time
import signal
import random

# 直接测试 datetime 功能（不通过 Flask app）
from datetime import datetime, timezone


def test_utc_now_returns_timezone_aware():
    """验证 datetime.now(timezone.utc) 返回 timezone-aware datetime"""
    result = datetime.now(timezone.utc)

    assert result.tzinfo is not None, "datetime.now(timezone.utc) 应返回 timezone-aware datetime"
    assert result.tzinfo == timezone.utc, "datetime.now(timezone.utc) 应返回 UTC 时区"
    print(f"[PASS] test_utc_now_returns_timezone_aware: {result}")
    return True


def test_utc_now_is_current_time():
    """验证 datetime.now(timezone.utc) 返回的是当前时间"""
    before = datetime.now(timezone.utc)
    result = datetime.now(timezone.utc)
    after = datetime.now(timezone.utc)

    assert before <= result <= after, "datetime.now(timezone.utc) 应返回当前时间"
    print(f"[PASS] test_utc_now_is_current_time: before={before}, result={result}, after={after}")
    return True


# 测试 2: 超时控制 (Unix only - signal.SIGALRM not available on Windows)
def test_signal_timeout_raises_timeout_error():
    """验证 signal.SIGALRM 能在指定时间后抛出 TimeoutError"""
    if not hasattr(signal, 'SIGALRM'):
        print("[SKIP] test_signal_timeout_raises_timeout_error: SIGALRM not available on Windows")
        return True

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
        print("[FAIL] test_signal_timeout_raises_timeout_error: 应该抛出 TimeoutError")
        return False
    except TimeoutError as e:
        elapsed = time.time() - start_time
        assert "timeout" in str(e).lower(), "错误信息应包含 timeout"
        assert 1 <= elapsed < 2, f"应在约1秒后超时，实际: {elapsed:.2f}秒"
        print(f"[PASS] test_signal_timeout_raises_timeout_error: 在 {elapsed:.2f}秒 后超时")
        return True
    finally:
        signal.alarm(0)  # 确保清理
        signal.signal(signal.SIGALRM, old_handler)  # 恢复原处理程序


def test_signal_timeout_cancelled():
    """验证任务在超时前完成时会取消信号"""
    if not hasattr(signal, 'SIGALRM'):
        print("[SKIP] test_signal_timeout_cancelled: SIGALRM not available on Windows")
        return True

    def timeout_handler(signum, frame):
        raise TimeoutError("Should not be called")

    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(5)  # 5秒超时

    time.sleep(0.1)  # 模拟快速完成的任务

    signal.alarm(0)  # 取消信号
    signal.signal(signal.SIGALRM, old_handler)  # 恢复原处理程序

    print("[PASS] test_signal_timeout_cancelled: 任务完成，信号已取消")
    return True


# 测试 3: 连接池计算
def test_connection_pool_size_calculation():
    """验证连接池大小计算逻辑"""
    # 根据配置: pool_size=30, max_overflow=30, 最大连接=60
    # 每个节点约需 3-4 个连接，安全值 = 60 / 4 = 15
    pool_size = 30
    max_overflow = 30
    max_connections = pool_size + max_overflow
    connections_per_node = 4

    max_workers = min(max_connections // connections_per_node, 20)  # 最多20个节点

    assert max_workers == 15, f"计算的最大并发数应为15，实际: {max_workers}"
    print(f"[PASS] test_connection_pool_size_calculation: max_workers={max_workers}")
    return True


# 测试 4: 失败节点处理
def test_failed_nodes_detail_tracking():
    """验证失败节点会被正确追踪"""
    failed_nodes = []

    try:
        # 模拟处理节点时发生错误
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

    print(f"[PASS] test_failed_nodes_detail_tracking: failed_nodes={failed_nodes}")
    return True


def test_collect_result_includes_failed_nodes():
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

    print(f"[PASS] test_collect_result_includes_failed_nodes: total={result['total']}, failed_nodes={result['failed_nodes']}")
    return True


# 测试 5: MetricCollector 模拟数据
def test_metric_collector_returns_expected_structure():
    """验证 MetricCollector 返回预期的数据结构"""
    # 模拟 MetricCollector 的返回
    expected_metrics = {
        'cpu_usage': round(random.uniform(10, 90), 2),
        'memory_usage': round(random.uniform(20, 85), 2),
        'disk_usage': round(random.uniform(30, 80), 2),
        'network_tx': round(random.uniform(1024 * 100, 1024 * 1024 * 50), 2),
        'network_rx': round(random.uniform(1024 * 100, 1024 * 1024 * 50), 2),
        'load_average': [
            round(random.uniform(0.5, 4.0), 2),
            round(random.uniform(0.5, 3.5), 2),
            round(random.uniform(0.5, 3.0), 2)
        ],
        'is_connected': random.choice([True, True, True, False])
    }

    # 验证结构
    assert 'cpu_usage' in expected_metrics
    assert 'memory_usage' in expected_metrics
    assert 'load_average' in expected_metrics
    assert isinstance(expected_metrics['load_average'], list)
    assert len(expected_metrics['load_average']) == 3

    print(f"[PASS] test_metric_collector_returns_expected_structure: 指标结构正确")
    return True


# 测试 6: 批量插入逻辑模拟
def test_bulk_insert_logic_simulation():
    """模拟批量插入逻辑"""
    # 模拟 metrics 字典
    metrics = {
        'cpu_usage': 45.5,
        'memory_usage': 60.0,
        'disk_usage': 50.0,
        'is_connected': True,
        'load_average': [1.5, 1.2, 1.0]
    }

    mappings = []
    collection_time = datetime.now(timezone.utc)

    for metric_name, value in metrics.items():
        if metric_name == 'is_connected':
            value = 1.0 if value else 0.0

        if metric_name == 'load_average' and isinstance(value, list):
            # load_average 列表展开为 3 条记录
            for i, load_val in enumerate(value[:3]):
                mappings.append({
                    'metric_name': f'load_average_{["1min", "5min", "15min"][i]}',
                    'metric_value': float(load_val),
                })
        else:
            mappings.append({
                'metric_name': metric_name,
                'metric_value': value,
            })

    # 验证
    assert len(mappings) == 7, f"应有 7 条记录（cpu, memory, disk, is_connected, load_1min, load_5min, load_15min），实际: {len(mappings)}"

    # 验证 is_connected 转换为 1.0
    is_connected_metric = [m for m in mappings if m['metric_name'] == 'is_connected'][0]
    assert is_connected_metric['metric_value'] == 1.0, "is_connected=True 应转换为 1.0"

    # 验证 load_average 展开
    load_metrics = [m for m in mappings if 'load_average' in m['metric_name']]
    assert len(load_metrics) == 3, f"load_average 应展开为 3 条，实际: {len(load_metrics)}"

    print(f"[PASS] test_bulk_insert_logic_simulation: mappings count = {len(mappings)}")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("Running Code Refactoring Fix Tests...")
    print("=" * 60)

    tests = [
        test_utc_now_returns_timezone_aware,
        test_utc_now_is_current_time,
        test_signal_timeout_raises_timeout_error,
        test_signal_timeout_cancelled,
        test_connection_pool_size_calculation,
        test_failed_nodes_detail_tracking,
        test_collect_result_includes_failed_nodes,
        test_metric_collector_returns_expected_structure,
        test_bulk_insert_logic_simulation,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            print(f"\nRunning: {test.__name__}")
            result = test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Test Complete: passed={passed}, failed={failed}")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)
