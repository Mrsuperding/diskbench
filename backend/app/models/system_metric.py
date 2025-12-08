from datetime import datetime
from app.models import db

class SystemMetric(db.Model):
    """系统指标模型"""
    
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='指标ID')
    node_id = db.Column(db.Integer, db.ForeignKey('nodes.id'), nullable=False, comment='节点ID')
    metric_type = db.Column(db.String(50), nullable=False, comment='指标类型')
    metric_name = db.Column(db.String(100), nullable=False, comment='指标名称')
    metric_value = db.Column(db.Float, nullable=False, comment='指标值')
    metric_unit = db.Column(db.String(50), comment='指标单位')
    collection_time = db.Column(db.DateTime, default=datetime.utcnow, comment='采集时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 索引
    __table_args__ = (
        db.Index('idx_node_id', 'node_id'),
        db.Index('idx_metric_type', 'metric_type'),
        db.Index('idx_metric_name', 'metric_name'),
        db.Index('idx_collection_time', 'collection_time'),
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
            'collection_time': self.collection_time.isoformat(),
            'created_at': self.created_at.isoformat(),
        }
    
    @classmethod
    def get_by_node(cls, node_id, metric_type=None, start_time=None, end_time=None):
        """根据节点ID获取指标"""
        query = cls.query.filter_by(node_id=node_id)
        
        if metric_type:
            query = query.filter_by(metric_type=metric_type)
        
        if start_time:
            query = query.filter(cls.collection_time >= start_time)
        
        if end_time:
            query = query.filter(cls.collection_time <= end_time)
        
        return query.order_by(cls.collection_time).all()
    
    @classmethod
    def get_latest_by_node(cls, node_id, metric_type=None):
        """获取节点最新的指标"""
        query = cls.query.filter_by(node_id=node_id)
        
        if metric_type:
            query = query.filter_by(metric_type=metric_type)
        
        return query.order_by(cls.collection_time.desc()).first()
    
    @classmethod
    def create_metric(cls, node_id, metric_type, metric_name, metric_value, metric_unit=None):
        """创建系统指标"""
        metric = cls(
            node_id=node_id,
            metric_type=metric_type,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit
        )
        db.session.add(metric)
        db.session.commit()
        return metric