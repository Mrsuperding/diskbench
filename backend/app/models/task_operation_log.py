from datetime import datetime
from app.models import db
import json

class TaskOperationLog(db.Model):
    """任务操作日志模型 - 存储任务执行过程中的操作记录"""

    __tablename__ = 'task_operation_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='日志ID')
    test_task_id = db.Column(db.Integer, db.ForeignKey('test_tasks.id'), nullable=False, comment='任务ID')
    task_execution_id = db.Column(db.Integer, db.ForeignKey('task_executions.id'), nullable=True, comment='执行ID')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, comment='时间戳')
    level = db.Column(db.String(20), default='INFO', comment='日志级别')
    message = db.Column(db.Text, nullable=False, comment='日志消息')
    context = db.Column(db.Text, comment='上下文信息(JSON)')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    # 索引
    __table_args__ = (
        db.Index('idx_task_operation_task_id', 'test_task_id'),
        db.Index('idx_task_operation_execution_id', 'task_execution_id'),
        db.Index('idx_task_operation_timestamp', 'timestamp'),
        db.Index('idx_task_operation_level', 'level'),
    )

    def __repr__(self):
        return f'<TaskOperationLog {self.test_task_id} - {self.message[:50]}>'

    def to_dict(self):
        """转换为字典"""
        context_dict = {}
        if self.context:
            try:
                context_dict = json.loads(self.context)
            except:
                context_dict = {}

        return {
            'id': self.id,
            'test_task_id': self.test_task_id,
            'task_execution_id': self.task_execution_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'level': self.level,
            'message': self.message,
            'context': context_dict,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def create_log(cls, task_id, message, level='INFO', context=None, execution_id=None):
        """创建日志记录"""
        context_json = None
        if context:
            try:
                context_json = json.dumps(context, ensure_ascii=False)
            except:
                context_json = None

        log = cls(
            test_task_id=task_id,
            task_execution_id=execution_id,
            level=level,
            message=message,
            context=context_json,
            timestamp=datetime.utcnow()
        )
        return log

    @classmethod
    def get_by_task(cls, task_id, limit=100):
        """根据任务ID获取日志（限制数量，按时间倒序）"""
        return cls.query.filter_by(test_task_id=task_id)\
            .order_by(cls.timestamp.desc())\
            .limit(limit)\
            .all()

    @classmethod
    def get_by_execution(cls, execution_id, limit=100):
        """根据执行ID获取日志"""
        return cls.query.filter_by(task_execution_id=execution_id)\
            .order_by(cls.timestamp.asc())\
            .limit(limit)\
            .all()

    @classmethod
    def delete_old_logs(cls, task_id, keep_count=100):
        """删除旧日志，只保留最新的N条"""
        logs = cls.query.filter_by(test_task_id=task_id)\
            .order_by(cls.timestamp.desc())\
            .offset(keep_count)\
            .all()

        for log in logs:
            db.session.delete(log)
