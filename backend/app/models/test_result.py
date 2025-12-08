from datetime import datetime
from app.models import db

class TestResult(db.Model):
    """测试结果模型"""
    
    __tablename__ = 'test_results'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='结果ID')
    test_task_id = db.Column(db.Integer, db.ForeignKey('test_tasks.id'), nullable=False, comment='任务ID')
    node_id = db.Column(db.Integer, db.ForeignKey('nodes.id'), nullable=False, comment='节点ID')
    io_test_case_id = db.Column(db.Integer, db.ForeignKey('io_test_cases.id'), nullable=False, comment='测试用例ID')
    task_execution_id = db.Column(db.Integer, db.ForeignKey('task_executions.id'), nullable=False, comment='执行ID')
    tool = db.Column(db.Enum('fio', 'iozone'), default='fio', comment='测试工具')
    command = db.Column(db.Text, comment='执行命令')
    raw_output = db.Column(db.Text, comment='原始输出')
    parsed_results = db.Column(db.JSON, comment='解析后的结果')
    status = db.Column(db.Enum('success', 'failed', 'partial'), default='success', comment='结果状态')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    result_aggregations = db.relationship('TestResultAggregation', backref='test_result', lazy='dynamic')
    
    # 索引
    __table_args__ = (
        db.Index('idx_test_task_id', 'test_task_id'),
        db.Index('idx_node_id', 'node_id'),
        db.Index('idx_io_test_case_id', 'io_test_case_id'),
        db.Index('idx_status', 'status'),
        db.Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f'<TestResult {self.id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'test_task_id': self.test_task_id,
            'node_id': self.node_id,
            'io_test_case_id': self.io_test_case_id,
            'task_execution_id': self.task_execution_id,
            'tool': self.tool,
            'command': self.command,
            'raw_output': self.raw_output,
            'parsed_results': self.parsed_results,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
        }
    
    @classmethod
    def get_by_test_task(cls, test_task_id):
        """根据任务ID获取结果"""
        return cls.query.filter_by(test_task_id=test_task_id).all()
    
    @classmethod
    def get_by_node(cls, node_id):
        """根据节点ID获取结果"""
        return cls.query.filter_by(node_id=node_id).all()


class TestResultAggregation(db.Model):
    """测试结果聚合模型"""
    
    __tablename__ = 'test_result_aggregations'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='聚合ID')
    test_result_id = db.Column(db.Integer, db.ForeignKey('test_results.id'), nullable=False, comment='结果ID')
    metric_name = db.Column(db.String(100), nullable=False, comment='指标名称')
    metric_value = db.Column(db.Float, nullable=False, comment='指标值')
    metric_unit = db.Column(db.String(50), comment='指标单位')
    metric_type = db.Column(db.Enum('average', 'min', 'max', 'sum', 'value'), default='value', comment='指标类型')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 索引
    __table_args__ = (
        db.Index('idx_test_result_id', 'test_result_id'),
        db.Index('idx_metric_name', 'metric_name'),
    )
    
    def __repr__(self):
        return f'<TestResultAggregation {self.metric_name} - {self.metric_value}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'test_result_id': self.test_result_id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_unit': self.metric_unit,
            'metric_type': self.metric_type,
            'created_at': self.created_at.isoformat(),
        }