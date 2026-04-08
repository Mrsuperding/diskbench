import os
from datetime import datetime, timedelta
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

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
from app.views.environment_spaces import environment_spaces_bp
from app.views.monitoring_config import monitoring_config_bp
from app.views.node_operations import node_operations_bp

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
    app.register_blueprint(environment_spaces_bp, url_prefix='/api/environment-spaces')
    app.register_blueprint(monitoring_config_bp, url_prefix='/api/monitoring-config')
    app.register_blueprint(node_operations_bp, url_prefix='/api/node-operations')
    
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


# 配置 APScheduler 定时任务
scheduler = BackgroundScheduler()


def collect_all_metrics():
    """定时任务：采集所有环境空间内节点的指标"""
    import signal
    from app.models.environment_space import EnvironmentSpace
    from app.models.node import Node
    from app.services.metric_collector import MetricCollector
    from app.models.system_metric import SystemMetric

    # 超时控制：25秒后强制终止
    def timeout_handler(signum, frame):
        raise TimeoutError("采集任务超时（超过25秒）")

    # 设置超时信号
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(25)  # 25秒超时

    with app.app_context():
        try:
            # 获取所有激活的环境空间
            spaces = EnvironmentSpace.get_all_active()
            app.logger.info(f'开始采集 {len(spaces)} 个环境空间的监控指标')

            total_nodes = 0
            success_count = 0
            failed_count = 0

            for space in spaces:
                # 采集该环境空间内的所有节点
                nodes = space.nodes
                total_nodes += len(nodes)

                for node in nodes:
                    try:
                        metrics = MetricCollector.collect_node_metrics(node.id)

                        # 使用封装的批量插入方法
                        inserted = SystemMetric.bulk_insert_system_metrics(node.id, metrics)

                        # 更新节点状态
                        node_status = 'active' if metrics.get('is_connected') else 'inactive'
                        node.status = node_status

                        success_count += 1
                    except TimeoutError:
                        app.logger.error(f'采集任务超时，停止执行')
                        db.session.rollback()
                        return
                    except Exception as e:
                        app.logger.error(f'采集节点 {node.id} ({node.name}) 指标失败: {e}')
                        failed_count += 1

            # 统一提交
            db.session.commit()

            app.logger.info(f'指标采集完成: {len(spaces)} 个环境空间, {total_nodes} 个节点, 成功 {success_count}, 失败 {failed_count}')

        except TimeoutError:
            app.logger.error('采集任务执行超时')
            db.session.rollback()
        except Exception as e:
            app.logger.error(f'采集任务执行失败: {e}')
            db.session.rollback()
        finally:
            signal.alarm(0)  # 取消超时信号


def cleanup_old_metrics():
    """定时任务：清理一周以前的监控数据"""
    from app.models.system_metric import SystemMetric

    with app.app_context():
        try:
            # 计算一周前的时间
            one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

            # 删除一周前的数据
            deleted = SystemMetric.query.filter(
                SystemMetric.collection_time < one_week_ago
            ).delete(synchronize_session=False)

            db.session.commit()
            app.logger.info(f'清理完成: 删除了 {deleted} 条过期监控数据（早于 {one_week_ago}）')
        except Exception as e:
            app.logger.error(f'清理监控数据失败: {e}')
            db.session.rollback()



# 添加任务 - 每30秒执行一次采集
scheduler.add_job(
    func=collect_all_metrics,
    trigger='interval',
    seconds=30,
    id='collect_metrics',
    replace_existing=True
)

# 添加任务 - 每天凌晨3点清理过期数据
scheduler.add_job(
    func=cleanup_old_metrics,
    trigger='cron',
    hour=3,
    minute=0,
    id='cleanup_metrics',
    replace_existing=True
)

# 启动调度器
scheduler.start()

# 优雅关闭
atexit.register(lambda: scheduler.shutdown())

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
        
        # 检查测试任务的FIO日志记录
        if len(sys.argv) > 2 and sys.argv[1] == '--check-logs-for-task':
            from app.models import TestLog
            import os
            
            # 获取任务ID
            task_id = int(sys.argv[2])
            
            # 查询任务的所有FIO日志记录
            logs = TestLog.query.filter_by(test_task_id=task_id, log_type='fio').all()
            print('Found', len(logs), 'FIO logs for task', task_id)
            
            for log in logs:
                print('\nLog ID:', log.id)
                print('Node ID:', log.node_id)
                print('Log path:', log.log_path)
                print('Log filename:', log.log_filename)
                print('File exists:', os.path.exists(log.log_path))
                
                # 如果文件存在，检查文件大小
                if os.path.exists(log.log_path):
                    print('File size:', os.path.getsize(log.log_path), 'bytes')
                else:
                    print('File does not exist!')
            
            # 查询任务的所有日志记录（包括iostat）
            all_logs = TestLog.query.filter_by(test_task_id=task_id).all()
            print('\nAll logs for task', task_id, ':', len(all_logs))
            for log in all_logs:
                print(f'ID: {log.id}, Type: {log.log_type}, Node: {log.node_id}, File: {log.log_filename}')
            
            sys.exit(0)
        
        # 检查测试任务32的FIO日志记录
        if len(sys.argv) > 1 and sys.argv[1] == '--check-logs':
            from app.models import TestLog
            import os
            
            # 查询任务32的所有FIO日志记录
            logs = TestLog.query.filter_by(test_task_id=32, log_type='fio').all()
            print('Found', len(logs), 'FIO logs for task 32')
            
            for log in logs:
                print('\nLog ID:', log.id)
                print('Node ID:', log.node_id)
                print('Log path:', log.log_path)
                print('Log filename:', log.log_filename)
                print('File exists:', os.path.exists(log.log_path))
                
                # 如果文件存在，检查文件大小和完整内容
                if os.path.exists(log.log_path):
                    print('File size:', os.path.getsize(log.log_path), 'bytes')
                    try:
                        with open(log.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            print('File content:')
                            print(content)
                    except Exception as e:
                        print('Error reading file:', e)
            
            sys.exit(0)
    
    # 检查端口是否可用
    import socket
    def check_port(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return True
            except socket.error:
                return False
    
    # 检查 5003 端口是否可用
    if not check_port(5003):
        print("错误: 端口 5003 已被占用，无法启动应用")
        sys.exit(1)
    
    # 使用 SocketIO 运行应用
    socketio.run(app, debug=True, host='0.0.0.0', port=5003, use_reloader=False)