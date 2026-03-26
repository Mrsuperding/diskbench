from datetime import datetime
from app.models import db

class IOTestCase(db.Model):
    """IO测试用例模型"""
    
    __tablename__ = 'io_test_cases'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='测试用例ID')
    name = db.Column(db.String(100), unique=True, nullable=False, comment='用例名称')
    description = db.Column(db.Text, comment='用例描述')
    tool = db.Column(db.Enum('fio', 'iozone'), default='fio', comment='测试工具')
    parameters = db.Column(db.JSON, nullable=False, comment='测试参数')
    partition_mode = db.Column(db.Enum('concurrent', 'sequential'), default='concurrent', comment='分区执行模式：concurrent并发，sequential串行')
    is_public = db.Column(db.Boolean, default=False, comment='是否公开')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='创建人')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    test_tasks = db.relationship('TestTask', secondary='task_case_association', backref=db.backref('io_test_cases', lazy='dynamic'), lazy='dynamic')
    
    # 索引
    __table_args__ = (
        db.Index('idx_name', 'name'),
        db.Index('idx_created_by', 'created_by'),
        db.Index('idx_public', 'is_public'),
    )
    
    def __repr__(self):
        return f'<IOTestCase {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'tool': self.tool,
            'parameters': self.parameters,
            'partition_mode': self.partition_mode,
            'is_public': self.is_public,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def find_by_name(cls, name):
        """根据名称查找测试用例"""
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def get_by_user(cls, user_id):
        """获取用户的测试用例"""
        return cls.query.filter_by(created_by=user_id).all()
    
    @classmethod
    def get_public_cases(cls):
        """获取公开的测试用例"""
        return cls.query.filter_by(is_public=True).all()


class TestCaseTemplate(db.Model):
    """测试用例模板模型"""
    
    __tablename__ = 'test_case_templates'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='模板ID')
    name = db.Column(db.String(100), unique=True, nullable=False, comment='模板名称')
    description = db.Column(db.Text, comment='模板描述')
    tool = db.Column(db.Enum('fio', 'iozone'), default='fio', comment='测试工具')
    parameters = db.Column(db.JSON, nullable=False, comment='模板参数')
    category = db.Column(db.String(50), comment='模板分类')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 索引
    __table_args__ = (
        db.Index('idx_name', 'name'),
        db.Index('idx_category', 'category'),
    )
    
    def __repr__(self):
        return f'<TestCaseTemplate {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'tool': self.tool,
            'parameters': self.parameters,
            'category': self.category,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def find_by_name(cls, name):
        """根据名称查找模板"""
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def get_by_category(cls, category):
        """根据分类获取模板"""
        return cls.query.filter_by(category=category).all()