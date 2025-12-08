from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, User
from app.utils.responses import success_response, error_response

users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
@jwt_required()
def get_users():
    """获取用户列表"""
    try:
        users = User.query.all()
        return success_response([user.to_dict() for user in users])
    except Exception as e:
        return error_response(f'获取用户列表失败: {str(e)}', 500)

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """获取单个用户信息"""
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('用户不存在', 404)
        return success_response(user.to_dict())
    except Exception as e:
        return error_response(f'获取用户信息失败: {str(e)}', 500)

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户信息"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return error_response('用户不存在', 404)
        
        # 只有管理员或用户自己可以更新
        if user.id != current_user_id:
            return error_response('没有权限', 403)
        
        data = request.get_json()
        if 'email' in data:
            user.email = data['email']
        if 'avatar_url' in data:
            user.avatar_url = data['avatar_url']
        
        db.session.commit()
        return success_response(user.to_dict(), '用户信息更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新用户信息失败: {str(e)}', 500)

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """删除用户"""
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('用户不存在', 404)
        
        db.session.delete(user)
        db.session.commit()
        return success_response(None, '用户删除成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除用户失败: {str(e)}', 500)