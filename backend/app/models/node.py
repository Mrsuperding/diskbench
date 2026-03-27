from datetime import datetime
from app.models import db

class Node(db.Model):
    """节点模型"""
    
    __tablename__ = 'nodes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='节点ID')
    name = db.Column(db.String(100), unique=True, nullable=False, comment='节点名称')
    ip_address = db.Column(db.String(50), nullable=False, comment='IP地址')  # 移除unique约束，允许IP重复
    status = db.Column(db.Enum('active', 'inactive', 'maintenance', 'error'), default='inactive', comment='节点状态')
    # type字段暂时注释掉，因为数据库中不存在该字段
    # type = db.Column(db.Enum('master', 'worker'), default='worker', nullable=False, comment='节点类型')
    os_type = db.Column(db.String(50), comment='操作系统类型')
    os_version = db.Column(db.String(100), comment='操作系统版本')
    cpu_info = db.Column(db.String(255), comment='CPU信息')
    memory_total = db.Column(db.BigInteger, comment='总内存(字节)')
    disk_total = db.Column(db.BigInteger, comment='总磁盘空间(字节)')
    login_credential_id = db.Column(db.Integer, db.ForeignKey('login_credentials.id'), nullable=True, comment='登录凭证ID')
    environment_space_id = db.Column(db.Integer, db.ForeignKey('environment_spaces.id'), nullable=True, comment='所属环境空间ID')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='创建人')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    last_heartbeat = db.Column(db.DateTime, comment='最后心跳时间')
    io_partitions = db.Column(db.JSON, default=list, comment='IO分区列表')
    
    # 关系
    environment_space = db.relationship('EnvironmentSpace', back_populates='nodes')
    status_history = db.relationship('NodeStatusHistory', backref='node', lazy='dynamic')
    test_results = db.relationship('TestResult', backref='node', lazy='dynamic')
    system_metrics = db.relationship('SystemMetric', backref='node', lazy='dynamic')
    
    # 索引
    __table_args__ = (
        db.Index('idx_name', 'name'),
        db.Index('idx_ip_address', 'ip_address'),
        db.Index('idx_status', 'status'),
        db.Index('idx_created_by', 'created_by'),
    )
    
    def __repr__(self):
        return f'<Node {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'ip_address': self.ip_address,
            'status': self.status,
            'os_type': self.os_type,
            'os_version': self.os_version,
            'cpu_info': self.cpu_info,
            'memory_total': self.memory_total,
            'disk_total': self.disk_total,
            'login_credential_id': self.login_credential_id,
            'environment_space_id': self.environment_space_id,
            'environment_space_name': self.environment_space.name if self.environment_space else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'io_partitions': self.io_partitions or [],
            # 确保返回前端需要的字段
            'port': 8000,  # 默认端口
            'type': 'worker',  # 默认节点类型，不依赖数据库字段
            'description': '',  # 默认描述
        }
    
    @classmethod
    def find_by_name(cls, name):
        """根据名称查找节点"""
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def find_by_ip(cls, ip_address):
        """根据IP地址查找节点"""
        return cls.query.filter_by(ip_address=ip_address).first()
    
    @classmethod
    def get_by_user(cls, user_id):
        """获取用户的节点"""
        return cls.query.filter_by(created_by=user_id).all()


class NodeStatusHistory(db.Model):
    """节点状态历史模型"""
    
    __tablename__ = 'node_status_history'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='历史记录ID')
    node_id = db.Column(db.Integer, db.ForeignKey('nodes.id'), nullable=False, comment='节点ID')
    status = db.Column(db.Enum('active', 'inactive', 'maintenance', 'error'), nullable=False, comment='状态')
    message = db.Column(db.Text, comment='状态变更消息')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='记录时间')
    
    # 索引
    __table_args__ = (
        db.Index('idx_node_id', 'node_id'),
        db.Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f'<NodeStatusHistory {self.node_id} - {self.status}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'node_id': self.node_id,
            'status': self.status,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
        }