from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 初始化数据库
db = SQLAlchemy()

# 任务和测试用例的多对多关联表
task_case_association = db.Table('task_case_association',
    db.Column('test_task_id', db.Integer, db.ForeignKey('test_tasks.id'), primary_key=True),
    db.Column('io_test_case_id', db.Integer, db.ForeignKey('io_test_cases.id'), primary_key=True)
)

# 任务和节点的多对多关联表
task_node_association = db.Table('task_node_association',
    db.Column('test_task_id', db.Integer, db.ForeignKey('test_tasks.id'), primary_key=True),
    db.Column('node_id', db.Integer, db.ForeignKey('nodes.id'), primary_key=True)
)

# 导入模型
from .user import User
from .login_credential import LoginCredential
from .node import Node, NodeStatusHistory
from .io_test_case import IOTestCase, TestCaseTemplate
from .test_task import TestTask, TaskExecution
from .test_result import TestResult, TestResultAggregation
from .task_space import TaskSpace, TaskSpaceMember
from .operation_log import OperationLog
from .system_metric import SystemMetric

__all__ = [
    'db',
    'User',
    'LoginCredential', 
    'Node',
    'NodeStatusHistory',
    'IOTestCase',
    'TestCaseTemplate',
    'TestTask',
    'TaskExecution',
    'TestResult',
    'TestResultAggregation',
    'TaskSpace',
    'TaskSpaceMember',
    'OperationLog',
    'SystemMetric'
]