#!/usr/bin/env python3
"""任务视图模块"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

from app.models.test_task import TestTask, TaskExecution
from app.models.node import Node
from app.models.io_test_case import IOTestCase
from app.models.login_credential import LoginCredential

from app.models.test_log import TestLog
from app import db
from app.utils.task_executor import execute_node_task
from app.utils.decorators import with_app_context
from app.views.socket_events import send_task_log

# 创建蓝图
tasks_bp = Blueprint('tasks', __name__)

# 日志配置
logger = logging.getLogger(__name__)


def get_task_info(task_id, execution_id, db):
    """获取任务信息"""
    try:
        task = db.session.query(TestTask).filter_by(id=task_id).first()
        if not task:
            logger.error(f"任务不存在: task_id={task_id}")
            return None, None
        
        execution = db.session.query(TaskExecution).filter_by(id=execution_id).first()
        if not execution:
            logger.error(f"任务执行记录不存在: execution_id={execution_id}")
            return task, None
        
        return task, execution
    except Exception as e:
        logger.error(f"获取任务信息失败: {e}")
        return None, None


def get_task_nodes(task):
    """获取任务关联的节点"""
    try:
        # 获取任务关联的节点
        return task.nodes
    except Exception as e:
        logger.error(f"获取任务节点失败: {e}")
        return []


def get_task_io_test_cases(task_id, db):
    """获取任务关联的IO测试用例"""
    try:
        # 获取任务关联的IO测试用例
        from app.models import task_case_association
        from app.models.io_test_case import IOTestCase
        
        # 通过关联表查询IO测试用例
        io_test_cases = db.session.query(IOTestCase).join(
            task_case_association,
            IOTestCase.id == task_case_association.c.io_test_case_id
        ).filter(
            task_case_association.c.test_task_id == task_id
        ).all()
        return io_test_cases
    except Exception as e:
        logger.error(f"获取任务IO测试用例失败: {e}")
        return []


def run_task_execution(task_id, execution_id, app):
    """执行任务的实际逻辑"""
    # 使用应用上下文装饰器
    @with_app_context(app)
    def execute_task():
        # 导入模型和工具
        from app.models.test_task import TestTask, TaskExecution
        from app import db
        
        task = None
        execution = None
        task_failed = False  # 任务失败标志
        failure_reasons = []  # 初始化失败原因列表
        
        try:
            logging.info(f"-----------开始执行任务: task_id={task_id}, execution_id={execution_id}------------")

            logging.info(f"创建应用上下文，开始查询数据库")

            # 获取任务信息
            task, execution = get_task_info(task_id, execution_id, db)

            # 发送任务开始阶段
            send_task_log(task_id, f"任务开始",
                        level='INFO',
                        context={'operation': 'task_start', 'stage': '任务开始', 'task_name': task.name})

            # 获取任务关联的节点
            nodes = get_task_nodes(task)

            # 获取任务关联的IO测试用例
            io_test_cases = get_task_io_test_cases(task_id, db)

            # 发送详细的任务开始信息
            node_names = [f"{node.name}({node.ip_address})" for node in nodes]
            io_model_names = [case.name for case in io_test_cases]
            send_task_log(task_id, f"任务开始：准备在 {len(nodes)} 个节点上执行 {len(io_test_cases)} 个IO模型",
                        level='INFO',
                        context={'operation': 'task_start', 'stage': '任务开始', 'task_name': task.name,
                                'nodes': node_names, 'io_models': io_model_names, 'node_count': len(nodes), 'io_case_count': len(io_test_cases)})

            # 为每个节点执行任务
            logging.info(f"开始为每个节点执行任务，节点数量: {len(nodes)}")

            # 获取执行模式，默认为并行
            execution_mode = task.execution_mode if hasattr(task, 'execution_mode') else 'parallel'
            logging.info(f"任务执行模式: {execution_mode}")
            
            # 执行节点任务
            if execution_mode == 'parallel':
                # 并行执行
                logging.info("使用并行模式执行节点任务")
                from concurrent.futures import ThreadPoolExecutor, as_completed
                
                # 限制并发数，最多同时执行3个节点
                max_workers = min(3, len(nodes))
                logging.info(f"最大并发数: {max_workers}")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # 提交所有节点任务
                    future_to_node = {executor.submit(execute_node_task, node, task_id, execution_id, io_test_cases, app): node for node in nodes}
                    
                    # 收集执行结果
                    for future in as_completed(future_to_node):
                        node = future_to_node[future]
                        try:
                            node_failed_flag, error_msg = future.result()
                            if node_failed_flag:
                                task_failed = True
                                failure_reasons.append(f"节点 {node.name} ({node.ip_address}): {error_msg}")
                        except Exception as e:
                            logging.error(f"执行节点任务时发生异常: {e}")
                            task_failed = True
                            failure_reasons.append(f"节点 {node.name} ({node.ip_address}): 执行异常: {str(e)}")
            else:
                # 串行执行
                logging.info("使用串行模式执行节点任务")
                for node in nodes:
                    node_failed_flag, error_msg = execute_node_task(node, task_id, execution_id, io_test_cases, app)
                    if node_failed_flag:
                        task_failed = True
                        failure_reasons.append(f"节点 {node.name} ({node.ip_address}): {error_msg}")
            
            # 6. 更新任务状态
            logging.info(f"更新任务状态: task_id={task_id}")
            if task_failed:
                # 任务失败
                task.status = 'failed'
                execution.status = 'failed'
                execution.error_message = '; '.join(failure_reasons)
                send_task_log(task_id, f"任务执行失败",
                            level='ERROR',
                            context={'operation': 'task_failed', 'stage': '任务失败', 'failure_count': len(failure_reasons)})
                logging.error(f"任务执行失败: {'; '.join(failure_reasons)}")
            else:
                # 任务成功
                task.status = 'completed'
                execution.status = 'completed'
                execution.duration = int((datetime.utcnow() - execution.start_time).total_seconds()) if execution.start_time else 0

                # 发送详细的完成信息
                node_count = len(task.nodes) if hasattr(task, 'nodes') else 0
                io_case_count = len(get_task_io_test_cases(task_id, db))
                send_task_log(task_id, f"任务完成：共测试 {node_count} 个节点，执行 {io_case_count} 个IO模型，耗时 {execution.duration} 秒",
                            level='INFO',
                            context={'operation': 'task_completed', 'stage': '任务完成', 'duration': execution.duration, 'node_count': node_count, 'io_case_count': io_case_count})
                logging.info("任务执行完成")
            
            # 更新完成时间
            task.completed_at = datetime.utcnow()
            execution.end_time = datetime.utcnow()
            
            # 提交事务
            db.session.commit()
            logging.info(f"任务状态更新成功: task_id={task_id}, status={task.status}")

        except Exception as e:
            logging.error(f"执行任务时发生异常: {e}", exc_info=True)
            send_task_log(task_id, f"任务执行异常",
                        level='ERROR',
                        context={'operation': 'task_exception', 'stage': '任务异常', 'error': str(e)})
            
            # 更新任务状态为失败
            try:
                if task:
                    task.status = 'failed'
                if execution:
                    execution.status = 'failed'
                    execution.error_message = str(e)
                db.session.commit()
            except Exception as update_error:
                logging.error(f"更新任务状态失败: {update_error}")
        
        finally:
            # 清理资源
            send_task_log(task_id, f"终止任务：回收线程资源和清理临时文件",
                        level='INFO',
                        context={'operation': 'cleanup_resources', 'stage': '资源回收'})
            logging.info(f"清理任务执行资源: task_id={task_id}")
            logging.info(f"-----------任务执行结束: task_id={task_id}, execution_id={execution_id}------------")
    
    # 执行任务
    execute_task()


@tasks_bp.route('/run/<int:task_id>', methods=['POST'])
def run_task(task_id):
    """执行任务"""
    try:
        from flask import current_app
        app = current_app._get_current_object()

        # 获取任务信息
        task = db.session.query(TestTask).filter_by(id=task_id).first()
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在',
                'data': None
            }), 404

        # 创建任务执行记录
        execution = TaskExecution(
            test_task_id=task_id,
            status='running',
            start_time=datetime.utcnow()
        )
        db.session.add(execution)
        db.session.commit()

        # 启动线程执行任务
        thread = threading.Thread(
            target=run_task_execution,
            args=(task_id, execution.id, app)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': '任务开始执行',
            'data': {
                'task_id': task_id,
                'execution_id': execution.id
            }
        }), 200

    except Exception as e:
        logger.error(f"执行任务失败: {e}")
        return jsonify({
            'success': False,
            'message': f'执行任务失败: {str(e)}',
            'data': None
        }), 500


@tasks_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情"""
    try:
        task = db.session.query(TestTask).filter_by(id=task_id).first()
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在',
                'data': None
            }), 404
        
        # 获取任务执行记录
        executions = db.session.query(TaskExecution).filter_by(test_task_id=task_id).order_by(TaskExecution.created_at.desc()).all()
        
        # 获取任务关联的节点
        nodes = get_task_nodes(task)
        
        # 获取任务关联的IO测试用例
        io_test_cases = get_task_io_test_cases(task_id, db)
        
        return jsonify({
            'success': True,
            'message': '获取任务详情成功',
            'data': {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'status': task.status,
                'execution_mode': task.execution_mode,
                'created_at': task.created_at,
                'updated_at': task.updated_at,
                'completed_at': task.completed_at,
                'executions': [{
                    'id': exec.id,
                    'status': exec.status,
                    'start_time': exec.start_time,
                    'end_time': exec.end_time,
                    'duration': exec.duration,
                    'error_message': exec.error_message
                } for exec in executions],
                'nodes': [{
                    'id': node.id,
                    'name': node.name,
                    'ip_address': node.ip_address,
                    'status': node.status,
                    'io_partitions': node.io_partitions if hasattr(node, 'io_partitions') else []
                } for node in nodes],
                'io_test_cases': [{
                    'id': case.id,
                    'name': case.name,
                    'description': case.description,
                    'tool': case.tool,
                    'parameters': case.parameters
                } for case in io_test_cases]
            }
        }), 200
    
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取任务详情失败: {str(e)}',
            'data': None
        }), 500


