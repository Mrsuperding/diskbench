# SocketIO事件处理文件
# 用于实现任务日志的实时打印功能

import logging
from datetime import datetime
from flask import request
from flask_socketio import emit, join_room, leave_room
from app.models import TaskExecution, TestTask, db
from app.models.task_operation_log import TaskOperationLog

# 设置日志
logger = logging.getLogger(__name__)

# 全局socketio对象，用于发送任务日志
global_socketio = None

# 存储任务ID到SocketIO客户端ID的映射
# 格式: {task_id: [client_id1, client_id2, ...]}
task_clients = {}

def register_socket_events(socketio):
    """注册SocketIO事件处理函数"""
    global global_socketio
    global_socketio = socketio
    
    @socketio.on('connect')
    def handle_connect(auth):
        """处理客户端连接"""
        # 获取当前客户端的会话ID
        client_sid = request.sid
        logger.info('客户端已连接: %s', client_sid)
        emit('connect_response', {'message': '连接成功'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """处理客户端断开连接"""
        # 获取当前客户端的会话ID
        client_sid = request.sid
        logger.info('客户端已断开: %s', client_sid)
        
        # 从所有任务房间中移除客户端
        for task_id, clients in task_clients.items():
            if client_sid in clients:
                clients.remove(client_sid)
                leave_room(str(task_id))
    
    @socketio.on('join_task_room')
    def handle_join_task_room(data):
        """客户端加入指定任务的日志房间"""
        task_id = data.get('task_id')
        if not task_id:
            emit('error', {'message': '缺少任务ID'})
            return
        
        try:
            # 验证任务是否存在
            task = TestTask.query.get(task_id)
            if not task:
                emit('error', {'message': '任务不存在'})
                return
            
            # 加入房间
            room = str(task_id)
            join_room(room)
            
            # 记录客户端与任务的关联
            client_id = request.sid  # 使用请求的会话ID作为客户端ID
            if task_id not in task_clients:
                task_clients[task_id] = []
            if client_id not in task_clients[task_id]:
                task_clients[task_id].append(client_id)
            
            logger.info('客户端 %s 加入任务 %s 的日志房间', client_id, task_id)
            emit('join_room_response', {'message': f'已加入任务 {task_id} 的日志房间'})
        except Exception as e:
            logger.error('加入任务房间失败: %s', str(e))
            emit('error', {'message': f'加入房间失败: {str(e)}'})
    
    @socketio.on('leave_task_room')
    def handle_leave_task_room(data):
        """客户端离开指定任务的日志房间"""
        task_id = data.get('task_id')
        if not task_id:
            emit('error', {'message': '缺少任务ID'})
            return
        
        try:
            # 离开房间
            room = str(task_id)
            leave_room(room)
            
            # 移除客户端与任务的关联
            client_id = request.sid  # 使用请求的会话ID作为客户端ID
            if task_id in task_clients and client_id in task_clients[task_id]:
                task_clients[task_id].remove(client_id)
                # 如果任务没有客户端了，清理
                if not task_clients[task_id]:
                    del task_clients[task_id]
            
            logger.info('客户端 %s 离开任务 %s 的日志房间', client_id, task_id)
            emit('leave_room_response', {'message': f'已离开任务 {task_id} 的日志房间'})
        except Exception as e:
            logger.error('离开任务房间失败: %s', str(e))
            emit('error', {'message': f'离开房间失败: {str(e)}'})

def send_task_log(task_id, log_content, level='INFO', module='tasks', context=None, execution_id=None):
    """向指定任务的所有客户端发送日志，并保存到数据库"""
    """
    发送任务日志到WebSocket客户端并持久化到数据库

    Args:
        task_id: 任务ID
        log_content: 日志内容
        level: 日志级别
        module: 模块名称
        context: 上下文信息
        execution_id: 执行ID（可选）
    """
    try:
        room = str(task_id)
        # 构建结构化日志数据
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level,
            'module': module,
            'message': log_content,
            'context': context or {'task_id': task_id}
        }

        # 添加调试日志
        logger.info(f'准备发送日志到任务 {task_id}: message={log_content[:50]}..., global_socketio={global_socketio is not None}')

        # 发送日志到房间内所有客户端
        if global_socketio:
            global_socketio.emit('task_log', {'data': log_data}, room=room)
            logger.info('已发送日志到任务 %s 的房间', task_id, extra={'context': {'task_id': task_id, 'log_level': level}})
        else:
            logger.warning('全局socketio对象未初始化，无法发送日志', extra={'context': {'task_id': task_id}})

        # 保存日志到数据库（在单独的try块中，避免数据库错误影响WebSocket发送）
        try:
            operation_log = TaskOperationLog.create_log(
                task_id=task_id,
                message=log_content,
                level=level,
                context=context,
                execution_id=execution_id
            )
            db.session.add(operation_log)
            db.session.commit()
            logger.debug(f'任务日志已保存到数据库: task_id={task_id}, log_id={operation_log.id}')
        except Exception as db_error:
            logger.error(f'保存任务日志到数据库失败: {db_error}', extra={'context': {'task_id': task_id}})
            # 数据库保存失败不影响WebSocket发送
            try:
                db.session.rollback()
            except:
                pass

    except Exception as e:
        logger.error('发送任务日志失败: %s', str(e), extra={'context': {'task_id': task_id}})