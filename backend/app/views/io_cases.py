from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, IOTestCase, TestCaseTemplate
from app.utils.responses import success_response, error_response

io_cases_bp = Blueprint('io_cases', __name__)

@io_cases_bp.route('', methods=['GET'])
@jwt_required()
def get_io_cases():
    """获取IO测试用例列表"""
    try:
        cases = IOTestCase.query.all()
        return success_response([case.to_dict() for case in cases])
    except Exception as e:
        return error_response(f'获取IO测试用例列表失败: {str(e)}', 500)

@io_cases_bp.route('/<int:case_id>', methods=['GET'])
@jwt_required()
def get_io_case(case_id):
    """获取单个IO测试用例信息"""
    try:
        case = IOTestCase.query.get(case_id)
        if not case:
            return error_response('IO测试用例不存在', 404)
        return success_response(case.to_dict())
    except Exception as e:
        return error_response(f'获取IO测试用例信息失败: {str(e)}', 500)

@io_cases_bp.route('', methods=['POST'])
@jwt_required()
def create_io_case():
    """创建新IO测试用例"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['name', 'parameters']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'{field} 是必需的', 400)
        
        case = IOTestCase(
            name=data['name'],
            description=data.get('description'),
            parameters=data['parameters'],
            created_by=current_user_id
        )
        
        db.session.add(case)
        db.session.commit()
        
        return success_response(case.to_dict(), 'IO测试用例创建成功', 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'创建IO测试用例失败: {str(e)}', 500)

@io_cases_bp.route('/<int:case_id>', methods=['PUT'])
@jwt_required()
def update_io_case(case_id):
    """更新IO测试用例信息"""
    try:
        case = IOTestCase.query.get(case_id)
        if not case:
            return error_response('IO测试用例不存在', 404)
        
        data = request.get_json()
        if 'name' in data:
            case.name = data['name']
        if 'description' in data:
            case.description = data['description']
        if 'parameters' in data:
            case.parameters = data['parameters']
        
        db.session.commit()
        return success_response(case.to_dict(), 'IO测试用例信息更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新IO测试用例信息失败: {str(e)}', 500)

@io_cases_bp.route('/<int:case_id>', methods=['DELETE'])
@jwt_required()
def delete_io_case(case_id):
    """删除IO测试用例"""
    try:
        case = IOTestCase.query.get(case_id)
        if not case:
            return error_response('IO测试用例不存在', 404)
        
        db.session.delete(case)
        db.session.commit()
        return success_response(None, 'IO测试用例删除成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除IO测试用例失败: {str(e)}', 500)

@io_cases_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_templates():
    """获取测试用例模板列表"""
    try:
        templates = TestCaseTemplate.query.all()
        return success_response([template.to_dict() for template in templates])
    except Exception as e:
        return error_response(f'获取测试用例模板列表失败: {str(e)}', 500)