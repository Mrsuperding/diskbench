"""指标采集服务"""

import random
from datetime import datetime


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
    def save_metrics(node_id, metrics):
        """
        保存指标到SystemMetric表

        Args:
            node_id: 节点ID
            metrics: 指标字典，包含 metric_name: value
        """
        from app.models.system_metric import SystemMetric
        from app.models import db

        for metric_name, value in metrics.items():
            # 将is_connected布尔值转为0.0或1.0
            if metric_name == 'is_connected':
                value = 1.0 if value else 0.0
                unit = None
                # 保存单个指标
                metric = SystemMetric(
                    node_id=node_id,
                    metric_type='system',
                    metric_name=metric_name,
                    metric_value=value,
                    metric_unit=unit,
                    collection_time=datetime.utcnow()
                )
                db.session.add(metric)

            # load_average 拆分成3个独立指标
            elif metric_name == 'load_average' and isinstance(value, list) and len(value) >= 3:
                for i, load_val in enumerate(value[:3]):
                    load_metric = SystemMetric(
                        node_id=node_id,
                        metric_type='system',
                        metric_name=f'load_average_{["1min", "5min", "15min"][i]}',
                        metric_value=float(load_val),
                        metric_unit=None,
                        collection_time=datetime.utcnow()
                    )
                    db.session.add(load_metric)

            else:
                # 其他指标直接保存
                unit = None
                if 'usage' in metric_name:
                    unit = '%'
                elif metric_name in ['network_tx', 'network_rx']:
                    unit = 'B/s'

                metric = SystemMetric(
                    node_id=node_id,
                    metric_type='system',
                    metric_name=metric_name,
                    metric_value=float(value),
                    metric_unit=unit,
                    collection_time=datetime.utcnow()
                )
                db.session.add(metric)

        db.session.commit()

    @staticmethod
    def collect_and_save(node_id):
        """
        采集并保存节点指标（组合方法）

        Args:
            node_id: 节点ID

        Returns:
            dict: 采集到的指标数据
        """
        metrics = MetricCollector.collect_node_metrics(node_id)
        MetricCollector.save_metrics(node_id, metrics)
        return metrics
