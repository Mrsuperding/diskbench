from flask import jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """404错误处理"""
        return jsonify({
            'code': 404,
            'message': '资源未找到',
            'success': False,
            'data': None
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        """405错误处理"""
        return jsonify({
            'code': 405,
            'message': '方法不被允许',
            'success': False,
            'data': None
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理"""
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'success': False,
            'data': None
        }), 500
    
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        """数据库错误处理"""
        logger.error(f"Database error: {error}")
        return jsonify({
            'code': 500,
            'message': '数据库操作失败',
            'success': False,
            'data': None
        }), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """未预期的错误处理"""
        logger.error(f"Unexpected error: {error}")
        return jsonify({
            'code': 500,
            'message': '发生未预期的错误',
            'success': False,
            'data': None
        }), 500