from datetime import datetime
import os
import tempfile
from loguru import logger
from app.models import db
from app.utils.encryption import encrypt_password, decrypt_password

class LoginCredential(db.Model):
    """登录凭证模型"""
    
    __tablename__ = 'login_credentials'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='登录信息ID')
    alias = db.Column(db.String(100), unique=True, nullable=False, comment='登录别名')
    host = db.Column(db.String(255), nullable=False, comment='主机地址')
    port = db.Column(db.Integer, default=22, comment='SSH端口')
    username = db.Column(db.String(100), nullable=False, comment='用户名')
    auth_type = db.Column(db.Enum('password', 'key'), default='password', comment='认证类型')
    password_encrypted = db.Column(db.Text, comment='加密后的密码')
    private_key_path = db.Column(db.String(500), comment='私钥文件路径')
    private_key_encrypted = db.Column(db.Text, comment='加密后的私钥内容')
    passphrase_encrypted = db.Column(db.Text, comment='加密后的私钥密码')
    root_password_encrypted = db.Column(db.Text, comment='Root密码（加密）')
    base_path = db.Column(db.String(500), default='/tmp', comment='基础文件路径')
    platform_partition = db.Column(db.String(500), default='/opt/io_platform', comment='平台分区路径，用于存储运行日志、IO日志和依赖文件')
    description = db.Column(db.Text, comment='描述信息')
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='创建人')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    nodes = db.relationship('Node', backref='login_credential', lazy='dynamic')
    
    # 索引
    __table_args__ = (
        db.Index('idx_alias', 'alias'),
        db.Index('idx_host', 'host'),
        db.Index('idx_created_by', 'created_by'),
        db.Index('idx_active', 'is_active'),
    )
    
    def __repr__(self):
        return f'<LoginCredential {self.alias}>'
    
    def set_password(self, password):
        """设置密码"""
        self.password_encrypted = encrypt_password(password)
    
    def get_password(self):
        """获取密码"""
        if self.password_encrypted:
            return decrypt_password(self.password_encrypted)
        return None
    
    def set_private_key(self, private_key):
        """设置私钥内容"""
        if private_key:
            self.private_key_encrypted = encrypt_password(private_key)
        else:
            self.private_key_encrypted = None
    
    def get_private_key(self):
        """获取私钥内容"""
        if self.private_key_encrypted:
            return decrypt_password(self.private_key_encrypted)
        return None
    
    def get_passphrase(self):
        """获取私钥密码"""
        if self.passphrase_encrypted:
            return decrypt_password(self.passphrase_encrypted)
        return None
    
    def get_private_key_file(self):
        """获取私钥文件路径"""
        # 如果有私钥路径，直接返回
        if self.private_key_path:
            return self.private_key_path
        
        # 如果有加密的私钥内容，创建临时文件
        private_key = self.get_private_key()
        if private_key:
            try:
                # 创建临时文件
                fd, path = tempfile.mkstemp(prefix='ssh_key_', suffix='.pem')
                with os.fdopen(fd, 'w') as f:
                    f.write(private_key)
                return path
            except Exception as e:
                logger.error(f"Failed to create temporary private key file: {e}")
                return None
        
        return None
    
    def set_passphrase(self, passphrase):
        """设置私钥密码"""
        if passphrase:
            self.passphrase_encrypted = encrypt_password(passphrase)
        else:
            self.passphrase_encrypted = None
    
    def get_passphrase(self):
        """获取私钥密码"""
        if self.passphrase_encrypted:
            return decrypt_password(self.passphrase_encrypted)
        return None
    
    def set_root_password(self, password):
        """设置root密码"""
        if password:
            self.root_password_encrypted = encrypt_password(password)
    
    def get_root_password(self):
        """获取root密码"""
        if self.root_password_encrypted:
            return decrypt_password(self.root_password_encrypted)
        return None
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'alias': self.alias,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'auth_type': self.auth_type,
            'base_path': self.base_path,
            'platform_partition': self.platform_partition,
            'description': self.description,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_sensitive:
            data['password'] = self.get_password()
            data['root_password'] = self.get_root_password()
            data['private_key_path'] = self.private_key_path
            data['private_key'] = self.get_private_key()
            data['passphrase'] = self.get_passphrase()
            
        return data
    
    def get_private_key_file(self):
        """获取私钥文件路径，如果有私钥内容则创建临时文件"""
        if self.private_key_path and os.path.exists(self.private_key_path):
            return self.private_key_path
        
        private_key = self.get_private_key()
        if private_key:
            # 创建临时文件保存私钥内容
            fd, path = tempfile.mkstemp(suffix='.pem')
            try:
                with os.fdopen(fd, 'w') as f:
                    f.write(private_key)
                # 设置文件权限
                os.chmod(path, 0o600)
                return path
            except:
                os.close(fd)
                os.unlink(path)
                raise
        
        return None
    
    def cleanup_private_key_file(self, file_path):
        """清理临时私钥文件"""
        if file_path and file_path.startswith(tempfile.gettempdir()):
            try:
                os.unlink(file_path)
            except:
                pass
    
    def test_connection(self):
        """测试连接"""
        from app.utils.ssh_client import SSHClient
        
        try:
            # 直接将当前实例传递给SSHClient
            client = SSHClient(self)
            
            result = client.test_connection()
            client.disconnect()  # 使用disconnect方法代替close方法
            return result
        except Exception as e:
            return False, str(e)
    
    @classmethod
    def find_by_alias(cls, alias):
        """根据别名查找"""
        return cls.query.filter_by(alias=alias).first()
    
    @classmethod
    def get_by_user(cls, user_id):
        """获取用户的登录凭证"""
        return cls.query.filter_by(created_by=user_id).all()