from datetime import datetime, timezone
from app.models import db


def utc_now():
    """获取当前 UTC 时间"""
    return datetime.now(timezone.utc)


class SystemMetric(db.Model):
    """系统指标模型"""

    __tablename__ = 'system_metrics'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='指标ID')
    node_id = db.Column(db.Integer, db.ForeignKey('nodes.id'), nullable=False, comment='节点ID')
    metric_type = db.Column(db.String(50), nullable=False, comment='指标类型')
    metric_name = db.Column(db.String(100), nullable=False, comment='指标名称')
    metric_value = db.Column(db.Float, nullable=False, comment='指标值')
    metric_unit = db.Column(db.String(50), comment='指标单位')
    partition_name = db.Column(db.String(255), nullable=True, comment='分区名称，用于分区级别指标')
    collection_time = db.Column(db.DateTime, default=utc_now, comment='采集时间')
    created_at = db.Column(db.DateTime, default=utc_now, comment='创建时间')
    
    # 索引
    __table_args__ = (
        db.Index('idx_node_id', 'node_id'),
        db.Index('idx_metric_type', 'metric_type'),
        db.Index('idx_metric_name', 'metric_name'),
        db.Index('idx_partition_name', 'partition_name'),
        db.Index('idx_collection_time', 'collection_time'),
        db.Index('idx_node_partition_time', 'node_id', 'partition_name', 'collection_time'),
    )
    
    def __repr__(self):
        return f'<SystemMetric {self.metric_name} - {self.metric_value}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'node_id': self.node_id,
            'metric_type': self.metric_type,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_unit': self.metric_unit,
            'partition_name': self.partition_name,
            'collection_time': self.collection_time.isoformat(),
            'created_at': self.created_at.isoformat(),
        }
    
    @classmethod
    def get_by_node(cls, node_id, metric_type=None, start_time=None, end_time=None, partition_name=None):
        """根据节点ID获取指标"""
        query = cls.query.filter_by(node_id=node_id)

        if metric_type:
            query = query.filter_by(metric_type=metric_type)

        if partition_name:
            query = query.filter_by(partition_name=partition_name)

        if start_time:
            query = query.filter(cls.collection_time >= start_time)

        if end_time:
            query = query.filter(cls.collection_time <= end_time)

        return query.order_by(cls.collection_time).all()

    @classmethod
    def get_latest_by_node(cls, node_id, metric_type=None, partition_name=None):
        """获取节点最新的指标"""
        query = cls.query.filter_by(node_id=node_id)

        if metric_type:
            query = query.filter_by(metric_type=metric_type)

        if partition_name:
            query = query.filter_by(partition_name=partition_name)

        return query.order_by(cls.collection_time.desc()).first()

    @classmethod
    def create_metric(cls, node_id, metric_type, metric_name, metric_value, metric_unit=None, partition_name=None):
        """创建系统指标"""
        metric = cls(
            node_id=node_id,
            metric_type=metric_type,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit,
            partition_name=partition_name
        )
        db.session.add(metric)
        db.session.commit()
        return metric

    @classmethod
    def get_metrics_by_environment(cls, environment_space_id, start_time, end_time, metric_name=None, partition_name=None):
        """获取环境空间内所有节点的指标数据"""
        from app.models.node import Node

        query = db.session.query(cls).join(Node).filter(
            Node.environment_space_id == environment_space_id,
            cls.collection_time >= start_time,
            cls.collection_time <= end_time
        )

        if metric_name:
            query = query.filter(cls.metric_name == metric_name)

        if partition_name:
            query = query.filter(cls.partition_name == partition_name)

        return query.order_by(cls.collection_time.asc()).all()

    @classmethod
    def get_partition_metrics_by_node(cls, node_id, partition_name, start_time=None, end_time=None):
        """获取指定节点指定分区的所有指标"""
        query = cls.query.filter_by(node_id=node_id, partition_name=partition_name)

        if start_time:
            query = query.filter(cls.collection_time >= start_time)

        if end_time:
            query = query.filter(cls.collection_time <= end_time)

        return query.order_by(cls.collection_time.asc()).all()

    @classmethod
    def bulk_insert_system_metrics(cls, node_id, metrics, collection_time=None):
        """
        便捷方法：批量插入单个节点的系统指标

        Args:
            node_id: 节点 ID
            metrics: 指标字典，如 {'cpu_usage': 45.5, 'memory_usage': 60.0, ...}
            collection_time: 采集时间，默认当前时间

        Returns:
            int: 插入的记录数
        """
        if collection_time is None:
            collection_time = utc_now()

        mappings = []
        for metric_name, value in metrics.items():
            # 处理 is_connected 布尔值
            if metric_name == 'is_connected':
                value = 1.0 if value else 0.0

            # 处理 load_average 列表
            if metric_name == 'load_average' and isinstance(value, list):
                for i, load_val in enumerate(value[:3]):
                    mappings.append({
                        'node_id': node_id,
                        'metric_type': 'system',
                        'metric_name': f'load_average_{["1min", "5min", "15min"][i]}',
                        'metric_value': float(load_val),
                        'metric_unit': None,
                        'collection_time': collection_time
                    })
            else:
                # 确定单位
                unit = None
                if 'usage' in metric_name:
                    unit = '%'
                elif metric_name in ['network_tx', 'network_rx']:
                    unit = 'B/s'

                mappings.append({
                    'node_id': node_id,
                    'metric_type': 'system',
                    'metric_name': metric_name,
                    'metric_value': float(value) if metric_name != 'is_connected' else value,
                    'metric_unit': unit,
                    'collection_time': collection_time
                })

        if mappings:
            db.session.bulk_insert_mappings(cls, mappings)

        return len(mappings)

    @classmethod
    def bulk_insert_partition_metrics(cls, node_id, partition_metrics, collection_time=None):
        """
        批量插入节点分区指标

        Args:
            node_id: 节点 ID
            partition_metrics: 分区指标字典，如 {'/dev/sda1': {'read_iops': 100, ...}, ...}
            collection_time: 采集时间，默认当前时间

        Returns:
            int: 插入的记录数
        """
        if collection_time is None:
            collection_time = utc_now()

        mappings = []

        for partition_name, metrics in partition_metrics.items():
            for metric_name, value in metrics.items():
                # 确定单位
                unit = None
                if 'usage' in metric_name or 'utilization' in metric_name:
                    unit = '%'
                elif 'throughput' in metric_name:
                    unit = 'B/s'
                elif 'latency' in metric_name:
                    unit = 'ms'
                elif 'iops' in metric_name:
                    unit = 'ops'

                mappings.append({
                    'node_id': node_id,
                    'metric_type': 'partition',
                    'metric_name': metric_name,
                    'metric_value': float(value),
                    'metric_unit': unit,
                    'partition_name': partition_name,
                    'collection_time': collection_time
                })

        if mappings:
            db.session.bulk_insert_mappings(cls, mappings)

        return len(mappings)

    @classmethod
    def bulk_insert_metrics_batch(cls, metrics_list):
        """
        批量插入任意指标数据列表

        Args:
            metrics_list: 指标数据列表，如 [{'node_id': 1, 'metric_name': 'cpu_usage', ...}, ...]

        Returns:
            int: 插入的记录数
        """
        if not metrics_list:
            return 0

        db.session.bulk_insert_mappings(cls, metrics_list)
        return len(metrics_list)
