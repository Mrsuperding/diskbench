# app包初始化文件
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

    # 彻底禁用所有SQLAlchemy相关日志（包括DEBUG级别的SQL语句打印）
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine.base.Engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool.impl.QueuePool').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.orm.attributes').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.orm.mapper').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.util').setLevel(logging.WARNING)

    # 禁用SQLAlchemy的echo和日志打印
    import sqlalchemy
    if hasattr(sqlalchemy, 'set_engine_options'):
        sqlalchemy.set_engine_options(None, echo=False, echo_pool=False)

    # 禁用loguru中与SQLAlchemy相关的日志
    try:
        from loguru import logger
        logger.disable('sqlalchemy')
        logger.disable('sqlalchemy.engine')
    except ImportError:
        pass
    
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
