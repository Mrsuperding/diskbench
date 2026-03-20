#!/usr/bin/env python3
"""装饰器模块"""
import functools


def with_app_context(app):
    """
    应用上下文装饰器
    用于在多线程操作中创建应用上下文
    
    Args:
        app: Flask应用实例
    
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with app.app_context():
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # 重新抛出异常，让调用者处理
                    raise
        return wrapper
    return decorator
