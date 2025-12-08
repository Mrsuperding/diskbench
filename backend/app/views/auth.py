from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_jwt
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import db, User
from app.utils.validators import validate_login_data, validate_password_data
from app.utils.responses import success_response, error_response
from app.utils.jwt_callbacks import token_blocklist

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        print(f"登录请求数据: {data}")
        
        # 验证输入数据
        is_valid, error_msg = validate_login_data(data)
        if not is_valid:
            print(f"数据验证失败: {error_msg}")
            return error_response(error_msg, 400)
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        print(f"登录尝试 - 用户名: {username}, 邮箱: {email}")
        
        # 根据提供的字段查找用户
        if username:
            user = User.find_by_username(username)
            print(f"根据用户名查找用户: {user}")
        else:
            user = User.find_by_email(email)
            print(f"根据邮箱查找用户: {user}")
        
        if not user:
            print("未找到用户")
            return error_response('用户名或密码错误', 401)
        
        # 检查用户状态
        if user.status == 'locked':
            return error_response('账户已被锁定', 403)
        
        if user.status == 'inactive':
            return error_response('账户未激活', 403)
        
        # 验证密码
        if not user.check_password(password):
            return error_response('用户名或密码错误', 401)
        
        # 更新登录信息
        user.last_login_at = datetime.utcnow()
        user.login_count += 1
        print(f"准备提交用户更新: {user}")
        db.session.commit()
        print(f"用户更新提交成功")
        
        # 创建token
        print(f"准备创建token, 用户ID: {user.id}")
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        print(f"token创建成功")
        
        # 准备响应数据
        print(f"准备转换用户数据为字典")
        user_data = user.to_dict(include_email=True)
        print(f"用户数据转换成功: {user_data}")
        
        return success_response({
            'token': access_token,
            'refresh_token': refresh_token,
            'user': user_data
        }, '登录成功')
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"登录错误详细信息: {str(e)}")
        print(f"错误堆栈: {traceback.format_exc()}")
        return error_response(f'登录失败: {str(e)}', 500)

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    try:
        jti = get_jwt()['jti']
        token_blocklist.add(jti)
        return success_response(None, '登出成功')
    except Exception as e:
        return error_response(f'登出失败: {str(e)}', 500)

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问token"""
    try:
        current_user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user_id)
        return success_response({'token': new_access_token}, 'Token刷新成功')
    except Exception as e:
        return error_response(f'Token刷新失败: {str(e)}', 500)

@auth_bp.route('/userinfo', methods=['GET'])
@jwt_required()
def get_user_info():
    """获取用户信息"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('用户不存在', 404)
        
        return success_response(user.to_dict(include_email=True))
    except Exception as e:
        return error_response(f'获取用户信息失败: {str(e)}', 500)

@auth_bp.route('/password', methods=['PUT'])
@jwt_required()
def update_password():
    """修改密码"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return error_response('用户不存在', 404)
        
        data = request.get_json()
        
        # 验证输入数据
        is_valid, error_msg = validate_password_data(data)
        if not is_valid:
            return error_response(error_msg, 400)
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        # 验证旧密码
        if not user.check_password(old_password):
            return error_response('旧密码错误', 400)
        
        # 设置新密码
        user.set_password(new_password)
        db.session.commit()
        
        return success_response(None, '密码修改成功')
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'密码修改失败: {str(e)}', 500)

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册（管理员功能）"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'{field} 是必需的', 400)
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')
        
        # 验证角色值
        valid_roles = ['admin', 'user']
        if role not in valid_roles:
            return error_response(f"无效的角色值，可选值：{', '.join(valid_roles)}", 400)
        
        # 检查用户名和邮箱是否已存在
        if User.find_by_username(username):
            return error_response('用户名已存在', 400)
        
        if User.find_by_email(email):
            return error_response('邮箱已存在', 400)
        
        # 创建新用户
        user = User.create_user(username, email, password, role)
        
        return success_response(user.to_dict(), '用户创建成功', 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'用户创建失败: {str(e)}', 500)