from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, TaskSpace, TaskSpaceMember, User
from app.utils.responses import success_response, error_response

# 创建蓝图
task_spaces_bp = Blueprint('task_spaces', __name__)

@task_spaces_bp.route('', methods=['GET'])
@jwt_required()
def get_task_spaces():
    """获取任务空间列表"""
    try:
        current_user_id = get_jwt_identity()
        args = request.args
        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 10, type=int)
        name = args.get('name', type=str)

        # 查询当前用户创建的空间和加入的空间
        user_spaces = TaskSpace.query.join(TaskSpaceMember, TaskSpace.id == TaskSpaceMember.task_space_id)
        query = TaskSpace.query.filter(
            (TaskSpace.owner_id == current_user_id) | (user_spaces.filter(TaskSpaceMember.user_id == current_user_id).exists()) |
            (TaskSpace.is_public == True)
        )

        if name:
            query = query.filter(TaskSpace.name.ilike(f'%{name}%'))

        spaces = query.order_by(TaskSpace.updated_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

        return success_response({
            'items': [space.to_dict() for space in spaces.items],
            'total': spaces.total,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        return error_response(f'获取任务空间列表失败: {str(e)}', 500)

@task_spaces_bp.route('/<int:space_id>', methods=['GET'])
@jwt_required()
def get_task_space(space_id):
    """获取任务空间详情"""
    try:
        current_user_id = get_jwt_identity()
        task_space = TaskSpace.query.get(space_id)
        
        if not task_space:
            return error_response('任务空间不存在', 404)

        # 检查权限
        is_owner = task_space.owner_id == current_user_id
        is_member = TaskSpaceMember.query.filter_by(
            task_space_id=space_id,
            user_id=current_user_id
        ).first()

        if not is_owner and not is_member and not task_space.is_public:
            return error_response('没有权限访问该任务空间', 403)

        return success_response(task_space.to_dict())
    except Exception as e:
        return error_response(f'获取任务空间详情失败: {str(e)}', 500)

@task_spaces_bp.route('', methods=['POST'])
@jwt_required()
def create_task_space():
    """创建任务空间"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('name'):
            return error_response('空间名称是必需的', 400)

        # 创建任务空间
        task_space = TaskSpace(
            name=data['name'],
            description=data.get('description'),
            owner_id=current_user_id,
            is_public=data.get('is_public', False)
        )

        db.session.add(task_space)
        db.session.flush()

        # 添加创建者为管理员
        member = TaskSpaceMember(
            task_space_id=task_space.id,
            user_id=current_user_id,
            role='admin'
        )
        db.session.add(member)

        db.session.commit()

        return success_response(task_space.to_dict(), '任务空间创建成功', 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'创建任务空间失败: {str(e)}', 500)

@task_spaces_bp.route('/<int:space_id>', methods=['PUT'])
@jwt_required()
def update_task_space(space_id):
    """更新任务空间"""
    try:
        current_user_id = get_jwt_identity()
        task_space = TaskSpace.query.get(space_id)
        
        if not task_space:
            return error_response('任务空间不存在', 404)

        # 检查权限
        is_owner = task_space.owner_id == current_user_id
        is_admin = TaskSpaceMember.query.filter_by(
            task_space_id=space_id,
            user_id=current_user_id,
            role='admin'
        ).first()

        if not is_owner and not is_admin:
            return error_response('没有权限修改该任务空间', 403)

        data = request.get_json()
        task_space.name = data.get('name', task_space.name)
        task_space.description = data.get('description', task_space.description)
        task_space.is_public = data.get('is_public', task_space.is_public)

        db.session.commit()

        return success_response(task_space.to_dict(), '任务空间更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新任务空间失败: {str(e)}', 500)

@task_spaces_bp.route('/<int:space_id>', methods=['DELETE'])
@jwt_required()
def delete_task_space(space_id):
    """删除任务空间"""
    try:
        current_user_id = get_jwt_identity()
        task_space = TaskSpace.query.get(space_id)
        
        if not task_space:
            return error_response('任务空间不存在', 404)

        # 只有所有者可以删除
        if task_space.owner_id != current_user_id:
            return error_response('只有空间所有者可以删除该任务空间', 403)

        # 删除空间成员
        TaskSpaceMember.query.filter_by(task_space_id=space_id).delete()

        # 删除空间
        db.session.delete(task_space)
        db.session.commit()

        return success_response(None, '任务空间删除成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除任务空间失败: {str(e)}', 500)

@task_spaces_bp.route('/<int:space_id>/members', methods=['GET'])
@jwt_required()
def get_task_space_members(space_id):
    """获取任务空间成员列表"""
    try:
        current_user_id = get_jwt_identity()
        task_space = TaskSpace.query.get(space_id)
        
        if not task_space:
            return error_response('任务空间不存在', 404)

        # 检查权限
        is_owner = task_space.owner_id == current_user_id
        is_member = TaskSpaceMember.query.filter_by(
            task_space_id=space_id,
            user_id=current_user_id
        ).first()

        if not is_owner and not is_member and not task_space.is_public:
            return error_response('没有权限访问该任务空间', 403)

        members = TaskSpaceMember.query.filter_by(task_space_id=space_id).all()
        return success_response([member.to_dict() for member in members])
    except Exception as e:
        return error_response(f'获取任务空间成员列表失败: {str(e)}', 500)

@task_spaces_bp.route('/<int:space_id>/members', methods=['POST'])
@jwt_required()
def add_task_space_member(space_id):
    """添加任务空间成员"""
    try:
        current_user_id = get_jwt_identity()
        task_space = TaskSpace.query.get(space_id)
        
        if not task_space:
            return error_response('任务空间不存在', 404)
            
        data = request.get_json()

        # 检查权限
        is_owner = task_space.owner_id == current_user_id
        is_admin = TaskSpaceMember.query.filter_by(
            task_space_id=space_id,
            user_id=current_user_id,
            role='admin'
        ).first()

        if not is_owner and not is_admin:
            return error_response('没有权限添加成员', 403)

        # 检查用户是否存在
        if not data.get('username'):
            return error_response('用户名是必需的', 400)
            
        user = User.query.filter_by(username=data['username']).first()
        if not user:
            return error_response('用户不存在', 404)

        # 检查用户是否已在空间中
        existing_member = TaskSpaceMember.query.filter_by(
            task_space_id=space_id,
            user_id=user.id
        ).first()
        if existing_member:
            return error_response('用户已在该任务空间中', 400)

        # 添加成员
        member = TaskSpaceMember(
            task_space_id=space_id,
            user_id=user.id,
            role=data.get('role', 'member')
        )

        db.session.add(member)
        db.session.commit()

        return success_response(member.to_dict(), '成员添加成功', 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'添加成员失败: {str(e)}', 500)

@task_spaces_bp.route('/<int:space_id>/members/<int:member_id>', methods=['PUT'])
@jwt_required()
def update_task_space_member(space_id, member_id):
    """更新任务空间成员角色"""
    try:
        current_user_id = get_jwt_identity()
        task_space = TaskSpace.query.get(space_id)
        
        if not task_space:
            return error_response('任务空间不存在', 404)
            
        data = request.get_json()

        # 检查权限
        is_owner = task_space.owner_id == current_user_id
        is_admin = TaskSpaceMember.query.filter_by(
            task_space_id=space_id,
            user_id=current_user_id,
            role='admin'
        ).first()

        if not is_owner and not is_admin:
            return error_response('没有权限修改成员角色', 403)

        # 不允许修改所有者角色
        member = TaskSpaceMember.query.get(member_id)
        if not member:
            return error_response('成员不存在', 404)
            
        if member.user_id == task_space.owner_id:
            return error_response('不允许修改空间所有者的角色', 400)

        # 更新角色
        member.role = data.get('role', member.role)
        db.session.commit()

        return success_response(member.to_dict(), '成员角色更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新成员角色失败: {str(e)}', 500)

@task_spaces_bp.route('/<int:space_id>/members/<int:member_id>', methods=['DELETE'])
@jwt_required()
def remove_task_space_member(space_id, member_id):
    """移除任务空间成员"""
    try:
        current_user_id = get_jwt_identity()
        task_space = TaskSpace.query.get(space_id)
        
        if not task_space:
            return error_response('任务空间不存在', 404)
            
        # 检查权限
        is_owner = task_space.owner_id == current_user_id
        is_admin = TaskSpaceMember.query.filter_by(
            task_space_id=space_id,
            user_id=current_user_id,
            role='admin'
        ).first()
        is_self = current_user_id == member_id

        if not is_owner and not is_admin and not is_self:
            return error_response('没有权限移除成员', 403)

        # 不允许移除所有者
        member = TaskSpaceMember.query.get(member_id)
        if not member:
            return error_response('成员不存在', 404)
            
        if member.user_id == task_space.owner_id:
            return error_response('不允许移除空间所有者', 400)

        # 移除成员
        db.session.delete(member)
        db.session.commit()

        return success_response(None, '成员移除成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'移除成员失败: {str(e)}', 500)