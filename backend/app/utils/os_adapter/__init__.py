"""
OS Adapter - 操作系统适配层

提供跨Linux发行版的统一接口，支持华为欧拉、CentOS、Ubuntu等系统
"""

from .os_info import OSInfo, OSInfoDetector
from .base import BaseOSAdapter
from .factory import OSAdapterFactory

__all__ = [
    'OSInfo',
    'OSInfoDetector',
    'BaseOSAdapter',
    'OSAdapterFactory',
]
