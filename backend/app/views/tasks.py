from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import threading
import logging
import os

# 导入WebSocket日志发送功能
from app.views.socket_events import send_task_log

from app.models import db, TestTask, TaskExecution, TestResult, IOTestCase, Node
from sqlalchemy import text
from app.utils.responses import success_response, error_response
from app.utils.ssh_client import SSHClient
from app.utils.log_collector import log_collector

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('', methods=['GET'])
@jwt_required()
def get_tasks():
    """获取任务列表"""
    try:
        args = request.args
        task_space_id = args.get('task_space_id', type=int)
        
        query = TestTask.query
        
        if task_space_id:
            query = query.filter(TestTask.task_space_id == task_space_id)
        
        tasks = query.all()
        return success_response([task.to_dict() for task in tasks])
    except Exception as e:
        return error_response(f'获取任务列表失败: {str(e)}', 500)

@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """获取单个任务信息"""
    try:
        task = TestTask.query.get(task_id)
        if not task:
            return error_response('任务不存在', 404)
        return success_response(task.to_dict())
    except Exception as e:
        return error_response(f'获取任务信息失败: {str(e)}', 500)

@tasks_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    """创建新任务"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['name', 'io_test_case_ids']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'{field} 是必需的', 400)
        
        # node_ids 允许为空列表，但必须存在于请求中
        if 'node_ids' not in data:
            return error_response('node_ids 是必需的', 400)
        
        # 检查节点是否存在
        from app.models import Node
        node_ids = data['node_ids']
        if not isinstance(node_ids, list):
            return error_response('节点ID必须是数组格式', 400)
        
        nodes = []
        if len(node_ids) > 0:
            nodes = Node.query.filter(Node.id.in_(node_ids)).all()
            if len(nodes) != len(node_ids):
                return error_response('部分节点不存在', 404)
        
        # 检查IO测试用例是否存在
        from app.models import IOTestCase
        io_test_cases = IOTestCase.query.filter(IOTestCase.id.in_(data['io_test_case_ids'])).all()
        if len(io_test_cases) != len(data['io_test_case_ids']):
            return error_response('部分IO测试用例不存在', 404)
        
        # 处理 task_space_id
        task_space_id = data.get('task_space_id')
        if task_space_id == '':
            task_space_id = None
        else:
            # 检查任务空间是否存在
            if task_space_id:
                from app.models import TaskSpace
                task_space = TaskSpace.query.get(task_space_id)
                if not task_space:
                    return error_response('任务空间不存在', 404)
        
        task = TestTask(
            name=data['name'],
            description=data.get('description'),
            task_space_id=task_space_id,
            priority=data.get('priority', 'medium'),
            created_by=current_user_id
        )
        
        # 添加关联的节点
        task.nodes = nodes
        
        # 先添加任务到数据库
        db.session.add(task)
        db.session.flush()  # 获取task.id
        
        # 直接操作关联表添加关联
        for io_test_case in io_test_cases:
            db.session.execute(text('INSERT INTO task_case_association (test_task_id, io_test_case_id) VALUES (:task_id, :case_id)'), 
                             {'task_id': task.id, 'case_id': io_test_case.id})
        
        db.session.commit()
        
        return success_response(task.to_dict(), '任务创建成功', 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新任务失败: {str(e)}', 500)
        return error_response(f'创建任务失败: {str(e)}', 500)

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """更新任务信息"""
    try:
        task = TestTask.query.get(task_id)
        if not task:
            return error_response('任务不存在', 404)
        
        data = request.get_json()
        if 'name' in data:
            task.name = data['name']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = data['status']
        if 'priority' in data:
            task.priority = data['priority']
        if 'scheduled_at' in data:
            from datetime import datetime
            if data['scheduled_at']:
                # 处理两种时间格式：ISO格式(2025-12-06T19:03:10)和普通格式(2025-12-06 19:03:10)
                try:
                    task.scheduled_at = datetime.strptime(data['scheduled_at'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # 尝试ISO格式
                    task.scheduled_at = datetime.fromisoformat(data['scheduled_at'])
            else:
                task.scheduled_at = None
        
        # 检查节点是否存在
        if 'node_ids' in data:
            from app.models import Node
            node_ids = data['node_ids']
            if not isinstance(node_ids, list):
                return error_response('节点ID必须是数组格式', 400)
            
            nodes = []
            if len(node_ids) > 0:
                nodes = Node.query.filter(Node.id.in_(node_ids)).all()
                if len(nodes) != len(node_ids):
                    return error_response('部分节点不存在', 404)
            
            # 更新关联的节点
            task.nodes = nodes
        
        # 检查IO测试用例是否存在并更新关联
        if 'io_test_case_ids' in data:
            from app.models import IOTestCase
            io_test_case_ids = data['io_test_case_ids']
            if not isinstance(io_test_case_ids, list):
                return error_response('测试用例ID必须是数组格式', 400)
            
            io_test_cases = IOTestCase.query.filter(IOTestCase.id.in_(io_test_case_ids)).all()
            if len(io_test_cases) != len(io_test_case_ids):
                return error_response('部分IO测试用例不存在', 404)
            # 直接操作关联表来更新关联关系
            # 清空现有关联
            db.session.execute(text('DELETE FROM task_case_association WHERE test_task_id = :task_id'), {'task_id': task.id})
            # 添加新关联
            for io_test_case in io_test_cases:
                db.session.execute(text('INSERT INTO task_case_association (test_task_id, io_test_case_id) VALUES (:task_id, :case_id)'), 
                                 {'task_id': task.id, 'case_id': io_test_case.id})
            db.session.flush()
        
        # 检查任务空间是否存在
        if 'task_space_id' in data:
            if data['task_space_id']:
                from app.models import TaskSpace
                task_space = TaskSpace.query.get(data['task_space_id'])
                if not task_space:
                    return error_response('任务空间不存在', 404)
                task.task_space_id = data['task_space_id']
            else:
                task.task_space_id = None
        
        db.session.commit()
        return success_response(task.to_dict(), '任务信息更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新任务信息失败: {str(e)}', 500)

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """删除任务"""
    try:
        task = TestTask.query.get(task_id)
        if not task:
            return error_response('任务不存在', 404)
        
        # 1. 删除关联的测试结果
        logging.info(f"删除任务关联的测试结果: task_id={task_id}")
        TestResult.query.filter_by(test_task_id=task_id).delete()
        
        # 2. 删除关联的测试日志
        logging.info(f"删除任务关联的测试日志: task_id={task_id}")
        from app.models import TestLog
        TestLog.query.filter_by(test_task_id=task_id).delete()
        
        # 3. 删除关联的任务执行记录
        logging.info(f"删除任务关联的执行记录: task_id={task_id}")
        TaskExecution.query.filter_by(test_task_id=task_id).delete()
        
        # 4. 删除任务与节点的关联
        logging.info(f"删除任务与节点的关联: task_id={task_id}")
        from sqlalchemy import text
        db.session.execute(
            text('DELETE FROM task_node_association WHERE test_task_id = :task_id'),
            {'task_id': task_id}
        )
        
        # 5. 删除任务与IO测试用例的关联
        logging.info(f"删除任务与IO测试用例的关联: task_id={task_id}")
        db.session.execute(
            text('DELETE FROM task_case_association WHERE test_task_id = :task_id'),
            {'task_id': task_id}
        )
        
        # 6. 删除任务本身
        logging.info(f"删除任务: task_id={task_id}")
        db.session.delete(task)
        db.session.commit()
        return success_response(None, '任务删除成功')
    except Exception as e:
        logging.error(f"删除任务失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return error_response(f'删除任务失败: {str(e)}', 500)

@tasks_bp.route('/<int:task_id>/clone', methods=['POST'])
@jwt_required()
def clone_task(task_id):
    """克隆任务"""
    try:
        current_user_id = get_jwt_identity()
        
        # 获取原任务
        original_task = TestTask.query.get(task_id)
        if not original_task:
            return error_response('任务不存在', 404)
        
        # 创建新任务
        new_task_name = f"{original_task.name} (克隆)"
        new_task = TestTask(
            name=new_task_name,
            description=original_task.description,
            task_space_id=original_task.task_space_id,
            status='pending',  # 新克隆的任务状态为待执行
            priority=original_task.priority,
            created_by=current_user_id
        )
        
        # 复制节点信息
        new_task.nodes = original_task.nodes
        
        # 添加任务到数据库
        db.session.add(new_task)
        db.session.flush()  # 获取新任务的ID
        
        # 复制IO用例信息
        # 获取原任务的所有IO用例
        io_test_cases = IOTestCase.query.join(
            TestTask.io_test_cases
        ).filter(TestTask.id == task_id).all()
        
        # 添加IO用例关联
        for io_test_case in io_test_cases:
            db.session.execute(text('INSERT INTO task_case_association (test_task_id, io_test_case_id) VALUES (:task_id, :case_id)'), 
                             {'task_id': new_task.id, 'case_id': io_test_case.id})
        
        db.session.commit()
        
        return success_response(new_task.to_dict(), '任务克隆成功', 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'克隆任务失败: {str(e)}', 500)

@tasks_bp.route('/<int:task_id>/execute', methods=['POST'])
@jwt_required()
def execute_task(task_id):
    """执行任务"""
    try:
        task = TestTask.query.get(task_id)
        if not task:
            return error_response('任务不存在', 404)
        
        # 检查任务状态
        if task.status == 'completed':
            return error_response('已完成状态的任务不能被执行', 400)
        
        # 创建任务执行记录
        task_execution = TaskExecution(
            test_task_id=task_id,
            status='running',
            start_time=datetime.utcnow()
        )
        db.session.add(task_execution)
        
        # 更新任务状态
        task.status = 'running'
        task.started_at = datetime.utcnow()
        
        db.session.commit()
        
        # 从flask获取当前app实例，避免循环导入
        from flask import current_app
        # 获取真实的app实例，而不是代理对象
        real_app = current_app._get_current_object()
        
        # 启动异步线程执行任务
        threading.Thread(target=run_task_execution, args=(task_id, task_execution.id, real_app)).start()
        
        return success_response(task.to_dict(), '任务开始执行')
    except Exception as e:
        db.session.rollback()
        return error_response(f'执行任务失败: {str(e)}', 500)

@tasks_bp.route('/<int:task_id>/pause', methods=['POST'])
@jwt_required()
def pause_task(task_id):
    """暂停任务"""
    try:
        task = TestTask.query.get(task_id)
        if not task:
            return error_response('任务不存在', 404)
    
        # 检查任务状态
        if task.status != 'running':
            return error_response('只有运行中的任务才能被暂停', 400)
    
        # 更新任务状态
        task.status = 'cancelled'
    
        # 更新所有运行中的任务执行记录
        task_executions = TaskExecution.query.filter_by(
            test_task_id=task_id,
            status='running'
        ).all()
    
        for execution in task_executions:
            execution.status = 'cancelled'
            execution.end_time = datetime.utcnow()
    
        # 停止节点上的fio命令并清理文件
        from app.utils.ssh_client import SSHClient
        # 获取任务关联的所有节点
        nodes = task.nodes
        for node in nodes:
            logging.info(f"停止节点 {node.ip_address} 上的fio命令并清理文件")
            # 获取节点关联的登录凭证
            login_credential = node.login_credential
            if not login_credential:
                logging.error(f'节点 {node.name} 没有关联登录凭证，跳过清理')
                continue
            
            try:
                # 使用节点的actual IP进行SSH连接
                connect_host = node.ip_address
                ssh_client = SSHClient(login_credential, hostname=connect_host)
                if not ssh_client.connect():
                    logging.error(f'无法连接到节点: {connect_host}，跳过清理')
                    continue
            
                # 1. 停止所有fio进程
                logging.info(f"停止节点 {node.ip_address} 上的所有fio进程")
                # 使用更强大的命令杀死所有fio进程
                ssh_client.execute_command('pkill -f "fio"')
                ssh_client.execute_command('pkill -f "fio --name=diskbench_test"')
                ssh_client.execute_command('pkill -f "iostat -xdm 1"')
                # 强制杀死可能残留的fio进程
                ssh_client.execute_command('pkill -9 -f "fio"')
            
                # 2. 删除上传的fio文件和目录
                target_dir = login_credential.platform_partition
                fio_dir_name = 'fio-fio-3.36'
                remote_fio_src = f'{target_dir}/{fio_dir_name}'
                
                logging.info(f"删除节点 {node.ip_address} 上的fio目录: {remote_fio_src}")
                ssh_client.execute_command(f'rm -rf {remote_fio_src}')
            
                # 3. 删除临时文件
                logging.info(f"删除节点 {node.ip_address} 上的临时文件")
                ssh_client.execute_command('rm -f /tmp/io_test_logs_* /tmp/iostat_* /tmp/iostat_pid.txt')
            
                # 断开SSH连接
                ssh_client.disconnect()
                logging.info(f"节点 {node.ip_address} 清理完成")
            except Exception as e:
                logging.error(f"清理节点 {node.ip_address} 失败: {str(e)}")
    
        db.session.commit()
    
        return success_response(task.to_dict(), '任务已暂停')
    except Exception as e:
        db.session.rollback()
        return error_response(f'暂停任务失败: {str(e)}', 500)

@tasks_bp.route('/<int:task_id>/results', methods=['GET'])
@jwt_required()
def get_task_results(task_id):
    """获取任务的测试结果"""
    try:
        logging.info(f'进入get_task_results函数，task_id={task_id}')
        # 获取任务
        task = TestTask.query.get(task_id)
        logging.info(f'获取到的任务: {task}')
        
        # 如果没有找到任务，仍然返回200状态码和空结果列表
        if not task:
            logging.info(f'任务 {task_id} 不存在，返回空结果列表')
            return success_response([], '获取任务结果成功')
        
        # 获取任务的所有测试结果
        results = TestResult.query.filter_by(test_task_id=task_id).all()
        
        # 格式化返回结果
        result_list = []
        for result in results:
            result_list.append({
                'id': result.id,
                'task_id': result.test_task_id,
                'io_test_case_id': result.io_test_case_id,
                'node_id': result.node_id,
                'status': result.status,
                'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'raw_result': result.raw_output,
                'parsed_result': result.parsed_results
            })
        
        return success_response(result_list, '获取任务结果成功')
    except Exception as e:
        logging.error(f"获取任务结果失败: {str(e)}")
        return error_response(f'获取任务结果失败: {str(e)}', 500)

@tasks_bp.route('/<int:task_id>/logs', methods=['GET'])
@jwt_required()
def get_task_logs(task_id):
    """获取任务的测试日志"""
    try:
        node_id = request.args.get('node_id')
        log_type = request.args.get('log_type')
        
        query = TestLog.query.filter_by(test_task_id=task_id)
        
        if node_id:
            query = query.filter_by(node_id=node_id)
        
        if log_type:
            query = query.filter_by(log_type=log_type)
        
        logs = query.order_by(TestLog.collection_time.desc()).all()
        
        return success_response(
            [log.to_dict() for log in logs],
            message="获取任务测试日志成功"
        )
    except Exception as e:
        return error_response(str(e), 500)

@tasks_bp.route('/<int:task_id>/logs/package', methods=['POST'])
@jwt_required()
def package_task_logs(task_id):
    """打包任务日志"""
    try:
        # 使用日志收集器打包任务日志
        package_path = log_collector.package_task_logs(task_id)
        if not package_path:
            return error_response('打包任务日志失败', 500)
        
        return success_response({'package_path': package_path}, '任务日志打包成功')
    except Exception as e:
        return error_response(f'打包任务日志失败: {str(e)}', 500)

@tasks_bp.route('/<int:task_id>/logs/download', methods=['GET'])
@jwt_required()
def download_task_logs(task_id):
    """下载任务日志压缩包"""
    try:
        from flask import send_file
        
        # 首先检查是否已经有打包文件
        # 从配置中获取本地数据存储目录
        local_data_dir = current_app.config.get('LOCAL_DATA_DIR', './local_data')
        package_filename = f'task_{task_id}_logs.tar.gz'
        package_path = os.path.join(local_data_dir, package_filename)
        
        # 如果打包文件不存在，先打包
        if not os.path.exists(package_path):
            package_path = log_collector.package_task_logs(task_id)
            if not package_path:
                return error_response('打包任务日志失败', 500)
        
        # 发送文件下载
        return send_file(
            package_path,
            as_attachment=True,
            download_name=os.path.basename(package_path)
        )
    except Exception as e:
        return error_response(f'下载任务日志失败: {str(e)}', 500)

def run_task_execution(task_id, execution_id, app):
    """执行任务的实际逻辑"""
    # 导入模型
    from app.models.test_task import TestTask, TaskExecution
    from app.models.io_test_case import IOTestCase
    from app.models.node import Node
    from app.models.test_result import TestResult
    
    task = None
    execution = None
    
    try:
        logging.info(f"-----------开始执行任务: task_id={task_id}, execution_id={execution_id}------------")
        
        # 创建应用上下文
        with app.app_context():
            logging.info(f"创建应用上下文，开始查询数据库")
            
            # 获取任务信息
            logging.info(f"查询任务信息: task_id={task_id}")
            task = TestTask.query.get(task_id)
            logging.info(f"查询执行记录: execution_id={execution_id}")
            execution = TaskExecution.query.get(execution_id)
            
            if not task:
                raise Exception(f'任务不存在: task_id={task_id}')
            if not execution:
                raise Exception(f'执行记录不存在: execution_id={execution_id}')
            
            logging.info(f"获取到任务信息: task_name={task.name}, status={task.status}")
            logging.info(f"获取到执行记录: execution_id={execution.id}, status={execution.status}")
            
            # 获取任务关联的节点
            logging.info(f"获取任务关联的节点: task_id={task_id}")
            nodes = task.nodes  # task.nodes已经是关系集合，不需要调用.all()
            logging.info(f"任务关联的节点数量: {len(nodes)}")
            for node in nodes:
                logging.info(f"节点信息: id={node.id}, name={node.name}, ip={node.ip_address}")
            
            # 使用SQL查询获取任务关联的IO测试用例
            logging.info(f"获取任务关联的IO测试用例: task_id={task_id}")
            from sqlalchemy import text
            case_ids = db.session.execute(
                text('SELECT io_test_case_id FROM task_case_association WHERE test_task_id = :task_id'),
                {'task_id': task_id}
            ).fetchall()
            io_test_case_ids = [case_id[0] for case_id in case_ids]
            logging.info(f"任务关联的IO测试用例ID列表: {io_test_case_ids}")
            io_test_cases = IOTestCase.query.filter(IOTestCase.id.in_(io_test_case_ids)).all()
            logging.info(f"任务关联的IO测试用例数量: {len(io_test_cases)}")
            for io_test_case in io_test_cases:
                logging.info(f"IO测试用例信息: id={io_test_case.id}, name={io_test_case.name}, tool={io_test_case.tool}")
            
            if not nodes:
                raise Exception(f'任务没有关联任何节点: task_id={task_id}')
            
            if not io_test_cases:
                raise Exception(f'任务没有关联任何IO测试用例: task_id={task_id}')
            
            # 为每个节点执行任务
            logging.info(f"开始为每个节点执行任务，节点数量: {len(nodes)}")
            task_failed = False  # 任务失败标志
            for node in nodes:
                logging.info(f"开始执行节点任务: node_id={node.id}, node_name={node.name}, ip={node.ip_address}")
                
                # 获取节点关联的登录凭证
                logging.info(f"获取节点关联的登录凭证: node_id={node.id}")
                login_credential = node.login_credential
                if not login_credential:
                    logging.error(f'节点 {node.name} 没有关联登录凭证')
                    task_failed = True
                    send_task_log(task_id, f"节点 {node.ip_address} 执行失败: 没有关联登录凭证")
                    continue
                
                logging.info(f"获取到登录凭证: id={login_credential.id}, alias={login_credential.alias}, host={login_credential.host}, port={login_credential.port}")
                
                # 使用节点的actual IP进行SSH连接
                connect_host = node.ip_address
                logging.info(f"创建SSH连接: host={connect_host}, port={login_credential.port}")
                ssh_client = SSHClient(login_credential, hostname=connect_host)
                
                try:
                    # 连接到节点
                    logging.info(f"连接到节点: {connect_host}")
                    if not ssh_client.connect():
                        raise Exception(f'无法连接到节点: {connect_host}')
                    logging.info(f"成功连接到节点: {connect_host}")
                    
                    # 1. 检测节点架构
                    logging.info(f"检测节点架构: {connect_host}")
                    send_task_log(task_id, f"节点 {node.ip_address} 正在检测架构...")
                    architecture = detect_node_architecture(ssh_client)
                    logging.info(f"节点 {connect_host} 架构: {architecture}")
                    send_task_log(task_id, f"节点 {node.ip_address} 架构检测完成: {architecture}")
                    
                    # 第一阶段：打印当前任务的节点和下IO的分区
                    logging.info(f"===== 第一阶段：任务节点和IO分区信息 =====")
                    logging.info(f"当前任务节点: {node.name} ({node.ip_address})")
                    
                    # 显示所有IO分区
                    if node.io_partitions and len(node.io_partitions) > 0:
                        logging.info(f"节点 {node.ip_address} 的IO分区列表:")
                        for i, partition in enumerate(node.io_partitions):
                            if isinstance(partition, dict) and 'path' in partition:
                                logging.info(f"  分区 {i+1}: {partition['path']}")
                            else:
                                logging.info(f"  分区 {i+1}: {partition}")
                        send_task_log(task_id, f"节点 {node.ip_address} 的IO分区: {', '.join([p['path'] if isinstance(p, dict) else p for p in node.io_partitions])}")
                    else:
                        logging.info(f"节点 {node.ip_address} 未配置IO分区")
                        send_task_log(task_id, f"节点 {node.ip_address} 未配置IO分区")
                    
                    # 第二阶段：上传工具阶段
                    logging.info(f"===== 第二阶段：上传工具阶段 =====")
                    logging.info(f"开始上传fio文件到节点: {login_credential.host}")
                    send_task_log(task_id, f"节点 {node.ip_address} 正在上传fio工具...")
                    
                    # 显示上传进度
                    logging.info(f"上传进度: 0%")
                    logging.info(f"上传进度: 50%")
                    upload_fio_files(ssh_client, architecture, login_credential)
                    logging.info(f"上传进度: 100%")
                    
                    logging.info(f"成功上传fio文件到节点: {login_credential.host}")
                    send_task_log(task_id, f"节点 {node.ip_address} fio工具上传完成")
                    
                    # 3. 执行每个IO测试用例
                    logging.info(f"开始执行IO测试用例，数量: {len(io_test_cases)}")
                    for io_test_case in io_test_cases:
                        # 第三阶段：上传工具后日志打印出当前下的IO是什么IO模型
                        logging.info(f"===== 第三阶段：IO模型执行阶段 =====")
                        logging.info(f"当前执行的IO模型: {io_test_case.name}")
                        logging.info(f"IO模型ID: {io_test_case.id}")
                        logging.info(f"IO模型工具: {io_test_case.tool}")
                        
                        send_task_log(task_id, f"节点 {node.ip_address} 开始执行IO模型: {io_test_case.name}")
                        
                        # 执行IO测试
                        logging.info(f"运行IO测试: {io_test_case.name}")
                        
                        # 执行fio命令，使用非阻塞方式，定期检查任务状态
                        import time
                        
                        # 构建fio命令
                        fio_params = io_test_case.parameters
                        
                        # 添加IO分区到测试参数
                        if node.io_partitions and len(node.io_partitions) > 0:
                            # 获取第一个分区作为测试设备
                            partition = node.io_partitions[0]
                            if isinstance(partition, dict) and 'path' in partition:
                                fio_params['filename'] = partition['path']
                            else:
                                # 兼容旧格式，直接使用分区路径
                                fio_params['filename'] = partition
                            logging.info(f"添加IO分区到测试参数: {fio_params['filename']}")
                        elif 'partitions' in fio_params and fio_params['partitions']:
                            # 从测试用例参数中获取分区信息
                            fio_params['filename'] = fio_params['partitions']
                            logging.info(f"从测试用例参数中获取分区信息: {fio_params['filename']}")
                        
                        # 收集IO性能抖动数据
                        send_task_log(task_id, f"节点 {node.ip_address} 正在收集IO性能抖动数据...")
                        logging.info(f"收集IO性能抖动数据: {login_credential.host}")
                        
                        # 启动iostat收集后台数据
                        iostat_log = f'/tmp/iostat_{task_id}_{execution_id}_{node.id}_{io_test_case.id}.log'
                        ssh_client.execute_command(f"sh -c 'iostat -xdm 1 > {iostat_log} 2>&1 & echo $! > /tmp/iostat_pid.txt'")
                        
                        # 执行IO测试
                        result = ssh_client.run_fio_test(fio_params)
                        logging.info(f"IO测试结果: success={result['success']}")
                        
                        # 检查任务状态，看是否被取消
                        task = TestTask.query.get(task_id)
                        if task.status == 'cancelled':
                            logging.info(f"任务已被取消，停止执行: task_id={task_id}")
                            send_task_log(task_id, f"节点 {node.ip_address} 任务已被取消，停止执行")
                            task_failed = True
                            # 停止iostat收集
                            ssh_client.execute_command(f'pkill -f "iostat -xdm 1"')
                            continue
                        
                        # 停止iostat收集
                        ssh_client.execute_command(f'pkill -f "iostat -xdm 1"')
                        
                        if result['success']:
                            # 4. 保存测试结果
                            logging.info(f"保存测试结果: task_id={task_id}, node_id={node.id}, case_id={io_test_case.id}")
                            test_result = TestResult(
                                test_task_id=task_id,
                                node_id=node.id,
                                io_test_case_id=io_test_case.id,
                                task_execution_id=execution_id,
                                raw_output=result['raw_output'],
                                parsed_results=result['parsed_output'],
                                status='success',
                                created_at=datetime.utcnow()
                            )
                            
                            db.session.add(test_result)
                            db.session.commit()
                            logging.info(f"测试结果保存成功: result_id={test_result.id}")
                            
                            # 5. 收集性能数据
                            logging.info(f"收集性能数据: task_id={task_id}, node_id={node.id}, case_id={io_test_case.id}")
                            # 收集CPU、内存、磁盘等性能指标
                            performance_data = {}
                            
                            # 收集CPU使用率
                            cpu_cmd = 'top -bn1 | grep "%Cpu(s)" | awk "{print $2 + $4}"'
                            success, cpu_output = ssh_client.execute_command(cpu_cmd)
                            if success:
                                performance_data['cpu_usage'] = cpu_output
                            
                            # 收集内存使用情况
                            mem_cmd = 'free -m | grep Mem | awk "{print $3/$2 * 100.0}"'
                            success, mem_output = ssh_client.execute_command(mem_cmd)
                            if success:
                                performance_data['mem_usage'] = mem_output
                            
                            # 收集磁盘空间信息
                            disk_cmd = 'df -h / | tail -1'
                            success, disk_output = ssh_client.execute_command(disk_cmd)
                            if success:
                                performance_data['disk_info'] = disk_output
                            
                            # 收集iostat数据
                            success, iostat_data = ssh_client.execute_command(f'cat {iostat_log}')
                            if success:
                                performance_data['iostat_output'] = iostat_data
                            
                            logging.info(f"性能数据收集成功: {performance_data}")
                            
                            # 6. 收集运行日志
                            logging.info(f"收集运行日志: task_id={task_id}, node_id={node.id}, case_id={io_test_case.id}")
                            # 收集系统日志和fio日志
                            log_file = f'/tmp/io_test_logs_{task_id}_{execution_id}_{node.id}_{io_test_case.id}.log'
                            
                            # 创建日志文件
                            ssh_client.execute_command(f'touch {log_file}')
                            
                            # 收集dmesg日志
                            ssh_client.execute_command(f'dmesg -T | tail -200 >> {log_file}')
                            
                            # 收集系统日志
                            ssh_client.execute_command(f'journalctl -n 200 >> {log_file}')
                            
                            # 收集fio测试输出
                            ssh_client.execute_command(f'echo "===== FIO TEST OUTPUT =====" >> {log_file}')
                            # 使用cat和heredoc写入fio结果，避免特殊字符问题
                            fio_result_file = f'/tmp/fio_result_{task_id}_{node.id}_{io_test_case.id}.txt'
                            ssh_client.execute_command(f'''cat > {fio_result_file} << "EOF"
{result["raw_output"]}
EOF''')
                            ssh_client.execute_command(f'cat {fio_result_file} >> {log_file}')
                            
                            # 收集iostat输出
                            ssh_client.execute_command(f'echo "===== IOSTAT OUTPUT =====" >> {log_file}')
                            ssh_client.execute_command(f'cat {iostat_log} >> {log_file}')
                            
                            # 7. 下载日志到本地
                            # 使用动态计算的项目根路径
                            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
                            util_dir = os.path.join(project_root, 'util')
                            
                            # 创建日志目录（如果不存在）
                            os.makedirs(util_dir, exist_ok=True)
                            
                            # 下载组合日志文件
                            local_log_path = os.path.join(util_dir, f'io_test_logs_{task_id}_{execution_id}_{node.id}_{io_test_case.id}_{datetime.now().strftime("%Y%m%d%H%M%S")}.log')
                            success, message = ssh_client.download_file(log_file, local_log_path)
                            if success:
                                logging.info(f"运行日志收集成功，保存到本地: {local_log_path}")
                            else:
                                logging.error(f"运行日志下载失败: {message}")
                            
                            # 8. 使用日志收集器收集iostat日志
                            iostat_log_obj = log_collector.collect_iostat_log(ssh_client, task_id, execution_id, node.id, io_test_case.id, iostat_log)
                            if iostat_log_obj:
                                logging.info(f"iostat日志收集成功")
                            else:
                                logging.error(f"iostat日志收集失败")
                            
                            # 9. 使用日志收集器收集fio日志
                            # 构建fio日志路径
                            fio_log = f'/tmp/fio_{task_id}_{execution_id}_{node.id}_{io_test_case.id}.log'
                            # 将fio结果写入文件（使用echo可能会导致格式问题，改用cat命令）
                            command = f'''cat > {fio_log} << "EOF"
{result["raw_output"]}
EOF'''
                            ssh_client.execute_command(command)
                            fio_log_obj = log_collector.collect_fio_log(ssh_client, task_id, execution_id, node.id, io_test_case.id, fio_log)
                            if fio_log_obj:
                                logging.info(f"fio日志收集成功")
                            else:
                                logging.error(f"fio日志收集失败")
                            
                            # 10. 清理临时文件
                            ssh_client.execute_command(f'rm -f {log_file} {iostat_log} {fio_log} /tmp/iostat_pid.txt')
                            
                            # 9. 记录详细的连跑信息
                            detailed_info = f"IO模型 {io_test_case.name} 执行完成，详细信息：\n"
                            detailed_info += f"  节点IP: {node.ip_address}\n"
                            detailed_info += f"  任务ID: {task_id}\n"
                            detailed_info += f"  执行状态: 成功\n"
                            detailed_info += f"  IO类型: {fio_params.get('io_type', 'read')}\n"
                            detailed_info += f"  块大小: {fio_params.get('block_size', '4k')}\n"
                            detailed_info += f"  队列深度: {fio_params.get('queue_depth', '16')}\n"
                            detailed_info += f"  运行时间: {fio_params.get('runtime', '30')}秒\n"
                            detailed_info += f"  读写比例: {fio_params.get('read_write_ratio', '100:0')}\n"
                            detailed_info += f"  测试文件大小: {fio_params.get('size', '1G')}\n"
                            detailed_info += f"  执行时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                            
                            send_task_log(task_id, detailed_info)
                            logging.info(detailed_info)
                            
                            send_task_log(task_id, f"节点 {node.ip_address} 完成IO模型: {io_test_case.name}")
                            logging.info(f"节点 {node.ip_address} 完成IO模型: {io_test_case.name}")
                        else:
                            logging.error(f"IO测试失败: {io_test_case.name}, 错误: {result['raw_output']}")
                            send_task_log(task_id, f"节点 {node.ip_address} 执行IO模型 {io_test_case.name} 失败: {result['raw_output'][:100]}...")
                            
                            # 记录失败的详细信息
                            fail_info = f"IO模型 {io_test_case.name} 执行失败，详细信息：\n"
                            fail_info += f"  节点IP: {node.ip_address}\n"
                            fail_info += f"  任务ID: {task_id}\n"
                            fail_info += f"  执行状态: 失败\n"
                            fail_info += f"  错误信息: {result['raw_output'][:200]}...\n"
                            send_task_log(task_id, fail_info)
                            
                            # 清理临时文件
                            ssh_client.execute_command(f'rm -f {iostat_log} /tmp/iostat_pid.txt')
                            
                            task_failed = True
                            
                except Exception as e:
                    logging.error(f"执行节点 {node.ip_address} 任务失败: {str(e)}", exc_info=True)
                    send_task_log(task_id, f"节点 {node.ip_address} 执行失败: {str(e)}")
                    task_failed = True
                finally:
                    logging.info(f"断开SSH连接: {login_credential.host}")
                    ssh_client.disconnect()
            
            # 更新任务状态
            logging.info(f"更新任务状态: task_id={task_id}, task_failed={task_failed}")
            
            # 使用日志收集器打包任务日志
            if not task_failed:
                package_path = log_collector.package_task_logs(task_id)
                if package_path:
                    logging.info(f"任务日志打包成功: {package_path}")
            if task_failed:
                # 任务失败
                task.status = 'failed'
                execution.status = 'failed'
                execution.error_message = "任务执行过程中发生错误"
                execution.end_time = datetime.utcnow()
                send_task_log(task_id, "任务执行失败")
                logging.info(f"任务状态更新为失败: task_id={task_id}")
            else:
                # 任务成功
                task.status = 'completed'
                task.completed_at = datetime.utcnow()
                execution.status = 'completed'
                execution.end_time = datetime.utcnow()
                execution.duration = int((execution.end_time - execution.start_time).total_seconds())
                send_task_log(task_id, "任务执行完成")
                logging.info(f"任务状态更新为已完成: task_id={task_id}, duration={execution.duration}秒")
            
            db.session.commit()
            app.logger.info(f"任务状态更新成功: task_id={task_id}, status={task.status}")
            
            app.logger.info(f"任务执行完成: task_id={task_id}")
            
    except Exception as e:
        app.logger.error(f"执行任务 {task_id} 失败: {str(e)}", exc_info=True)
        
        # 更新任务状态为失败
        try:
            with app.app_context():
                app.logger.info(f"更新任务状态为失败: task_id={task_id}")
                # 重新获取任务和执行记录，确保在上下文中
                task = TestTask.query.get(task_id)
                execution = TaskExecution.query.get(execution_id)
                
                if task and execution:
                    task.status = 'failed'
                    execution.status = 'failed'
                    execution.error_message = str(e)
                    execution.end_time = datetime.utcnow()
                    
                    db.session.commit()
                    app.logger.info(f"任务状态更新为失败: task_id={task_id}, error={str(e)}")
                    
                    send_task_log(task_id, f"任务执行失败: {str(e)}")
                else:
                    app.logger.error(f"无法获取任务或执行记录，无法更新状态: task_id={task_id}, execution_id={execution_id}")
        except Exception as update_error:
            app.logger.error(f"更新任务状态失败: {str(update_error)}", exc_info=True)

def detect_node_architecture(ssh_client):
    """检测节点架构"""
    try:
        success, result = ssh_client.execute_command('uname -m')
        if not success:
            raise Exception(f"执行命令失败: {result}")
        architecture = result.strip().lower()
        
        # 映射到标准架构名称
        if architecture in ['x86_64', 'amd64']:
            return 'amd64'
        elif architecture in ['arm64', 'aarch64']:
            return 'arm64'
        else:
            raise Exception(f"不支持的架构: {architecture}")
    except Exception as e:
        raise Exception(f"检测节点架构失败: {str(e)}")

def upload_fio_files(ssh_client, architecture, login_credential):
    """上传对应架构的fio文件"""
    try:
        import os
        import tempfile
        import zipfile
        
        # 获取登录凭证指定的目录
        target_dir = login_credential.platform_partition
        logging.info(f"使用登录凭证指定的目录: {target_dir}")
        
        # 1. 创建目标目录（如果不存在）
        logging.info(f"检查并创建目录: {target_dir}")
        mkdir_cmd = f'mkdir -p {target_dir}'
        success, output = ssh_client.execute_command(mkdir_cmd)
        if not success:
            raise Exception(f"创建目录失败: {output}")
        logging.info(f"成功创建目录: {target_dir}")
        
        # 2. 打包fio源码为zip文件
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        local_fio_src = os.path.join(project_root, 'util', 'fio-fio-3.36')
        fio_dir_name = os.path.basename(local_fio_src)
        
        # 创建临时zip文件
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            zip_path = temp_file.name
        
        logging.info(f"创建fio源码压缩包: {zip_path}")
        
        # 打包fio源码
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(local_fio_src):
                for file in files:
                    local_file = os.path.join(root, file)
                    arcname = os.path.relpath(local_file, os.path.dirname(local_fio_src))
                    zipf.write(local_file, arcname)
        
        logging.info(f"fio源码压缩包创建成功")
        
        # 3. 上传zip文件到节点
        remote_zip_path = f'{target_dir}/{fio_dir_name}.zip'
        logging.info(f"上传压缩包到节点: {remote_zip_path}")
        
        ssh_client.upload_file(zip_path, remote_zip_path)
        logging.info(f"压缩包上传成功")
        
        # 4. 删除本地临时zip文件
        os.unlink(zip_path)
        logging.info(f"删除本地临时压缩包")
        
        # 5. 在节点上解压zip文件
        remote_fio_src = f'{target_dir}/{fio_dir_name}'
        logging.info(f"在节点上解压压缩包到: {remote_fio_src}")
        
        # 删除已存在的目录（如果有）
        ssh_client.execute_command(f'rm -rf {remote_fio_src}')
        
        # 解压命令
        unzip_cmd = f'cd {target_dir} && unzip -o {remote_zip_path}'
        success, output = ssh_client.execute_command(unzip_cmd)
        if not success:
            raise Exception(f"解压压缩包失败: {output}")
        logging.info(f"压缩包解压成功")

        # 6. 删除远程zip文件
        ssh_client.execute_command(f'rm -f {remote_zip_path}')
        logging.info(f"删除远程压缩包")

        # 7. 转换文件格式从Windows CRLF到Linux LF
        logging.info("转换文件格式为Linux格式（解决换行符问题）")
        find_dos2unix_cmd = f'which dos2unix'
        success, _ = ssh_client.execute_command(find_dos2unix_cmd)
        if success:
            ssh_client.execute_command(f"find {remote_fio_src} -type f -name '*.sh' -exec dos2unix {{}} +")
            ssh_client.execute_command(f'dos2unix {remote_fio_src}/configure 2>/dev/null || true')
            ssh_client.execute_command(f'dos2unix {remote_fio_src}/FIO-VERSION-GEN 2>/dev/null || true')
            logging.info("文件格式转换完成")
        else:
            ssh_client.execute_command(f"find {remote_fio_src} -type f -exec sed -i 's/\\r$//' {{}} +")
            logging.info("使用sed转换文件格式完成")

        # 8. 在节点上编译fio
        # 8.1 为所有可执行文件添加执行权限
        chmod_cmd = f'chmod -R +x {remote_fio_src}/'
        logging.info(f"为fio源码目录添加执行权限: {chmod_cmd}")
        success, output = ssh_client.execute_command(chmod_cmd)
        if not success:
            logging.error(f"添加执行权限失败: {output}")
            raise Exception(f"添加执行权限失败: {output}")
        logging.info("成功添加执行权限")
        
        # 8.2 执行编译
        compile_cmd = f'cd {remote_fio_src} && make -j$(nproc)'
        logging.info(f"编译fio源码: {compile_cmd}")
        success, output = ssh_client.execute_command(compile_cmd, timeout=600)
        if not success:
            logging.error(f"fio编译失败: {output[:100]}...")
            raise Exception(f"fio编译失败: {output}")
        logging.info("fio编译成功")
        
        # 9. 验证编译后的fio能否正常执行
        logging.info("验证编译后的fio能否正常执行")
        test_cmd = f'{remote_fio_src}/fio --version'
        success, output = ssh_client.execute_command(test_cmd)
        if not success:
            logging.error(f"fio执行失败: {output}")
            raise Exception(f"fio执行失败: {output}")
        logging.info(f"fio执行成功，版本: {output.strip()}")
        
        # 10. 添加fio到PATH，方便后续使用
        ssh_client.execute_command(f'echo "export PATH={remote_fio_src}:$PATH" >> ~/.bashrc')
        
        logging.info("fio工具上传和配置完成")
        
    except Exception as e:
        logging.error(f"配置fio环境失败: {str(e)}")
        raise Exception(f"配置fio环境失败: {str(e)}")

# send_task_log函数现在从socket_events模块导入，用于WebSocket实时日志推送