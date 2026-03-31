"""监控配置管理API"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db
from app.models.monitoring_config import MonitoringConfig
from app.models.environment_space import EnvironmentSpace
from app.utils.responses import success_response, error_response

monitoring_config_bp = Blueprint('monitoring_config', __name__)


@monitoring_config_bp.route('/global', methods=['GET'])
@jwt_required()
def get_global_config():
    """获取全局监控配置"""
    try:
        config = MonitoringConfig.get_global_config()
        return success_response(config.to_dict())
    except Exception as e:
        return error_response(f'获取全局配置失败: {str(e)}', 500)


@monitoring_config_bp.route('/environment/<int:space_id>', methods=['GET'])
@jwt_required()
def get_environment_config(space_id):
    """获取环境监控配置"""
    try:
        # 验证环境空间是否存在
        space = EnvironmentSpace.query.get(space_id)
        if not space:
            return error_response('环境空间不存在', 404)

        # 获取配置（如果不存在则返回全局配置）
        config = MonitoringConfig.get_config_for_environment(space_id)
        return success_response(config.to_dict())
    except Exception as e:
        return error_response(f'获取环境配置失败: {str(e)}', 500)


@monitoring_config_bp.route('/environment/<int:space_id>', methods=['PUT'])
@jwt_required()
def update_environment_config(space_id):
    """更新环境监控配置（仅所有者）"""
    try:
        current_user_id = get_jwt_identity()

        # 验证环境空间是否存在及权限
        space = EnvironmentSpace.query.get(space_id)
        if not space:
            return error_response('环境空间不存在', 404)

        # 权限检查：只有所有者可以更新配置
        if space.owner_id != current_user_id:
            return error_response('没有权限更新此环境空间的配置', 403)

        data = request.get_json()

        # 查找或创建配置
        config = MonitoringConfig.query.filter_by(environment_space_id=space_id).first()
        if not config:
            config = MonitoringConfig(environment_space_id=space_id)
            db.session.add(config)

        # 更新配置字段
        if 'collection_interval' in data:
            interval = data['collection_interval']
            if interval < 60 or interval > 3600:
                return error_response('采集间隔必须在60秒到3600秒之间', 400)
            config.collection_interval = interval

        if 'retention_period' in data:
            period = data['retention_period']
            if period < 1 or period > 90:
                return error_response('保留期必须在1天到90天之间', 400)
            config.retention_period = period

        if 'enabled' in data:
            config.enabled = data['enabled']

        db.session.commit()
        return success_response(config.to_dict(), '监控配置更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新监控配置失败: {str(e)}', 500)


@monitoring_config_bp.route('/global', methods=['PUT'])
@jwt_required()
def update_global_config():
    """更新全局监控配置（需要管理员权限）"""
    try:
        # TODO: 添加管理员权限检查
        data = request.get_json()

        # 获取或创建全局配置
        config = MonitoringConfig.get_global_config()

        # 更新配置字段
        if 'collection_interval' in data:
            interval = data['collection_interval']
            if interval < 60 or interval > 3600:
                return error_response('采集间隔必须在60秒到3600秒之间', 400)
            config.collection_interval = interval

        if 'retention_period' in data:
            period = data['retention_period']
            if period < 1 or period > 90:
                return error_response('保留期必须在1天到90天之间', 400)
            config.retention_period = period

        if 'enabled' in data:
            config.enabled = data['enabled']

        db.session.commit()
        return success_response(config.to_dict(), '全局监控配置更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新全局监控配置失败: {str(e)}', 500)
