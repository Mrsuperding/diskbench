from datetime import datetime
from app.models import db


class EnvironmentSpace(db.Model):
    """环境空间模型 - 简化版，无成员管理"""

    __tablename__ = 'environment_spaces'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='环境空间ID')
    name = db.Column(db.String(100), nullable=False, unique=True, comment='环境空间名称')
    description = db.Column(db.Text, comment='环境空间描述')
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='所有者ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')

    # 关系
    owner = db.relationship('User', backref='created_environment_spaces')
    nodes = db.relationship('Node', back_populates='environment_space')

    # 索引
    __table_args__ = (
        db.Index('idx_owner_id', 'owner_id'),
        db.Index('idx_name', 'name'),
        db.Index('idx_is_active', 'is_active'),
    )

    def __repr__(self):
        return f'<EnvironmentSpace {self.name}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner_id,
            'owner_name': self.owner.username if self.owner else None,
            'node_count': len(self.nodes) if self.nodes else 0,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def find_by_name(cls, name):
        """根据名称查找环境空间"""
        return cls.query.filter_by(name=name).first()

    @classmethod
    def get_by_owner(cls, owner_id):
        """获取所有者的所有环境空间"""
        return cls.query.filter_by(owner_id=owner_id, is_active=True).all()

    @classmethod
    def get_all_active(cls):
        """获取所有激活的环境空间"""
        return cls.query.filter_by(is_active=True).all()
