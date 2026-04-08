"""指标采集服务

注意：本模块仅负责采集指标数据，保存逻辑已移至 SystemMetric 模型的批量方法。
推荐使用：
- SystemMetric.bulk_insert_system_metrics() 保存系统指标
- SystemMetric.bulk_insert_partition_metrics() 保存分区指标
"""

import random


class MetricCollector:
    """指标采集服务"""

    @staticmethod
    def collect_node_metrics(node_id):
        """
        采集单个节点的指标（当前返回模拟数据）

        Args:
            node_id: 节点ID

        Returns:
            dict: 包含各项监控指标的字典
        """
        # Phase 1: 返回模拟数据，接口预留给后期实现
        # 模拟更完整的监控数据
        return {
            'cpu_usage': round(random.uniform(10, 90), 2),
            'memory_usage': round(random.uniform(20, 85), 2),
            'disk_usage': round(random.uniform(30, 80), 2),
            'network_tx': round(random.uniform(1024 * 100, 1024 * 1024 * 50), 2),  # 100KB - 50MB/s
            'network_rx': round(random.uniform(1024 * 100, 1024 * 1024 * 50), 2),  # 100KB - 50MB/s
            'load_average': [
                round(random.uniform(0.5, 4.0), 2),
                round(random.uniform(0.5, 3.5), 2),
                round(random.uniform(0.5, 3.0), 2)
            ],
            'is_connected': random.choice([True, True, True, False])  # 75%概率在线
        }

    @staticmethod
    def collect_partition_metrics(node_id, partitions):
        """
        采集节点分区指标（秒级粒度）

        Args:
            node_id: 节点ID
            partitions: 分区列表，可以是字符串列表或字典列表

        Returns:
            dict: 键为分区名称，值为该分区的监控指标
        """
        partition_metrics = {}

        for partition in partitions:
            # 解析分区名称
            if isinstance(partition, dict) and 'path' in partition:
                partition_name = partition['path']
            else:
                partition_name = str(partition)

            partition_name = partition_name.strip()

            # 模拟分区IO指标数据（秒级粒度）
            partition_metrics[partition_name] = {
                'read_iops': round(random.uniform(100, 5000), 2),      # 读取IOPS
                'write_iops': round(random.uniform(100, 5000), 2),   # 写入IOPS
                'read_throughput': round(random.uniform(1024 * 1024, 1024 * 1024 * 200), 2),  # 读取吞吐量 B/s
                'write_throughput': round(random.uniform(1024 * 1024, 1024 * 1024 * 200), 2), # 写入吞吐量 B/s
                'read_latency': round(random.uniform(0.1, 10.0), 3),   # 读取延迟 ms
                'write_latency': round(random.uniform(0.1, 10.0), 3),  # 写入延迟 ms
                'utilization': round(random.uniform(5, 95), 2),      # 分区利用率 %
            }

        return partition_metrics
