"""环境空间管理API"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from app.models import db
from app.models.environment_space import EnvironmentSpace
from app.models.node import Node
from app.models.system_metric import SystemMetric
from app.utils.responses import success_response, error_response

environment_spaces_bp = Blueprint('environment_spaces', __name__)


@environment_spaces_bp.route('', methods=['GET'])
@jwt_required()
def get_environment_spaces():
    """获取环境空间列表（用户拥有的）"""
    try:
        current_user_id = get_jwt_identity()
        # 获取用户拥有的所有环境空间
        spaces = EnvironmentSpace.get_by_owner(current_user_id)
        return success_response([space.to_dict() for space in spaces])
    except Exception as e:
        return error_response(f'获取环境空间列表失败: {str(e)}', 500)


@environment_spaces_bp.route('/<int:space_id>', methods=['GET'])
@jwt_required()
def get_environment_space(space_id):
    """获取环境空间详情"""
    try:
        space = EnvironmentSpace.query.get(space_id)
        if not space:
            return error_response('环境空间不存在', 404)
        return success_response(space.to_dict())
    except Exception as e:
        return error_response(f'获取环境空间详情失败: {str(e)}', 500)


@environment_spaces_bp.route('', methods=['POST'])
@jwt_required()
def create_environment_space():
    """创建环境空间"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # 验证必需字段
        if not data.get('name'):
            return error_response('环境空间名称是必需的', 400)

        # 检查名称是否已存在
        if EnvironmentSpace.find_by_name(data['name']):
            return error_response('环境空间名称已存在', 400)

        space = EnvironmentSpace(
            name=data['name'],
            description=data.get('description', ''),
            owner_id=current_user_id
        )

        db.session.add(space)
        db.session.commit()

        return success_response(space.to_dict(), '环境空间创建成功', 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'创建环境空间失败: {str(e)}', 500)


@environment_spaces_bp.route('/<int:space_id>', methods=['PUT'])
@jwt_required()
def update_environment_space(space_id):
    """更新环境空间（仅所有者）"""
    try:
        current_user_id = get_jwt_identity()
        space = EnvironmentSpace.query.get(space_id)

        if not space:
            return error_response('环境空间不存在', 404)

        # 权限检查：只有所有者可以更新
        if space.owner_id != current_user_id:
            return error_response('没有权限更新此环境空间', 403)

        data = request.get_json()

        if 'name' in data:
            # 检查新名称是否与其他空间冲突
            existing = EnvironmentSpace.find_by_name(data['name'])
            if existing and existing.id != space_id:
                return error_response('环境空间名称已存在', 400)
            space.name = data['name']

        if 'description' in data:
            space.description = data['description']

        if 'is_active' in data:
            space.is_active = data['is_active']

        db.session.commit()
        return success_response(space.to_dict(), '环境空间更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新环境空间失败: {str(e)}', 500)


@environment_spaces_bp.route('/<int:space_id>', methods=['DELETE'])
@jwt_required()
def delete_environment_space(space_id):
    """删除环境空间（仅所有者）"""
    try:
        current_user_id = get_jwt_identity()
        space = EnvironmentSpace.query.get(space_id)

        if not space:
            return error_response('环境空间不存在', 404)

        # 权限检查：只有所有者可以删除
        if space.owner_id != current_user_id:
            return error_response('没有权限删除此环境空间', 403)

        # 将关联的节点的environment_space_id设为NULL
        for node in space.nodes:
            node.environment_space_id = None

        db.session.delete(space)
        db.session.commit()

        return success_response(None, '环境空间删除成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除环境空间失败: {str(e)}', 500)


@environment_spaces_bp.route('/<int:space_id>/nodes', methods=['GET'])
@jwt_required()
def get_environment_nodes(space_id):
    """获取环境内的所有节点及其最新指标"""
    try:
        space = EnvironmentSpace.query.get(space_id)
        if not space:
            return error_response('环境空间不存在', 404)

        nodes_data = []
        for node in space.nodes:
            node_dict = node.to_dict()

            # 获取最新的系统指标
            latest_cpu = SystemMetric.query.filter_by(
                node_id=node.id,
                metric_name='cpu_usage'
            ).order_by(SystemMetric.collection_time.desc()).first()

            latest_memory = SystemMetric.query.filter_by(
                node_id=node.id,
                metric_name='memory_usage'
            ).order_by(SystemMetric.collection_time.desc()).first()

            latest_connection = SystemMetric.query.filter_by(
                node_id=node.id,
                metric_name='is_connected'
            ).order_by(SystemMetric.collection_time.desc()).first()

            # 添加最新指标到节点数据
            node_dict['latest_metrics'] = {
                'cpu_usage': latest_cpu.metric_value if latest_cpu else None,
                'memory_usage': latest_memory.metric_value if latest_memory else None,
                'is_connected': bool(latest_connection.metric_value) if latest_connection else None,
                'last_update': latest_cpu.collection_time.isoformat() if latest_cpu else None
            }

            nodes_data.append(node_dict)

        return success_response(nodes_data)
    except Exception as e:
        return error_response(f'获取环境节点列表失败: {str(e)}', 500)


