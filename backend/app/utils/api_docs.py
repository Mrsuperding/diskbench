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
    
    # 认证接口文档
    @auth_ns.route('/login')
    class Login(Resource):
        @api.doc(description='用户登录')
        @api.expect(api.model('Login', {
            'username': fields.String(required=True, description='用户名或邮箱'),
            'password': fields.String(required=True, description='密码')
        }))
        def post(self):
            '''用户登录'''
            return {'message': '登录接口'}
    
    @auth_ns.route('/logout')
    class Logout(Resource):
        @api.doc(description='用户登出')
        def post(self):
            '''用户登出'''
            return {'message': '登出接口'}
    
    @auth_ns.route('/refresh')
    class Refresh(Resource):
        @api.doc(description='刷新访问token')
        def post(self):
            '''刷新访问token'''
            return {'message': '刷新token接口'}
    
    @auth_ns.route('/userinfo')
    class UserInfo(Resource):
        @api.doc(description='获取用户信息')
        def get(self):
            '''获取用户信息'''
            return {'message': '获取用户信息接口'}
    
    @auth_ns.route('/password')
    class UpdatePassword(Resource):
        @api.doc(description='修改密码')
        @api.expect(api.model('UpdatePassword', {
            'old_password': fields.String(required=True, description='旧密码'),
            'new_password': fields.String(required=True, description='新密码')
        }))
        def put(self):
            '''修改密码'''
            return {'message': '修改密码接口'}
    
    @auth_ns.route('/register')
    class Register(Resource):
        @api.doc(description='用户注册（管理员功能）')
        @api.expect(api.model('Register', {
            'username': fields.String(required=True, description='用户名'),
            'email': fields.String(required=True, description='邮箱'),
            'password': fields.String(required=True, description='密码'),
            'role': fields.String(description='用户角色，可选值：admin, user，默认为user')
        }))
        def post(self):
            '''用户注册'''
            return {'message': '注册接口'}
    
    # 用户管理接口文档
    @users_ns.route('')
    class Users(Resource):
        @api.doc(description='获取用户列表')
        def get(self):
            '''获取用户列表'''
            return {'message': '获取用户列表接口'}
    
    @users_ns.route('/<int:user_id>')
    class User(Resource):
        @api.doc(description='获取单个用户信息')
        def get(self, user_id):
            '''获取单个用户信息'''
            return {'message': '获取单个用户信息接口'}
        
        @api.doc(description='更新用户信息')
        @api.expect(api.model('UpdateUser', {
            'email': fields.String(description='邮箱'),
            'avatar_url': fields.String(description='头像URL')
        }))
        def put(self, user_id):
            '''更新用户信息'''
            return {'message': '更新用户信息接口'}
        
        @api.doc(description='删除用户')
        def delete(self, user_id):
            '''删除用户'''
            return {'message': '删除用户接口'}
    
    # 节点管理接口文档
    @nodes_ns.route('')
    class Nodes(Resource):
        @api.doc(description='获取节点列表')
        def get(self):
            '''获取节点列表'''
            return {'message': '获取节点列表接口'}
        
        @api.doc(description='创建新节点')
        @api.expect(api.model('CreateNode', {
            'name': fields.String(required=True, description='节点名称'),
            'ip_address': fields.String(required=True, description='IP地址'),
            'login_credential_id': fields.Integer(required=True, description='登录凭证ID'),
            'os_type': fields.String(description='操作系统类型'),
            'os_version': fields.String(description='操作系统版本'),
            'cpu_info': fields.String(description='CPU信息'),
            'memory_total': fields.Integer(description='总内存(MB)'),
            'disk_total': fields.Integer(description='总磁盘(GB)')
        }))
        def post(self):
            '''创建新节点'''
            return {'message': '创建新节点接口'}
    
    @nodes_ns.route('/<int:node_id>')
    class NodeResource(Resource):
        @api.doc(description='获取单个节点信息')
        def get(self, node_id):
            '''获取单个节点信息'''
            return {'message': '获取单个节点信息接口'}
        
        @api.doc(description='更新节点信息')
        @api.expect(api.model('UpdateNode', {
            'name': fields.String(description='节点名称'),
            'status': fields.String(description='节点状态'),
            'os_type': fields.String(description='操作系统类型'),
            'os_version': fields.String(description='操作系统版本'),
            'cpu_info': fields.String(description='CPU信息'),
            'memory_total': fields.Integer(description='总内存(MB)'),
            'disk_total': fields.Integer(description='总磁盘(GB)')
        }))
        def put(self, node_id):
            '''更新节点信息'''
            return {'message': '更新节点信息接口'}
        
        @api.doc(description='删除节点')
        def delete(self, node_id):
            '''删除节点'''
            return {'message': '删除节点接口'}
    
    # 测试任务接口文档
    @tasks_ns.route('')
    class Tasks(Resource):
        @api.doc(description='获取任务列表')
        def get(self):
            '''获取任务列表'''
            return {'message': '获取任务列表接口'}
        
        @api.doc(description='创建新任务')
        @api.expect(api.model('CreateTask', {
            'name': fields.String(required=True, description='任务名称'),
            'description': fields.String(description='任务描述'),
            'node_id': fields.Integer(required=True, description='节点ID'),
            'io_case_id': fields.Integer(required=True, description='IO用例ID'),
            'task_space_id': fields.Integer(description='任务空间ID'),
            'priority': fields.String(description='优先级，默认为medium')
        }))
        def post(self):
            '''创建新任务'''
            return {'message': '创建新任务接口'}
    
    @tasks_ns.route('/<int:task_id>')
    class Task(Resource):
        @api.doc(description='获取单个任务信息')
        def get(self, task_id):
            '''获取单个任务信息'''
            return {'message': '获取单个任务信息接口'}
        
        @api.doc(description='更新任务信息')
        @api.expect(api.model('UpdateTask', {
            'name': fields.String(description='任务名称'),
            'description': fields.String(description='任务描述'),
            'status': fields.String(description='任务状态'),
            'priority': fields.String(description='优先级')
        }))
        def put(self, task_id):
            '''更新任务信息'''
            return {'message': '更新任务信息接口'}
        
        @api.doc(description='删除任务')
        def delete(self, task_id):
            '''删除任务'''
            return {'message': '删除任务接口'}
    
    # IO用例接口文档
    @io_cases_ns.route('')
    class IOCases(Resource):
        @api.doc(description='获取IO测试用例列表')
        def get(self):
            '''获取IO测试用例列表'''
            return {'message': '获取IO测试用例列表接口'}
        
        @api.doc(description='创建新IO测试用例')
        @api.expect(api.model('CreateIOCase', {
            'name': fields.String(required=True, description='用例名称'),
            'description': fields.String(description='用例描述'),
            'test_parameters': fields.Raw(required=True, description='测试参数')
        }))
        def post(self):
            '''创建新IO测试用例'''
            return {'message': '创建新IO测试用例接口'}
    
    @io_cases_ns.route('/<int:case_id>')
    class IOCase(Resource):
        @api.doc(description='获取单个IO测试用例信息')
        def get(self, case_id):
            '''获取单个IO测试用例信息'''
            return {'message': '获取单个IO测试用例信息接口'}
        
        @api.doc(description='更新IO测试用例信息')
        @api.expect(api.model('UpdateIOCase', {
            'name': fields.String(description='用例名称'),
            'description': fields.String(description='用例描述'),
            'test_parameters': fields.Raw(description='测试参数')
        }))
        def put(self, case_id):
            '''更新IO测试用例信息'''
            return {'message': '更新IO测试用例信息接口'}
        
        @api.doc(description='删除IO测试用例')
        def delete(self, case_id):
            '''删除IO测试用例'''
            return {'message': '删除IO测试用例接口'}
    
    @io_cases_ns.route('/templates')
    class IOCaseTemplates(Resource):
        @api.doc(description='获取测试用例模板列表')
        def get(self):
            '''获取测试用例模板列表'''
            return {'message': '获取测试用例模板列表接口'}
    
    # 测试结果接口文档
    @results_ns.route('')
    class Results(Resource):
        @api.doc(description='获取测试结果列表')
        def get(self):
            '''获取测试结果列表'''
            return {'message': '获取测试结果列表接口'}
    
    @results_ns.route('/<int:result_id>')
    class Result(Resource):
        @api.doc(description='获取单个测试结果信息')
        def get(self, result_id):
            '''获取单个测试结果信息'''
            return {'message': '获取单个测试结果信息接口'}
        
        @api.doc(description='删除测试结果')
        def delete(self, result_id):
            '''删除测试结果'''
            return {'message': '删除测试结果接口'}
    
    @results_ns.route('/aggregations')
    class Aggregations(Resource):
        @api.doc(description='获取测试结果聚合数据')
        def get(self):
            '''获取测试结果聚合数据'''
            return {'message': '获取测试结果聚合数据接口'}
    
    @results_ns.route('/aggregations/<int:agg_id>')
    class Aggregation(Resource):
        @api.doc(description='获取单个测试结果聚合信息')
        def get(self, agg_id):
            '''获取单个测试结果聚合信息'''
            return {'message': '获取单个测试结果聚合信息接口'}
    
    # 仪表盘接口文档
    @dashboard_ns.route('/stats')
    class DashboardStats(Resource):
        @api.doc(description='获取仪表盘统计数据')
        def get(self):
            '''获取仪表盘统计数据'''
            return {'message': '获取仪表盘统计数据接口'}
    
    @dashboard_ns.route('/recent-tasks')
    class RecentTasks(Resource):
        @api.doc(description='获取最近的任务列表')
        def get(self):
            '''获取最近的任务列表'''
            return {'message': '获取最近的任务列表接口'}
    
    @dashboard_ns.route('/recent-results')
    class RecentResults(Resource):
        @api.doc(description='获取最近的测试结果列表')
        def get(self):
            '''获取最近的测试结果列表'''
            return {'message': '获取最近的测试结果列表接口'}
    
    @dashboard_ns.route('/node-status')
    class NodeStatus(Resource):
        @api.doc(description='获取节点状态统计')
        def get(self):
            '''获取节点状态统计'''
            return {'message': '获取节点状态统计接口'}
    
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