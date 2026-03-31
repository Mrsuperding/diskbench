from datetime import datetime
from app.models import db


class MonitoringConfig(db.Model):
    """监控配置模型"""

    __tablename__ = 'monitoring_configs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='配置ID')
    environment_space_id = db.Column(
        db.Integer,
        db.ForeignKey('environment_spaces.id'),
        nullable=True,
        comment='环境空间ID，为空时表示全局配置'
    )
    collection_interval = db.Column(db.Integer, default=300, comment='采集间隔(秒)，默认5分钟')
    retention_period = db.Column(db.Integer, default=7, comment='数据保留期(天)，默认7天')
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关系
    environment_space = db.relationship('EnvironmentSpace', backref='monitoring_configs')

    # 索引
    __table_args__ = (
        db.Index('idx_environment_space_id', 'environment_space_id'),
        db.Index('idx_enabled', 'enabled'),
    )

    def __repr__(self):
        if self.environment_space_id:
            return f'<MonitoringConfig for Environment {self.environment_space_id}>'
        return '<MonitoringConfig Global>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'environment_space_id': self.environment_space_id,
            'collection_interval': self.collection_interval,
            'retention_period': self.retention_period,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_config_for_environment(cls, environment_space_id):
        """获取指定环境空间的配置，如果不存在则返回全局配置"""
        config = cls.query.filter_by(environment_space_id=environment_space_id).first()
        return config if config else cls.get_global_config()

    @classmethod
    def get_global_config(cls):
        """获取全局监控配置"""
        config = cls.query.filter_by(environment_space_id=None).first()
        if not config:
            # 如果全局配置不存在，创建默认配置
            config = cls(
                environment_space_id=None,
                collection_interval=300,
                retention_period=7,
                enabled=True
            )
            db.session.add(config)
            db.session.commit()
        return config
