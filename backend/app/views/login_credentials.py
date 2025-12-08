from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, LoginCredential
from app.utils.responses import success_response, error_response

login_credentials_bp = Blueprint('login_credentials', __name__)

@login_credentials_bp.route('', methods=['GET'])
@jwt_required()
def get_login_credentials():
    """获取登录凭证列表"""
    try:
        current_user_id = get_jwt_identity()
        credentials = LoginCredential.get_by_user(current_user_id)
        return success_response([cred.to_dict() for cred in credentials])
    except Exception as e:
        return error_response(f'获取登录凭证列表失败: {str(e)}', 500)

@login_credentials_bp.route('/<int:credential_id>', methods=['GET'])
@jwt_required()
def get_login_credential(credential_id):
    """获取单个登录凭证信息"""
    try:
        current_user_id = get_jwt_identity()
        credential = LoginCredential.query.get(credential_id)
        
        if not credential:
            return error_response('登录凭证不存在', 404)
        
        # 验证凭证是否属于当前用户
        if credential.created_by != current_user_id:
            return error_response('无权访问该登录凭证', 403)
        
        return success_response(credential.to_dict(include_sensitive=True))
    except Exception as e:
        return error_response(f'获取登录凭证信息失败: {str(e)}', 500)

@login_credentials_bp.route('', methods=['POST'])
@jwt_required()
def create_login_credential():
    """创建新的登录凭证"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['alias', 'host', 'username', 'auth_type']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'{field} 是必需的', 400)
        
        # 创建登录凭证
        credential = LoginCredential(
            alias=data['alias'],
            host=data['host'],
            port=data.get('port', 22),
            username=data['username'],
            auth_type=data['auth_type'],
            created_by=current_user_id
        )
        
        # 设置密码（如果是密码认证）
        if data['auth_type'] == 'password' and data.get('password'):
            credential.set_password(data['password'])
        
        # 设置私钥信息（如果是密钥认证）
        if data['auth_type'] == 'key':
            if data.get('private_key_path'):
                credential.private_key_path = data['private_key_path']
            else:
                credential.private_key_path = None
            
            # 设置私钥内容和密码
            credential.set_private_key(data.get('private_key'))
            credential.set_passphrase(data.get('passphrase'))
        
        # 设置其他可选字段
        if data.get('root_password'):
            credential.set_root_password(data['root_password'])
        
        if data.get('base_path'):
            credential.base_path = data['base_path']
        
        if data.get('platform_partition'):
            credential.platform_partition = data['platform_partition']
        
        if data.get('description'):
            credential.description = data['description']
        
        db.session.add(credential)
        db.session.commit()
        
        return success_response(credential.to_dict(), '登录凭证创建成功', 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'创建登录凭证失败: {str(e)}', 500)

@login_credentials_bp.route('/<int:credential_id>', methods=['PUT'])
@jwt_required()
def update_login_credential(credential_id):
    """更新登录凭证信息"""
    try:
        current_user_id = get_jwt_identity()
        credential = LoginCredential.query.get(credential_id)
        
        if not credential:
            return error_response('登录凭证不存在', 404)
        
        # 验证凭证是否属于当前用户
        if credential.created_by != current_user_id:
            return error_response('无权修改该登录凭证', 403)
        
        data = request.get_json()
        
        # 更新基本信息
        if 'alias' in data:
            credential.alias = data['alias']
        
        if 'host' in data:
            credential.host = data['host']
        
        if 'port' in data:
            credential.port = data['port']
        
        if 'username' in data:
            credential.username = data['username']
        
        if 'auth_type' in data:
            credential.auth_type = data['auth_type']
        
        # 更新密码（如果是密码认证）
        if data.get('auth_type') == 'password' and data.get('password'):
            credential.set_password(data['password'])
        elif credential.auth_type == 'password' and data.get('password'):
            credential.set_password(data['password'])
        
        # 更新私钥信息（如果是密钥认证）
        if 'auth_type' in data or credential.auth_type == 'key':
            auth_type = data.get('auth_type', credential.auth_type)
            if auth_type == 'key':
                if 'private_key_path' in data:
                    credential.private_key_path = data['private_key_path']
                
                # 更新私钥内容和密码
                if 'private_key' in data:
                    credential.set_private_key(data['private_key'])
                
                if 'passphrase' in data:
                    credential.set_passphrase(data['passphrase'])
        
        # 更新root密码
        if data.get('root_password') is not None:
            if data['root_password']:
                credential.set_root_password(data['root_password'])
            else:
                credential.root_password_encrypted = None
        
        # 更新其他字段
        if 'base_path' in data:
            credential.base_path = data['base_path']
        
        if 'platform_partition' in data:
            credential.platform_partition = data['platform_partition']
        
        if 'description' in data:
            credential.description = data['description']
        
        if 'is_active' in data:
            credential.is_active = data['is_active']
        
        db.session.commit()
        
        return success_response(credential.to_dict(), '登录凭证更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新登录凭证失败: {str(e)}', 500)

@login_credentials_bp.route('/<int:credential_id>', methods=['DELETE'])
@jwt_required()
def delete_login_credential(credential_id):
    """删除登录凭证"""
    try:
        current_user_id = get_jwt_identity()
        credential = LoginCredential.query.get(credential_id)
        
        if not credential:
            return error_response('登录凭证不存在', 404)
        
        # 验证凭证是否属于当前用户
        if credential.created_by != current_user_id:
            return error_response('无权删除该登录凭证', 403)
        
        db.session.delete(credential)
        db.session.commit()
        
        return success_response(None, '登录凭证删除成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除登录凭证失败: {str(e)}', 500)

@login_credentials_bp.route('/<int:credential_id>/test', methods=['POST'])
@jwt_required()
def test_login_credential(credential_id):
    """测试登录凭证连接"""
    try:
        current_user_id = get_jwt_identity()
        credential = LoginCredential.query.get(credential_id)
        
        if not credential:
            return error_response('登录凭证不存在', 404)
        
        # 验证凭证是否属于当前用户
        if credential.created_by != current_user_id:
            return error_response('无权测试该登录凭证', 403)
        
        success, message = credential.test_connection()
        
        if success:
            return success_response({'connected': True}, '连接成功')
        else:
            return error_response(f'连接失败: {message}', 400)
    except Exception as e:
        return error_response(f'测试连接失败: {str(e)}', 500)