@environment_spaces_bp.route('/<int:space_id>/nodes/<int:node_id>', methods=['POST'])
@jwt_required()
def add_node_to_environment(space_id, node_id):
    """将节点添加到环境"""
    try:
        current_user_id = get_jwt_identity()
        space = EnvironmentSpace.query.get(space_id)

        if not space:
            return error_response('环境空间不存在', 404)

        # 权限检查：只有所有者可以添加节点
        if space.owner_id != current_user_id:
            return error_response('没有权限操作此环境空间', 403)

        node = Node.query.get(node_id)
        if not node:
            return error_response('节点不存在', 404)

        # 更新节点的环境空间
        node.environment_space_id = space_id
        db.session.commit()

        return success_response(node.to_dict(), '节点已添加到环境空间')
    except Exception as e:
        db.session.rollback()
        return error_response(f'添加节点失败: {str(e)}', 500)


@environment_spaces_bp.route('/<int:space_id>/nodes/<int:node_id>', methods=['DELETE'])
@jwt_required()
def remove_node_from_environment(space_id, node_id):
    """从环境中移除节点"""
    try:
        current_user_id = get_jwt_identity()
        space = EnvironmentSpace.query.get(space_id)

        if not space:
            return error_response('环境空间不存在', 404)

        # 权限检查：只有所有者可以移除节点
        if space.owner_id != current_user_id:
            return error_response('没有权限操作此环境空间', 403)

        node = Node.query.get(node_id)
        if not node:
            return error_response('节点不存在', 404)

        if node.environment_space_id != space_id:
            return error_response('节点不属于此环境空间', 400)

        # 将节点的环境空间设为NULL
        node.environment_space_id = None
        db.session.commit()

        return success_response(None, '节点已从环境空间移除')
    except Exception as e:
        db.session.rollback()
        return error_response(f'移除节点失败: {str(e)}', 500)


@environment_spaces_bp.route('/<int:space_id>/metrics/realtime', methods=['GET'])
@jwt_required()
def get_environment_realtime_metrics(space_id):
    """获取环境内所有节点的实时指标"""
    try:
        space = EnvironmentSpace.query.get(space_id)
        if not space:
            return error_response('环境空间不存在', 404)

        realtime_data = []
        for node in space.nodes:
            # 获取最新指标
            latest_metrics = {}
            for metric_name in ['cpu_usage', 'memory_usage', 'is_connected']:
                metric = SystemMetric.query.filter_by(
                    node_id=node.id,
                    metric_name=metric_name
                ).order_by(SystemMetric.collection_time.desc()).first()

                if metric:
                    latest_metrics[metric_name] = {
                        'value': metric.metric_value,
                        'unit': metric.metric_unit,
                        'time': metric.collection_time.isoformat()
                    }

            realtime_data.append({
                'node_id': node.id,
                'node_name': node.name,
                'metrics': latest_metrics
            })

        return success_response(realtime_data)
    except Exception as e:
        return error_response(f'获取实时指标失败: {str(e)}', 500)


@environment_spaces_bp.route('/<int:space_id>/metrics/history', methods=['GET'])
@jwt_required()
def get_environment_history_metrics(space_id):
    """获取环境内所有节点的历史指标"""
    try:
        space = EnvironmentSpace.query.get(space_id)
        if not space:
            return error_response('环境空间不存在', 404)

        # 获取查询参数
        hours = request.args.get('hours', 1, type=int)  # 默认最近1小时
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # 获取环境内所有节点的历史数据
        metrics = SystemMetric.get_metrics_by_environment(
            space_id,
            start_time,
            end_time
        )

        # 按节点和指标名称组织数据
        history_data = {}
        for metric in metrics:
            node_key = f"node_{metric.node_id}"
            if node_key not in history_data:
                node = Node.query.get(metric.node_id)
                history_data[node_key] = {
                    'node_id': metric.node_id,
                    'node_name': node.name if node else f'Unknown-{metric.node_id}',
                    'metrics': {}
                }

            metric_name = metric.metric_name
            if metric_name not in history_data[node_key]['metrics']:
                history_data[node_key]['metrics'][metric_name] = []

            history_data[node_key]['metrics'][metric_name].append({
                'value': metric.metric_value,
                'unit': metric.metric_unit,
                'time': metric.collection_time.isoformat()
            })

        return success_response(list(history_data.values()))
    except Exception as e:
        return error_response(f'获取历史指标失败: {str(e)}', 500)


@environment_spaces_bp.route('/<int:space_id>/metrics/collect', methods=['POST'])
@jwt_required()
def collect_space_metrics(space_id):
    """手动触发环境空间内所有节点的监控数据采集"""
    try:
        space = EnvironmentSpace.query.get(space_id)
        if not space:
            return error_response('环境空间不存在', 404)

        from app.services.metric_collector import MetricCollector

        success_count = 0
        failed_count = 0
        nodes = space.nodes

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
        }, f'采集完成: 成功 {success_count}, 失败 {failed_count}')
    except Exception as e:
        db.session.rollback()
        return error_response(f'采集监控数据失败: {str(e)}', 500)

