from flask_restx import Api, Resource, fields
from flask import Blueprint
from app.models.user import User
from app.models.node import Node
from app.models.test_task import TestTask
from app.models.io_test_case import IOTestCase, TestCaseTemplate
from app.models.test_result import TestResult

# 创建API蓝图
api_docs_bp = Blueprint('api_docs', __name__)

# 初始化API
def init_api(app):
    # 延迟导入视图蓝图，避免循环导入
    from app.views.auth import auth_bp
    from app.views.users import users_bp
    from app.views.nodes import nodes_bp
    from app.views.tasks import tasks_bp
    from app.views.io_cases import io_cases_bp
    from app.views.results import results_bp
    from app.views.task_spaces import task_spaces_bp
    from app.views.dashboard import dashboard_bp
    api = Api(
        api_docs_bp,
        version='1.0',
        title='IO性能测试平台API文档',
        description='IO性能测试平台的RESTful API文档',
        doc='/docs'  # API文档访问路径
    )
    
    # 命名空间定义
    auth_ns = api.namespace('auth', description='认证相关接口')
    users_ns = api.namespace('users', description='用户管理接口')
    nodes_ns = api.namespace('nodes', description='节点管理接口')
    tasks_ns = api.namespace('tasks', description='测试任务接口')
    io_cases_ns = api.namespace('io-cases', description='IO测试用例接口')
    results_ns = api.namespace('results', description='测试结果接口')
    dashboard_ns = api.namespace('dashboard', description='仪表盘接口')
    task_spaces_ns = api.namespace('task-spaces', description='任务空间接口')
    
    # 数据模型定义
    # 用户模型
    user_model = api.model('User', {
        'id': fields.Integer(readonly=True, description='用户ID'),
        'username': fields.String(required=True, description='用户名'),
        'email': fields.String(required=True, description='邮箱'),
        'role': fields.String(description='用户角色'),
        'status': fields.String(description='用户状态'),
        'created_at': fields.DateTime(readonly=True, description='创建时间'),
        'updated_at': fields.DateTime(readonly=True, description='更新时间')
    })
    
    # 节点模型
    node_model = api.model('Node', {
        'id': fields.Integer(readonly=True, description='节点ID'),
        'name': fields.String(required=True, description='节点名称'),
        'ip_address': fields.String(required=True, description='IP地址'),
        'status': fields.String(description='节点状态'),
        'os_type': fields.String(description='操作系统类型'),
        'os_version': fields.String(description='操作系统版本'),
        'cpu_info': fields.String(description='CPU信息'),
        'memory_total': fields.Integer(description='总内存(MB)'),
        'disk_total': fields.Integer(description='总磁盘(GB)'),
        'login_credential_id': fields.Integer(description='登录凭证ID'),
        'created_by': fields.Integer(description='创建人ID'),
        'created_at': fields.DateTime(readonly=True, description='创建时间'),
        'updated_at': fields.DateTime(readonly=True, description='更新时间')
    })
    
    # 测试任务模型
    task_model = api.model('TestTask', {
        'id': fields.Integer(readonly=True, description='任务ID'),
        'name': fields.String(required=True, description='任务名称'),
        'description': fields.String(description='任务描述'),
        'task_space_id': fields.Integer(description='任务空间ID'),
        'io_case_id': fields.Integer(description='IO用例ID'),
        'node_id': fields.Integer(description='节点ID'),
        'status': fields.String(description='任务状态'),
        'created_by': fields.Integer(description='创建人ID'),
        'created_at': fields.DateTime(readonly=True, description='创建时间'),
        'updated_at': fields.DateTime(readonly=True, description='更新时间'),
        'started_at': fields.DateTime(readonly=True, description='开始时间'),
        'finished_at': fields.DateTime(readonly=True, description='完成时间')
    })
    
    # IO用例模型
    io_case_model = api.model('IOTestCase', {
        'id': fields.Integer(readonly=True, description='用例ID'),
        'name': fields.String(required=True, description='用例名称'),
        'description': fields.String(description='用例描述'),
        'tool': fields.String(description='测试工具'),
        'parameters': fields.Raw(description='测试参数'),
        'is_public': fields.Boolean(description='是否公开'),
        'created_by': fields.Integer(description='创建人ID'),
        'created_at': fields.DateTime(readonly=True, description='创建时间'),
        'updated_at': fields.DateTime(readonly=True, description='更新时间')
    })
    
    # 测试结果模型
    result_model = api.model('TestResult', {
        'id': fields.Integer(readonly=True, description='结果ID'),
        'task_id': fields.Integer(description='任务ID'),
        'node_id': fields.Integer(description='节点ID'),
        'io_case_id': fields.Integer(description='IO用例ID'),
        'status': fields.String(description='执行状态'),
        'metrics': fields.Raw(description='测试指标'),
        'output_log': fields.String(description='输出日志'),
        'created_at': fields.DateTime(readonly=True, description='创建时间'),
        'updated_at': fields.DateTime(readonly=True, description='更新时间')
    })
    
    # 任务空间模型
    task_space_model = api.model('TaskSpace', {
        'id': fields.Integer(readonly=True, description='空间ID'),
        'name': fields.String(required=True, description='空间名称'),
        'description': fields.String(description='空间描述'),
        'owner_id': fields.Integer(description='所有者ID'),
        'is_public': fields.Boolean(description='是否公开'),
        'created_at': fields.DateTime(readonly=True, description='创建时间'),
        'updated_at': fields.DateTime(readonly=True, description='更新时间')
    })
    
    # 任务空间成员模型
    task_space_member_model = api.model('TaskSpaceMember', {
        'id': fields.Integer(readonly=True, description='成员ID'),
        'task_space_id': fields.Integer(description='空间ID'),
        'user_id': fields.Integer(description='用户ID'),
        'role': fields.String(description='成员角色'),
        'joined_at': fields.DateTime(readonly=True, description='加入时间')
    })
    
    # 示例健康检查端点
    @api.route('/health')
    class HealthCheck(Resource):
        @api.doc('health_check')
        def get(self):
            '''健康检查'''
            return {'status': 'healthy'}
    
    # 注册API蓝图到应用
    app.register_blueprint(api_docs_bp, url_prefix='/api')
    
    return api