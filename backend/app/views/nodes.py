from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, Node
from app.utils.responses import success_response, error_response

nodes_bp = Blueprint('nodes', __name__)

@nodes_bp.route('', methods=['GET'])
@jwt_required()
def get_nodes():
    """获取节点列表"""
    try:
        nodes = Node.query.all()
        return success_response([node.to_dict() for node in nodes])
    except Exception as e:
        return error_response(f'获取节点列表失败: {str(e)}', 500)

@nodes_bp.route('/<int:node_id>', methods=['GET'])
@jwt_required()
def get_node(node_id):
    """获取单个节点信息"""
    try:
        node = Node.query.get(node_id)
        if not node:
            return error_response('节点不存在', 404)
        return success_response(node.to_dict())
    except Exception as e:
        return error_response(f'获取节点信息失败: {str(e)}', 500)

@nodes_bp.route('', methods=['POST'])
@jwt_required()
def create_node():
    """创建新节点"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['name', 'ip_address']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'{field} 是必需的', 400)
        
        # 获取登录凭证ID
        login_credential_id = data.get('login_credential_id')
        
        # 如果没有提供登录凭证ID，返回错误信息
        if not login_credential_id:
            return error_response('login_credential_id 是必需的', 400)
        
        node = Node(
            name=data['name'],
            ip_address=data['ip_address'],
            login_credential_id=login_credential_id,
            created_by=current_user_id
        )
        
        db.session.add(node)
        db.session.commit()
        
        return success_response(node.to_dict(), '节点创建成功', 201)
    except Exception as e:
        db.session.rollback()
        # 检查是否是唯一性约束错误
        if 'unique constraint' in str(e).lower() or 'duplicate entry' in str(e).lower():
            if 'name' in str(e):
                return error_response('节点名称已存在，请使用其他名称', 400)
        return error_response(f'创建节点失败: {str(e)}', 500)

@nodes_bp.route('/<int:node_id>', methods=['PUT'])
@jwt_required()
def update_node(node_id):
    """更新节点信息"""
    try:
        node = Node.query.get(node_id)
        if not node:
            return error_response('节点不存在', 404)
        
        data = request.get_json()
        if 'name' in data:
            node.name = data['name']
        if 'ip_address' in data:
            node.ip_address = data['ip_address']
        if 'status' in data:
            node.status = data['status']
        if 'os_type' in data:
            node.os_type = data['os_type']
        if 'os_version' in data:
            node.os_version = data['os_version']
        if 'cpu_info' in data:
            node.cpu_info = data['cpu_info']
        if 'memory_total' in data:
            node.memory_total = data['memory_total']
        if 'disk_total' in data:
            node.disk_total = data['disk_total']
        if 'io_partitions' in data:
            node.io_partitions = data['io_partitions']
        if 'login_credential_id' in data:
            node.login_credential_id = data['login_credential_id']
        
        db.session.commit()
        return success_response(node.to_dict(), '节点信息更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新节点信息失败: {str(e)}', 500)

@nodes_bp.route('/<int:node_id>', methods=['DELETE'])
@jwt_required()
def delete_node(node_id):
    """删除节点"""
    try:
        node = Node.query.get(node_id)
        if not node:
            return error_response('节点不存在', 404)
        
        db.session.delete(node)
        db.session.commit()
        return success_response(None, '节点删除成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除节点失败: {str(e)}', 500)

@nodes_bp.route('/<int:node_id>/status', methods=['GET'])
@jwt_required()
def check_node_status(node_id):
    """检查节点状态"""
    try:
        node = Node.query.get(node_id)
        if not node:
            return error_response('节点不存在', 404)
        
        # 这里应该实现实际的节点状态检查逻辑
        # 目前只是返回节点的当前状态
        return success_response({'status': node.status})
    except Exception as e:
        return error_response(f'检查节点状态失败: {str(e)}', 500)