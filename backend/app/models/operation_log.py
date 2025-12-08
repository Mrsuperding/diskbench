from datetime import datetime
from app.models import db

class OperationLog(db.Model):
    """操作日志模型"""
    
    __tablename__ = 'operation_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='日志ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='操作用户ID')
    operation_type = db.Column(db.String(50), nullable=False, comment='操作类型')
    operation_target = db.Column(db.String(100), nullable=False, comment='操作目标')
    target_id = db.Column(db.Integer, comment='目标ID')
    operation_details = db.Column(db.Text, comment='操作详情')
    ip_address = db.Column(db.String(50), comment='IP地址')
    user_agent = db.Column(db.String(500), comment='用户代理')
    result = db.Column(db.Enum('success', 'failed', 'partial'), default='success', comment='操作结果')
    error_message = db.Column(db.Text, comment='错误信息')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='操作时间')
    
    # 索引
    __table_args__ = (
        db.Index('idx_user_id', 'user_id'),
        db.Index('idx_operation_type', 'operation_type'),
        db.Index('idx_operation_target', 'operation_target'),
        db.Index('idx_result', 'result'),
        db.Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f'<OperationLog {self.operation_type} - {self.result}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'operation_type': self.operation_type,
            'operation_target': self.operation_target,
            'target_id': self.target_id,
            'operation_details': self.operation_details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'result': self.result,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
        }
    
    @classmethod
    def get_by_user(cls, user_id):
        """获取用户的操作日志"""
        return cls.query.filter_by(user_id=user_id).all()
    
    @classmethod
    def get_by_operation_type(cls, operation_type):
        """根据操作类型获取日志"""
        return cls.query.filter_by(operation_type=operation_type).all()
    
    @classmethod
    def get_failed_operations(cls):
        """获取失败的操作日志"""
        return cls.query.filter_by(result='failed').all()
    
    @classmethod
    def create_log(cls, user_id, operation_type, operation_target, target_id=None, operation_details=None, ip_address=None, user_agent=None, result='success', error_message=None):
        """创建操作日志"""
        log = cls(
            user_id=user_id,
            operation_type=operation_type,
            operation_target=operation_target,
            target_id=target_id,
            operation_details=operation_details,
            ip_address=ip_address,
            user_agent=user_agent,
            result=result,
            error_message=error_message
        )
        db.session.add(log)
        db.session.commit()
        return log