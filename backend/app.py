import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_socketio import SocketIO

from config import config
from app.models import db
from app.utils.log_collector import log_collector

# 导入所有视图蓝图
from app.views.auth import auth_bp
from app.views.users import users_bp
from app.views.nodes import nodes_bp
from app.views.tasks import tasks_bp
from app.views.io_cases import io_cases_bp
from app.views.results import results_bp
from app.views.task_spaces import task_spaces_bp
from app.views.dashboard import dashboard_bp
from app.views.login_credentials import login_credentials_bp
from app.views.logs import logs_bp

from app.utils.error_handlers import register_error_handlers
from app.utils.jwt_callbacks import register_jwt_callbacks
from app.utils.api_docs import init_api

def create_app(config_name=None):
    """应用工厂函数"""
    
    # 获取配置名称
    if not config_name:
        config_name = os.environ.get('FLASK_CONFIG') or 'default'
    
    # 创建Flask应用
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 配置日志
    import logging
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL']),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
    app.logger.info('IO Platform startup')
    
    # 初始化扩展
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    
    # 配置CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(nodes_bp, url_prefix='/api/nodes')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(io_cases_bp, url_prefix='/api/io-cases')
    app.register_blueprint(results_bp, url_prefix='/api/results')
    app.register_blueprint(task_spaces_bp, url_prefix='/api/task-spaces')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(login_credentials_bp, url_prefix='/api/login-credentials')
    app.register_blueprint(logs_bp, url_prefix='/api/logs')
    
    # 注册错误处理
    register_error_handlers(app)
    
    # 注册JWT回调
    register_jwt_callbacks(jwt)
    
    # 初始化API文档
    init_api(app)
    
    # 初始化日志收集器
    log_collector.init_app(app)
    
    # 健康检查端点
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'app': app.config.get('APP_NAME', 'IO Platform'),
            'version': app.config.get('APP_VERSION', '1.0.0')
        })
    
    # API根端点
    @app.route('/api')
    def api_root():
        return jsonify({
            'message': 'IO Performance Testing Platform API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'users': '/api/users',
                'tasks': '/api/tasks',
                'nodes': '/api/nodes',
                'io_cases': '/api/io-cases',
                'results': '/api/results',
                'dashboard': '/api/dashboard'
            }
        })
    
    return app

# 创建应用实例
app = create_app()

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# 导入SocketIO事件处理
from app.views.socket_events import register_socket_events
register_socket_events(socketio)

if __name__ == '__main__':
    import sys
    
    with app.app_context():
        db.create_all()
        
        # 检查是否需要创建管理员用户
        if len(sys.argv) > 1 and sys.argv[1] == '--create-admin':
            from app.models import User
            
            # 检查是否已存在管理员用户
            admin = User.query.filter_by(username='admin').first()
            
            if not admin:
                # 创建管理员用户
                admin = User(username='admin', email='admin@example.com', role='admin')
                admin.set_password('adminpassword')
                
                db.session.add(admin)
                db.session.commit()
                
                print('管理员用户创建成功！')
                print(f'用户名: admin')
                print(f'邮箱: admin@example.com')
                print(f'密码: adminpassword')
            else:
                print('管理员用户已存在！')
                print(f'用户名: {admin.username}')
                print(f'邮箱: {admin.email}')
            
            sys.exit(0)
    
    # 使用SocketIO运行应用
    socketio.run(app, debug=True, host='0.0.0.0', port=5001, use_reloader=False)