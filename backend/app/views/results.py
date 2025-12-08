from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, TestResult, TestResultAggregation
from app.utils.responses import success_response, error_response

results_bp = Blueprint('results', __name__)

@results_bp.route('', methods=['GET'])
@jwt_required()
def get_results():
    """获取测试结果列表"""
    try:
        results = TestResult.query.all()
        return success_response([result.to_dict() for result in results])
    except Exception as e:
        return error_response(f'获取测试结果列表失败: {str(e)}', 500)

@results_bp.route('/<int:result_id>', methods=['GET'])
@jwt_required()
def get_result(result_id):
    """获取单个测试结果信息"""
    try:
        result = TestResult.query.get(result_id)
        if not result:
            return error_response('测试结果不存在', 404)
        return success_response(result.to_dict())
    except Exception as e:
        return error_response(f'获取测试结果信息失败: {str(e)}', 500)

@results_bp.route('/<int:result_id>', methods=['DELETE'])
@jwt_required()
def delete_result(result_id):
    """删除测试结果"""
    try:
        result = TestResult.query.get(result_id)
        if not result:
            return error_response('测试结果不存在', 404)
        
        db.session.delete(result)
        db.session.commit()
        return success_response(None, '测试结果删除成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除测试结果失败: {str(e)}', 500)

@results_bp.route('/aggregations', methods=['GET'])
@jwt_required()
def get_aggregations():
    """获取测试结果聚合数据"""
    try:
        aggregations = TestResultAggregation.query.all()
        return success_response([agg.to_dict() for agg in aggregations])
    except Exception as e:
        return error_response(f'获取测试结果聚合数据失败: {str(e)}', 500)

@results_bp.route('/aggregations/<int:agg_id>', methods=['GET'])
@jwt_required()
def get_aggregation(agg_id):
    """获取单个测试结果聚合信息"""
    try:
        agg = TestResultAggregation.query.get(agg_id)
        if not agg:
            return error_response('测试结果聚合不存在', 404)
        return success_response(agg.to_dict())
    except Exception as e:
        return error_response(f'获取测试结果聚合信息失败: {str(e)}', 500)