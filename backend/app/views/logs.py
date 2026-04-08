from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import TestLog, IOStatMetric
from app.utils.responses import success_response, error_response
from app.utils.log_collector import log_collector

logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/<int:log_id>/iostat-metrics', methods=['GET'])
@jwt_required()
def get_iostat_metrics(log_id):
    """获取IOSTAT指标数据"""
    try:
        # 先检查日志是否存在
        log = TestLog.query.get(log_id)
        if not log:
            return error_response('日志不存在', 404)

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

@logs_bp.route('/<int:log_id>/jitter', methods=['GET'])
@jwt_required()
def get_jitter(log_id):
    """获取性能抖动数据"""
    try:
        # 先检查日志是否存在
        log = TestLog.query.get(log_id)
        if not log:
            return error_response('日志不存在', 404)

        # 获取查询参数
        metric_type = request.args.get('metric_type', 'iops')

        # 调用日志收集器获取性能抖动数据
        jitter_data = log_collector.get_performance_jitter(log_id, metric_type)
        
        return success_response(
            jitter_data,
            message="获取性能抖动数据成功"
        )
    except Exception as e:
        return error_response(str(e), 500)

@logs_bp.route('/<int:log_id>/fio-results', methods=['GET'])
@jwt_required()
def get_fio_results(log_id):
    """获取FIO日志解析结果"""
    try:
        # 查询日志
        log = TestLog.query.get(log_id)
        if not log:
            return error_response('日志不存在', 404)
        
        # 检查日志类型
        if log.log_type != 'fio':
            return error_response('该日志不是FIO日志', 400)
        
        # 检查日志文件是否存在
        import os
        if not os.path.exists(log.log_path):
            return error_response('日志文件不存在', 404)
        
        # 解析fio日志
        fio_results = log_collector._parse_fio_log(log.log_path)
        
        return success_response(
            fio_results,
            message="获取FIO日志解析结果成功"
        )
    except Exception as e:
        return error_response(str(e), 500)

@logs_bp.route('/task/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task_logs(task_id):
    """获取测试任务的所有日志"""
    try:
        # 获取查询参数
        node_id = request.args.get('node_id')
        
        # 将node_id转换为整数类型（如果提供了）
        if node_id is not None:
            node_id = int(node_id)
        
        # 调用日志收集器获取任务日志
        logs = log_collector.get_task_logs(task_id, node_id=node_id)
        
        return success_response(
            logs,
            message="获取测试任务日志成功"
        )
    except Exception as e:
        return error_response(str(e), 500)

@logs_bp.route('/<int:log_id>', methods=['GET'])
@jwt_required()
def get_log(log_id):
    """获取日志详情"""
    try:
        import os

        # 查询日志
        log = TestLog.query.get(log_id)
        if not log:
            return error_response('日志不存在', 404)

        # 获取日志基本信息
        log_data = log.to_dict()

        # 读取日志文件内容
        log_content = None
        if log.log_path and os.path.exists(log.log_path):
            try:
                # 限制读取文件大小，避免内存溢出（最大10MB）
                max_size = 10 * 1024 * 1024  # 10MB
                file_size = os.path.getsize(log.log_path)

                if file_size <= max_size:
                    with open(log.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()
                else:
                    # 文件太大，只读取前10MB
                    with open(log.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read(max_size)
                    log_content += f'\n\n... (文件过大，仅显示前{max_size // 1024 // 1024}MB内容，完整内容请下载查看)'
            except Exception as e:
                logger.error(f"读取日志文件失败: {e}")
                log_content = f"无法读取日志文件内容: {str(e)}"
        else:
            log_content = "日志文件不存在或路径无效"

        log_data['log_content'] = log_content

        return success_response(
            log_data,
            message="获取日志详情成功"
        )
    except Exception as e:
        logger.error(f"获取日志详情失败: {e}")
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

@logs_bp.route('/<int:log_id>/iostat-jitter', methods=['GET'])
@jwt_required()
def get_iostat_jitter(log_id):
    """获取IOSTAT指标的抖动计算结果"""
    try:
        # 先检查日志是否存在
        log = TestLog.query.get(log_id)
        if not log:
            return error_response('日志不存在', 404)

        # 获取iostat指标
        metrics = IOStatMetric.query.filter_by(test_log_id=log_id).order_by(IOStatMetric.collection_time).all()
        metrics_dict = [metric.to_dict() for metric in metrics]
        
        # 计算不同类型的抖动
        iops_jitter = log_collector.calculate_jitter(metrics_dict, 'iops')
        bandwidth_jitter = log_collector.calculate_jitter(metrics_dict, 'bandwidth')
        latency_jitter = log_collector.calculate_jitter(metrics_dict, 'latency')
        
        return success_response(
            {
                'iops': iops_jitter,
                'bandwidth': bandwidth_jitter,
                'latency': latency_jitter
            },
            message="获取IOSTAT指标抖动计算结果成功"
        )
    except Exception as e:
        return error_response(str(e), 500)

@logs_bp.route('/task/<int:task_id>/realtime-metrics', methods=['GET'])
@jwt_required()
def get_realtime_metrics(task_id):
    """获取实时FIO日志指标数据"""
    try:
        # 获取查询参数
        node_ids = request.args.get('node_ids')
        devices = request.args.get('devices')
        
        # 解析节点ID列表
        node_id_list = []
        if node_ids:
            node_id_list = [int(nid) for nid in node_ids.split(',')]
        
        # 解析设备列表
        device_list = []
        if devices:
            device_list = devices.split(',')
        
        # 调用日志收集器获取实时指标数据
        realtime_metrics = log_collector.get_realtime_metrics(task_id, node_id_list, device_list)
        
        return success_response(
            realtime_metrics,
            message="获取实时FIO日志指标数据成功"
        )
    except Exception as e:
        return error_response(str(e), 500)