@tasks_bp.route('/', methods=['GET'])
def get_tasks():
    """获取任务列表（优化版 - 使用 eager loading 避免 N+1 查询）"""
    try:
        from sqlalchemy.orm import joinedload
        from app.models import task_case_association, task_node_association

        # 使用 joinedload 一次性加载所有关联数据
        tasks = db.session.query(TestTask)\
            .options(joinedload(TestTask.nodes))\
            .order_by(TestTask.created_at.desc())\
            .all()

        # 批量获取所有任务的测试用例ID（一次查询）
        task_ids = [task.id for task in tasks]
        case_associations = db.session.query(
            task_case_association.c.test_task_id,
            task_case_association.c.io_test_case_id
        ).filter(
            task_case_association.c.test_task_id.in_(task_ids)
        ).all() if task_ids else []

        # 构建任务ID到测试用例ID的映射
        task_case_map = {}
        for task_id, case_id in case_associations:
            if task_id not in task_case_map:
                task_case_map[task_id] = []
            task_case_map[task_id].append(case_id)

        # 批量获取所有需要的测试用例信息（一次查询）
        all_case_ids = list(set([case_id for _, case_id in case_associations]))
        io_cases_query = db.session.query(IOTestCase).filter(
            IOTestCase.id.in_(all_case_ids)
        ).all() if all_case_ids else []
        io_cases_dict = {case.id: case for case in io_cases_query}

        # 构建返回数据（只返回列表页面需要的字段）
        tasks_data = []
        for task in tasks:
            # 节点信息（已通过 joinedload 加载，不会触发额外查询）
            nodes_data = [{
                'id': node.id,
                'name': node.name,
                'ip_address': node.ip_address,
                'status': node.status
                # ❌ 删除 io_partitions - 列表页面不需要
            } for node in task.nodes]

            # 测试用例信息（从缓存中获取）
            case_ids = task_case_map.get(task.id, [])
            io_test_cases_data = [{
                'id': case_id,
                'name': io_cases_dict[case_id].name
            } for case_id in case_ids if case_id in io_cases_dict]

            tasks_data.append({
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'status': task.status,
                'priority': task.priority if hasattr(task, 'priority') else 'medium',
                'execution_mode': task.execution_mode,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'task_space_id': task.task_space_id if hasattr(task, 'task_space_id') else None,
                'progress': 0,  # 默认进度，前端可以计算
                'nodes': nodes_data,
                'io_test_cases': io_test_cases_data,
                'io_test_case_ids': case_ids  # 保持兼容性
            })

        logger.info(f"获取任务列表成功，共 {len(tasks_data)} 个任务")
        return jsonify({
            'success': True,
            'message': '获取任务列表成功',
            'data': tasks_data
        }), 200

    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'获取任务列表失败: {str(e)}',
            'data': None
        }), 500


