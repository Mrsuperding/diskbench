"""
统一的时间工具模块

解决 datetime.utcnow() 在 Python 3.12+ 废弃的问题
所有需要获取当前 UTC 时间的地方都应该使用本模块的函数
"""

from datetime import datetime, timezone


def utc_now():
    """
    获取当前 UTC 时间（timezone-aware）

    Returns:
        datetime: 当前 UTC 时间，带时区信息

    Example:
        >>> from app.utils.datetime_utils import utc_now
        >>> now = utc_now()
        >>> now.isoformat()
        '2024-01-15T10:30:00+00:00'
    """
    return datetime.now(timezone.utc)


def utc_now_naive():
    """
    获取当前 UTC 时间（naive，无时区信息）

    注意：仅在需要兼容旧代码时使用，新增代码应使用 utc_now()

    Returns:
        datetime: 当前 UTC 时间，无时区信息
    """
    return datetime.utcnow()


def local_now():
    """
    获取当前本地时间（timezone-aware）

    Returns:
        datetime: 当前本地时间，带时区信息
    """
    return datetime.now()
