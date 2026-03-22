from datetime import datetime
from app.models import db, task_case_association, task_node_association

class TestTask(db.Model):
    """测试任务模型"""
    
    __tablename__ = 'test_tasks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='任务ID')
    name = db.Column(db.String(100), nullable=False, comment='任务名称')
    description = db.Column(db.Text, comment='任务描述')
    task_space_id = db.Column(db.Integer, db.ForeignKey('task_spaces.id'), nullable=True, comment='任务空间ID')
    status = db.Column(db.Enum('pending', 'running', 'completed', 'failed', 'cancelled', 'stopped', 'cancelling'), default='pending', comment='任务状态')
    priority = db.Column(db.Enum('low', 'medium', 'high'), default='medium', comment='任务优先级')
    execution_mode = db.Column(db.Enum('parallel', 'serial'), default='parallel', comment='执行模式')
    scheduled_at = db.Column(db.DateTime, comment='计划执行时间')
    started_at = db.Column(db.DateTime, comment='开始执行时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, default=1, comment='创建人')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    task_executions = db.relationship('TaskExecution', backref='test_task', lazy='dynamic')
    test_results = db.relationship('TestResult', backref='test_task', lazy='dynamic')
    nodes = db.relationship('Node', secondary=task_node_association, backref=db.backref('tasks', lazy='dynamic'))
    # io_test_cases relationship is defined in IOTestCase model via backref

    # 索引
    __table_args__ = (
        db.Index('idx_name', 'name'),
        db.Index('idx_status', 'status'),
        db.Index('idx_priority', 'priority'),
        db.Index('idx_created_by', 'created_by'),
    )
    
    def __repr__(self):
        return f'<TestTask {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        from sqlalchemy import text
        # 直接通过SQL查询获取测试用例ID列表
        case_ids = db.session.execute(
            text('SELECT io_test_case_id FROM task_case_association WHERE test_task_id = :task_id'),
            {'task_id': self.id}
        ).fetchall()
        io_test_case_ids = [case_id[0] for case_id in case_ids]
        
        # 直接通过SQL查询获取节点ID列表
        node_id_results = db.session.execute(
            text('SELECT node_id FROM task_node_association WHERE test_task_id = :task_id'),
            {'task_id': self.id}
        ).fetchall()
        node_ids = [node_id[0] for node_id in node_id_results]
        
        # 获取完整的节点信息
        from app.models import Node
        nodes = []
        for node_id in node_ids:
            node = Node.query.get(node_id)
            if node:
                nodes.append({
                    'id': node.id,
                    'name': node.name,
                    'ip_address': node.ip_address,
                    'io_partitions': node.io_partitions
                })
        
        # 计算总耗时
        total_duration = None
        if self.started_at and self.completed_at:
            total_duration = int((self.completed_at - self.started_at).total_seconds())
        
        # 获取测试用例数量
        test_case_count = len(io_test_case_ids)
        
        # 获取测试用例信息
        from app.models import IOTestCase
        io_test_cases = []
        for case_id in io_test_case_ids:
            case = IOTestCase.query.get(case_id)
            if case:
                io_test_cases.append({
                    'id': case.id,
                    'name': case.name
                })
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'node_ids': node_ids,
            'nodes': nodes,  # 返回完整的节点信息
            'io_test_case_ids': io_test_case_ids,
            'io_test_cases': io_test_cases,  # 返回测试用例信息
            'task_space_id': self.task_space_id,
            'status': self.status,
            'priority': self.priority,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_duration': total_duration,
            'node_count': len(nodes),
            'test_case_count': test_case_count,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def find_by_name(cls, name):
        """根据名称查找任务"""
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def get_by_user(cls, user_id):
        """获取用户的任务"""
        return cls.query.filter_by(created_by=user_id).all()
    
    @classmethod
    def get_by_status(cls, status):
        """根据状态获取任务"""
        return cls.query.filter_by(status=status).all()


class TaskExecution(db.Model):
    """任务执行模型"""
    
    __tablename__ = 'task_executions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='执行ID')
    test_task_id = db.Column(db.Integer, db.ForeignKey('test_tasks.id'), nullable=False, comment='任务ID')
    status = db.Column(db.Enum('pending', 'running', 'completed', 'failed', 'cancelled', 'stopped', 'cancelling'), default='pending', comment='执行状态')
    error_message = db.Column(db.Text, comment='错误信息')
    start_time = db.Column(db.DateTime, comment='开始时间')
    end_time = db.Column(db.DateTime, comment='结束时间')
    duration = db.Column(db.Integer, comment='执行时长(秒)')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 索引
    __table_args__ = (
        db.Index('idx_test_task_id', 'test_task_id'),
        db.Index('idx_status', 'status'),
        db.Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f'<TaskExecution {self.test_task_id} - {self.status}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'test_task_id': self.test_task_id,
            'status': self.status,
            'error_message': self.error_message,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'created_at': self.created_at.isoformat(),
        }