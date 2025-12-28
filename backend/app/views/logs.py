from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import TestLog, IOStatMetric
from app.utils.responses import success_response, error_response

logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/<int:log_id>/iostat-metrics', methods=['GET'])
@jwt_required()
def get_iostat_metrics(log_id):
    """获取IOSTAT指标数据"""
    try:
        # 获取查询参数
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        
        # 查询IOSTAT指标
        query = IOStatMetric.query.filter_by(test_log_id=log_id)
        
        # 如果提供了时间范围，添加时间过滤
        if start_time and end_time:
            from datetime import datetime
            try:
                start_datetime = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                end_datetime = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                query = query.filter(
                    IOStatMetric.collection_time.between(start_datetime, end_datetime)
                )
            except ValueError as e:
                return error_response(f'时间格式错误: {str(e)}', 400)
        
        # 按时间排序
        query = query.order_by(IOStatMetric.collection_time)
        
        # 获取结果
        metrics = query.all()
        
        return success_response(
            [metric.to_dict() for metric in metrics],
            message="获取IOSTAT指标数据成功"
        )
    except Exception as e:
        return error_response(str(e), 500)

@logs_bp.route('/<int:log_id>', methods=['GET'])
@jwt_required()
def get_log(log_id):
    """获取日志详情"""
    try:
        # 查询日志
        log = TestLog.query.get(log_id)
        if not log:
            return error_response('日志不存在', 404)
        
        return success_response(
            log.to_dict(),
            message="获取日志详情成功"
        )
    except Exception as e:
        return error_response(str(e), 500)

@logs_bp.route('/<int:log_id>/download', methods=['GET'])
@jwt_required()
def download_log(log_id):
    """下载日志文件"""
    try:
        from flask import send_file
        
        # 查询日志
        log = TestLog.query.get(log_id)
        if not log:
            return error_response('日志不存在', 404)
        
        # 检查日志文件是否存在
        import os
        if not os.path.exists(log.log_path):
            return error_response('日志文件不存在', 404)
        
        # 发送文件
        return send_file(
            log.log_path,
            as_attachment=True,
            download_name=log.log_filename
        )
    except Exception as e:
        return error_response(str(e), 500)