@tasks_bp.route('/', methods=['POST'])
def create_task():
    """创建任务"""
    try:
        data = request.get_json()
        
        # 验证参数
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': '任务名称不能为空',
                'data': None
            }), 400
        
        # 创建任务
        task = TestTask(
            name=data.get('name'),
            description=data.get('description'),
            execution_mode=data.get('execution_mode', 'parallel')
        )
        db.session.add(task)
        db.session.commit()
        
        # 关联节点
        if 'node_ids' in data:
            from app.models.node import Node
            for node_id in data['node_ids']:
                node = Node.query.get(node_id)
                if node:
                    task.nodes.append(node)
        
        # 关联IO测试用例
        if 'io_test_case_ids' in data:
            from app.models.io_test_case import IOTestCase
            for io_test_case_id in data['io_test_case_ids']:
                io_test_case = IOTestCase.query.get(io_test_case_id)
                if io_test_case:
                    task.io_test_cases.append(io_test_case)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '创建任务成功',
            'data': {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'status': task.status,
                'execution_mode': task.execution_mode,
                'created_at': task.created_at
            }
        }), 201
    
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return jsonify({
            'success': False,
            'message': f'创建任务失败: {str(e)}',
            'data': None
        }), 500


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务"""
    try:
        task = db.session.query(TestTask).filter_by(id=task_id).first()
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在',
                'data': None
            }), 404
        
        data = request.get_json()
        
        # 更新任务信息
        if 'name' in data:
            task.name = data['name']
        if 'description' in data:
            task.description = data['description']
        if 'execution_mode' in data:
            task.execution_mode = data['execution_mode']
        
        # 更新关联节点
        if 'node_ids' in data:
            # 清空现有节点关联
            task.nodes.clear()
            # 添加新关联
            from app.models.node import Node
            for node_id in data['node_ids']:
                node = Node.query.get(node_id)
                if node:
                    task.nodes.append(node)
        
        # 更新关联IO测试用例
        if 'io_test_case_ids' in data:
            # 删除现有关联
            from app.models import task_case_association
            db.session.execute(
                task_case_association.delete().where(
                    task_case_association.c.test_task_id == task.id
                )
            )
            # 添加新关联
            from app.models.io_test_case import IOTestCase
            for io_test_case_id in data['io_test_case_ids']:
                io_test_case = IOTestCase.query.get(io_test_case_id)
                if io_test_case:
                    db.session.execute(
                        task_case_association.insert().values(
                            test_task_id=task.id,
                            io_test_case_id=io_test_case_id
                        )
                    )
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '更新任务成功',
            'data': {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'status': task.status,
                'execution_mode': task.execution_mode,
                'updated_at': task.updated_at
            }
        }), 200
    
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        return jsonify({
            'success': False,
            'message': f'更新任务失败: {str(e)}',
            'data': None
        }), 500


@tasks_bp.route('/<int:task_id>/pause', methods=['POST'])
def pause_task(task_id):
    """暂停任务"""
    try:
        task = db.session.query(TestTask).filter_by(id=task_id).first()
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在',
                'data': None
            }), 404

        # 只能暂停正在运行的任务
        if task.status != 'running':
            return jsonify({
                'success': False,
                'message': f'只能暂停正在运行的任务，当前状态：{task.status}',
                'data': None
            }), 400

        # 更新任务状态为暂停
        task.status = 'paused'

        # 更新最近的执行记录状态
        latest_execution = db.session.query(TaskExecution).filter_by(
            test_task_id=task_id
        ).order_by(TaskExecution.start_time.desc()).first()

        if latest_execution:
            latest_execution.status = 'paused'

        db.session.commit()

        # 发送暂停日志
        from app.views.socket_events import send_task_log
        send_task_log(task_id, f"任务已暂停",
                    level='INFO',
                    context={'operation': 'task_paused', 'stage': '任务暂停'})

        return jsonify({
            'success': True,
            'message': '任务已暂停',
            'data': task.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"暂停任务失败: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'暂停任务失败: {str(e)}',
            'data': None
        }), 500


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    try:
        task = db.session.query(TestTask).filter_by(id=task_id).first()
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在',
                'data': None
            }), 404

        # 按依赖顺序删除关联数据
        # 1. 删除 iostat_metrics（依赖 test_logs）
        from app.models import TestLog, IOStatMetric
        test_logs = db.session.query(TestLog).filter_by(test_task_id=task_id).all()
        test_log_ids = [log.id for log in test_logs]

        if test_log_ids:
            db.session.query(IOStatMetric).filter(IOStatMetric.test_log_id.in_(test_log_ids)).delete(synchronize_session=False)

        # 2. 删除 io_performance_data（依赖 task_executions）
        from app.models import IOPerformanceData
        executions = db.session.query(TaskExecution).filter_by(test_task_id=task_id).all()
        execution_ids = [exec.id for exec in executions]

        if execution_ids:
            db.session.query(IOPerformanceData).filter(IOPerformanceData.task_execution_id.in_(execution_ids)).delete(synchronize_session=False)

        # 3. 删除 test_results
        from app.models import TestResult
        db.session.query(TestResult).filter_by(test_task_id=task_id).delete(synchronize_session=False)

        # 4. 删除 test_logs
        db.session.query(TestLog).filter_by(test_task_id=task_id).delete(synchronize_session=False)

        # 5. 删除 task_operation_logs
        from app.models.task_operation_log import TaskOperationLog
        db.session.query(TaskOperationLog).filter_by(test_task_id=task_id).delete(synchronize_session=False)

        # 6. 删除 task_executions
        db.session.query(TaskExecution).filter_by(test_task_id=task_id).delete(synchronize_session=False)

        # 7. 清空多对多关联表（task_case_association 和 task_node_association）
        # 通过直接删除关联表记录，而不是通过 ORM 关系
        from app.models import task_case_association, task_node_association
        db.session.execute(
            task_case_association.delete().where(
                task_case_association.c.test_task_id == task_id
            )
        )
        db.session.execute(
            task_node_association.delete().where(
                task_node_association.c.test_task_id == task_id
            )
        )

        # 8. 最后删除任务本身
        db.session.delete(task)
        db.session.commit()

        logger.info(f"成功删除任务: task_id={task_id}")
        return jsonify({
            'success': True,
            'message': '删除任务成功',
            'data': None
        }), 200

    except Exception as e:
        logger.error(f"删除任务失败: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除任务失败: {str(e)}',
            'data': None
        }), 500


@tasks_bp.route('/<int:task_id>/executions/<int:execution_id>/logs', methods=['GET'])
def get_task_execution_logs(task_id, execution_id):
    """获取任务执行日志"""
    try:
        # 验证任务和执行记录存在
        task = db.session.query(TestTask).filter_by(id=task_id).first()
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在',
                'data': None
            }), 404
        
        execution = db.session.query(TaskExecution).filter_by(id=execution_id, test_task_id=task_id).first()
        if not execution:
            return jsonify({
                'success': False,
                'message': '执行记录不存在',
                'data': None
            }), 404
        
        # 获取日志
        logs = db.session.query(TestLog).filter_by(
            test_task_id=task_id,
            task_execution_id=execution_id
        ).order_by(TestLog.collection_time.desc()).all()
        
        return jsonify({
            'success': True,
            'message': '获取任务执行日志成功',
            'data': [{
                'id': log.id,
                'message': log.message,
                'level': log.level,
                'context': log.context,
                'timestamp': log.collection_time,
                'collection_time': log.collection_time
            } for log in logs]
        }), 200
    
    except Exception as e:
        logger.error(f"获取任务执行日志失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取任务执行日志失败: {str(e)}',
            'data': None
        }), 500


@tasks_bp.route('/<int:task_id>/clone', methods=['POST'])
def clone_task(task_id):
    """克隆任务"""
    try:
        # 获取原任务
        original_task = db.session.query(TestTask).filter_by(id=task_id).first()
        if not original_task:
            return jsonify({
                'success': False,
                'message': '任务不存在',
                'data': None
            }), 404
        
        # 创建新任务，复制基本信息
        new_task = TestTask(
            name=f"{original_task.name} (克隆)",
            description=original_task.description,
            execution_mode=original_task.execution_mode,
            priority=original_task.priority
        )
        # 手动设置 created_by
        new_task.created_by = 1
        db.session.add(new_task)
        db.session.commit()
        
        # 复制关联节点
        for node in original_task.nodes:
            new_task.nodes.append(node)
        
        # 复制关联IO测试用例
        for io_test_case in original_task.io_test_cases:
            new_task.io_test_cases.append(io_test_case)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '克隆任务成功',
            'data': {
                'id': new_task.id,
                'name': new_task.name,
                'description': new_task.description,
                'status': new_task.status,
                'execution_mode': new_task.execution_mode,
                'created_at': new_task.created_at
            }
        }), 201
    except Exception as e:
        logger.error(f"克隆任务失败: {e}")
        return jsonify({
            'success': False,
            'message': f'克隆任务失败: {str(e)}',
            'data': None
        }), 500


@tasks_bp.route('/<int:task_id>/results', methods=['GET'])
def get_task_results(task_id):
    """获取任务结果"""
    try:
        # 验证任务存在
        task = db.session.query(TestTask).filter_by(id=task_id).first()
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在',
                'data': None
            }), 404
        
        # 获取任务相关的测试结果
        from app.models import TestResult
        results = db.session.query(TestResult).filter_by(test_task_id=task_id).all()
        
        return jsonify({
            'success': True,
            'message': '获取任务结果成功',
            'data': [{
                'id': result.id,
                'test_task_id': result.test_task_id,
                'node_id': result.node_id,
                'io_test_case_id': result.io_test_case_id,
                'task_execution_id': result.task_execution_id,
                'status': result.status,
                'tool': result.tool,
                'command': result.command,
                'raw_output': result.raw_output,
                'parsed_results': result.parsed_results,
                'created_at': result.created_at.isoformat() if result.created_at else None
            } for result in results]
        }), 200
    except Exception as e:
        logger.error(f"获取任务结果失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取任务结果失败: {str(e)}',
            'data': None
        }), 500


@tasks_bp.route('/<int:task_id>/operation-logs', methods=['GET'])
def get_task_operation_logs(task_id):
    """获取任务的操作日志"""
    try:
        from app.models.task_operation_log import TaskOperationLog

        # 验证任务是否存在
        task = db.session.query(TestTask).filter_by(id=task_id).first()
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在',
                'data': None
            }), 404

        # 获取limit参数，默认100条
        limit = request.args.get('limit', 100, type=int)
        limit = min(limit, 500)  # 最多500条

        # 获取任务的操作日志（按时间正序，显示执行流程）
        logs = TaskOperationLog.query.filter_by(test_task_id=task_id)\
            .order_by(TaskOperationLog.timestamp.asc())\
            .limit(limit)\
            .all()

        return jsonify({
            'success': True,
            'message': '获取操作日志成功',
            'data': [log.to_dict() for log in logs]
        }), 200

    except Exception as e:
        logger.error(f"获取操作日志失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取操作日志失败: {str(e)}',
            'data': None
        }), 500