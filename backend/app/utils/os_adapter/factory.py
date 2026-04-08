"""
OS Adapter Factory - 操作系统适配器工厂

根据检测到的OS信息创建对应的适配器实例
"""

from typing import Optional
from .base import BaseOSAdapter
from .os_info import OSInfo


class OSAdapterFactory:
    """OS适配器工厂"""

    # OS名称到适配器类的映射
    _ADAPTERS = {}

    @classmethod
    def register(cls, os_names: list, adapter_class):
        """注册适配器"""
        for name in os_names:
            cls._ADAPTERS[name.lower()] = adapter_class

    @classmethod
    def create(cls, os_info: OSInfo, ssh_client=None) -> BaseOSAdapter:
        """
        根据OS信息创建适配器实例

        Args:
            os_info: OSInfo对象
            ssh_client: SSHClient实例

        Returns:
            对应的OS适配器实例
        """
        # 优先按版本创建特定适配器
        adapter = cls._create_version_specific_adapter(os_info, ssh_client)
        if adapter:
            return adapter

        # 按OS名称创建适配器
        adapter_class = cls._ADAPTERS.get(os_info.name.lower())
        if adapter_class:
            return adapter_class(os_info, ssh_client)

        # 默认使用通用适配器
        from .euleros import EulerOSAdapter
        return EulerOSAdapter(os_info, ssh_client)

    @classmethod
    def _create_version_specific_adapter(cls, os_info: OSInfo, ssh_client):
        """创建版本特定的适配器"""
        from .euleros import (
            EulerOSAdapter, EulerOSR10Adapter,
            EulerOSR9Adapter, EulerOSHCEAdapter
        )

        if os_info.name == 'EulerOS':
            if os_info.version == 'R10':
                return EulerOSR10Adapter(os_info, ssh_client)
            elif os_info.version == 'R9':
                return EulerOSR9Adapter(os_info, ssh_client)
            elif os_info.version == 'HCE':
                return EulerOSHCEAdapter(os_info, ssh_client)

        return None

    @classmethod
    def get_supported_os(cls) -> list:
        """获取支持的OS列表"""
        return list(set(cls._ADAPTERS.keys()))


# 注册默认适配器
def _register_default_adapters():
    """注册默认适配器"""
    from . import euleros, centos, ubuntu, debian, fedora

    # EulerOS
    OSAdapterFactory.register(['EulerOS', 'euleros', 'huawei euleros'], euleros.EulerOSAdapter)

    # CentOS/RHEL
    OSAdapterFactory.register(['CentOS', 'centos'], centos.CentOSAdapter)
    OSAdapterFactory.register(['RHEL', 'rhel', 'red hat enterprise linux'], centos.CentOSAdapter)

    # Ubuntu
    OSAdapterFactory.register(['Ubuntu', 'ubuntu'], ubuntu.UbuntuAdapter)

    # Debian
    OSAdapterFactory.register(['Debian', 'debian'], debian.DebianAdapter)

    # Fedora
    OSAdapterFactory.register(['Fedora', 'fedora'], fedora.FedoraAdapter)


# 注册
_register_default_adapters()
