from datetime import datetime
from app.models import db

class TaskSpace(db.Model):
    """任务空间模型"""
    
    __tablename__ = 'task_spaces'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='空间ID')
    name = db.Column(db.String(100), nullable=False, comment='空间名称')
    description = db.Column(db.Text, comment='空间描述')
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='所有者ID')
    is_public = db.Column(db.Boolean, default=False, comment='是否公开')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    task_space_members = db.relationship('TaskSpaceMember', backref='task_space', lazy='dynamic')
    test_tasks = db.relationship('TestTask', backref='task_space', lazy='dynamic')
    
    # 索引
    __table_args__ = (
        db.Index('idx_name', 'name'),
        db.Index('idx_owner_id', 'owner_id'),
        db.Index('idx_public', 'is_public'),
    )
    
    def __repr__(self):
        return f'<TaskSpace {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner_id,
            'owner_name': self.owner.username if hasattr(self, 'owner') else None,
            'is_public': self.is_public,
            'member_count': self.task_space_members.count() if hasattr(self, 'task_space_members') else 0,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def find_by_name(cls, name):
        """根据名称查找空间"""
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def get_by_owner(cls, owner_id):
        """获取用户拥有的空间"""
        return cls.query.filter_by(owner_id=owner_id).all()
    
    @classmethod
    def get_public_spaces(cls):
        """获取公开的空间"""
        return cls.query.filter_by(is_public=True).all()


class TaskSpaceMember(db.Model):
    """任务空间成员模型"""
    
    __tablename__ = 'task_space_members'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='成员ID')
    task_space_id = db.Column(db.Integer, db.ForeignKey('task_spaces.id'), nullable=False, comment='空间ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    role = db.Column(db.Enum('admin', 'member'), default='member', comment='成员角色')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, comment='加入时间')
    
    # 索引
    __table_args__ = (
        db.Index('idx_task_space_id', 'task_space_id'),
        db.Index('idx_user_id', 'user_id'),
        db.UniqueConstraint('task_space_id', 'user_id', name='uq_task_space_user'),
    )
    
    def __repr__(self):
        return f'<TaskSpaceMember {self.user_id} in {self.task_space_id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_space_id': self.task_space_id,
            'user_id': self.user_id,
            'username': self.user.username if hasattr(self, 'user') else None,
            'role': self.role,
            'joined_at': self.joined_at.isoformat(),
        }
    
    @classmethod
    def get_members_by_space(cls, task_space_id):
        """获取空间成员"""
        return cls.query.filter_by(task_space_id=task_space_id).all()
    
    @classmethod
    def get_spaces_by_user(cls, user_id):
        """获取用户加入的空间"""
        return cls.query.filter_by(user_id=user_id).all()