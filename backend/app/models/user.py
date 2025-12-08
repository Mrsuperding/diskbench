from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db

class User(db.Model):
    """用户模型"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户ID')
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    email = db.Column(db.String(100), unique=True, nullable=False, comment='邮箱地址')
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希')
    role = db.Column(db.Enum('admin', 'user'), default='user', comment='用户角色')
    status = db.Column(db.Enum('active', 'inactive', 'locked'), default='active', comment='账户状态')
    avatar_url = db.Column(db.String(500), comment='头像URL')
    last_login_at = db.Column(db.DateTime, comment='最后登录时间')
    login_count = db.Column(db.Integer, default=0, comment='登录次数')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    login_credentials = db.relationship('LoginCredential', backref='creator', lazy='dynamic')
    nodes = db.relationship('Node', backref='creator', lazy='dynamic')
    io_test_cases = db.relationship('IOTestCase', backref='creator', lazy='dynamic')
    test_tasks = db.relationship('TestTask', backref='creator', lazy='dynamic')
    task_spaces = db.relationship('TaskSpace', backref='owner', lazy='dynamic')
    task_space_memberships = db.relationship('TaskSpaceMember', backref='user', lazy='dynamic')
    operation_logs = db.relationship('OperationLog', backref='user', lazy='dynamic')
    
    # 索引
    __table_args__ = (
        db.Index('idx_username', 'username'),
        db.Index('idx_email', 'email'),
        db.Index('idx_role_status', 'role', 'status'),
        db.Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_email=True):
        """转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'status': self.status,
            'avatar_url': self.avatar_url,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'login_count': self.login_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_email:
            data['email'] = self.email
            
        return data
    
    @classmethod
    def find_by_username(cls, username):
        """根据用户名查找用户"""
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def find_by_email(cls, email):
        """根据邮箱查找用户"""
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def create_user(cls, username, email, password, role='user'):
        """创建新用户"""
        user = cls(
            username=username,
            email=email,
            role=role
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user