from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from app.models import db, Node
from app.models.system_metric import SystemMetric
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


@nodes_bp.route('/<int:node_id>/metrics', methods=['GET'])
@jwt_required()
def get_node_metrics(node_id):
    """获取节点最新监控数据"""
    try:
        node = Node.query.get(node_id)
        if not node:
            return error_response('节点不存在', 404)

        # 获取最新的各项指标
        metric_names = ['cpu_usage', 'memory_usage', 'disk_usage', 'network_rx', 'network_tx',
                       'load_average_1min', 'load_average_5min', 'load_average_15min']
        metrics_data = {}

        for metric_name in metric_names:
            metric = SystemMetric.query.filter_by(
                node_id=node_id,
                metric_name=metric_name
            ).order_by(SystemMetric.collection_time.desc()).first()

            if metric:
                metrics_data[metric_name] = metric.metric_value
                if not metrics_data.get('updated_at'):
                    metrics_data['updated_at'] = metric.collection_time.strftime('%Y-%m-%d %H:%M:%S')

        # 将load_average的三个指标合并成数组
        if all(key in metrics_data for key in ['load_average_1min', 'load_average_5min', 'load_average_15min']):
            metrics_data['load_average'] = [
                metrics_data.pop('load_average_1min'),
                metrics_data.pop('load_average_5min'),
                metrics_data.pop('load_average_15min')
            ]

        return success_response(metrics_data)
    except Exception as e:
        return error_response(f'获取节点监控数据失败: {str(e)}', 500)


@nodes_bp.route('/<int:node_id>/metrics/history', methods=['GET'])
@jwt_required()
def get_node_metrics_history(node_id):
    """获取节点历史监控数据"""
    try:
        node = Node.query.get(node_id)
        if not node:
            return error_response('节点不存在', 404)

        # 获取查询参数
        hours = request.args.get('hours', 1, type=int)  # 默认最近1小时
        metric_name = request.args.get('metric_name')  # 可选：指定指标名称

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # 构建查询
        query = SystemMetric.query.filter(
            SystemMetric.node_id == node_id,
            SystemMetric.collection_time >= start_time,
            SystemMetric.collection_time <= end_time
        )

        if metric_name:
            query = query.filter(SystemMetric.metric_name == metric_name)

        metrics = query.order_by(SystemMetric.collection_time.asc()).all()

        # 按指标名称组织数据
        history_data = {}
        for metric in metrics:
            if metric.metric_name not in history_data:
                history_data[metric.metric_name] = []

            history_data[metric.metric_name].append({
                'value': metric.metric_value,
                'unit': metric.metric_unit,
                'time': metric.collection_time.isoformat()
            })

        return success_response(history_data)
    except Exception as e:
        return error_response(f'获取节点历史监控数据失败: {str(e)}', 500)


@nodes_bp.route('/<int:node_id>/metrics/collect', methods=['POST'])
@jwt_required()
def collect_node_metrics(node_id):
    """手动触发节点监控数据采集"""
    try:
        node = Node.query.get(node_id)
        if not node:
            return error_response('节点不存在', 404)

        from app.services.metric_collector import MetricCollector

        # 采集并保存监控数据
        metrics = MetricCollector.collect_node_metrics(node_id)
        MetricCollector.save_metrics(node_id, metrics)

        return success_response(metrics, '监控数据采集成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'采集监控数据失败: {str(e)}', 500)


@nodes_bp.route('/metrics/collect-all', methods=['POST'])
@jwt_required()
def collect_all_metrics():
    """手动触发所有节点监控数据采集"""
    try:
        nodes = Node.query.all()
        from app.services.metric_collector import MetricCollector

        success_count = 0
        failed_count = 0

        for node in nodes:
            try:
                metrics = MetricCollector.collect_node_metrics(node.id)
                MetricCollector.save_metrics(node.id, metrics)
                success_count += 1
            except Exception as e:
                failed_count += 1
                print(f'采集节点 {node.id} 指标失败: {e}')

        return success_response({
            'total': len(nodes),
            'success': success_count,
            'failed': failed_count
        }, f'批量采集完成: 成功 {success_count}, 失败 {failed_count}')
    except Exception as e:
        db.session.rollback()
        return error_response(f'批量采集监控数据失败: {str(e)}', 500)