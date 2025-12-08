from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from app.models import db, TestTask, TestResult, Node, User
from app.utils.responses import success_response, error_response

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """获取仪表盘统计数据"""
    try:
        # 获取最近7天的数据
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # 任务统计
        total_tasks = TestTask.query.count()
        pending_tasks = TestTask.query.filter_by(status='pending').count()
        running_tasks = TestTask.query.filter_by(status='running').count()
        completed_tasks = TestTask.query.filter_by(status='completed').count()
        failed_tasks = TestTask.query.filter_by(status='failed').count()
        
        # 最近7天完成的任务数
        recent_completed_tasks = TestTask.query.filter(
            TestTask.status == 'completed',
            TestTask.completed_at >= seven_days_ago
        ).count()
        
        # 节点统计
        total_nodes = Node.query.count()
        online_nodes = Node.query.filter_by(status='online').count()
        offline_nodes = Node.query.filter_by(status='offline').count()
        
        # 测试结果统计
        total_results = TestResult.query.count()
        
        # 最近7天的测试结果数
        recent_results = TestResult.query.filter(
            TestResult.created_at >= seven_days_ago
        ).count()
        
        # 用户统计
        total_users = User.query.count()
        
        stats = {
            'tasks': {
                'total': total_tasks,
                'pending': pending_tasks,
                'running': running_tasks,
                'completed': completed_tasks,
                'failed': failed_tasks,
                'recent_completed': recent_completed_tasks
            },
            'nodes': {
                'total': total_nodes,
                'online': online_nodes,
                'offline': offline_nodes
            },
            'results': {
                'total': total_results,
                'recent': recent_results
            },
            'users': {
                'total': total_users
            }
        }
        
        return success_response(stats)
    except Exception as e:
        return error_response(f'获取仪表盘统计数据失败: {str(e)}', 500)

@dashboard_bp.route('/recent-tasks', methods=['GET'])
@jwt_required()
def get_recent_tasks():
    """获取最近的任务列表"""
    try:
        recent_tasks = TestTask.query.order_by(
            TestTask.created_at.desc()
        ).limit(10).all()
        
        return success_response([task.to_dict() for task in recent_tasks])
    except Exception as e:
        return error_response(f'获取最近任务列表失败: {str(e)}', 500)

@dashboard_bp.route('/recent-results', methods=['GET'])
@jwt_required()
def get_recent_results():
    """获取最近的测试结果列表"""
    try:
        recent_results = TestResult.query.order_by(
            TestResult.created_at.desc()
        ).limit(10).all()
        
        return success_response([result.to_dict() for result in recent_results])
    except Exception as e:
        return error_response(f'获取最近测试结果列表失败: {str(e)}', 500)

@dashboard_bp.route('/node-status', methods=['GET'])
@jwt_required()
def get_node_status():
    """获取节点状态统计"""
    try:
        nodes = Node.query.all()
        status_counts = {}
        
        for node in nodes:
            status = node.status
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
        
        return success_response(status_counts)
    except Exception as e:
        return error_response(f'获取节点状态统计失败: {str(e)}', 500)