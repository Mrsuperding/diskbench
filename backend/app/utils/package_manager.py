"""
Package Manager - 包管理器抽象

提供跨包管理器的统一安装接口
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import logging


class BasePackageManager(ABC):
    """包管理器基类"""

    def __init__(self, ssh_client):
        """
        初始化包管理器

        Args:
            ssh_client: SSHClient实例
        """
        self.ssh_client = ssh_client
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def is_installed(self, package: str) -> bool:
        """检查包是否已安装"""
        pass

    @abstractmethod
    def install(self, packages: List[str]) -> Tuple[bool, str]:
        """安装包"""
        pass

    @abstractmethod
    def uninstall(self, packages: List[str]) -> Tuple[bool, str]:
        """卸载包"""
        pass

    @abstractmethod
    def update(self) -> Tuple[bool, str]:
        """更新包索引"""
        pass


class DnfPackageManager(BasePackageManager):
    """DNF包管理器（RHEL 8+, Fedora, EulerOS R10/HCE）"""

    def is_installed(self, package: str) -> bool:
        cmd = f"dnf list installed {package}"
        success, output = self.ssh_client.execute_command(cmd)
        return success and package in output

    def install(self, packages: List[str]) -> Tuple[bool, str]:
        package_list = ' '.join(packages)
        cmd = f"sudo dnf install -y {package_list}"
        self.logger.info(f"安装包: {package_list}")
        success, output = self.ssh_client.execute_command(cmd, timeout=300)
        if success:
            return True, f"Successfully installed {package_list}"
        return False, output

    def uninstall(self, packages: List[str]) -> Tuple[bool, str]:
        package_list = ' '.join(packages)
        cmd = f"sudo dnf remove -y {package_list}"
        success, output = self.ssh_client.execute_command(cmd, timeout=300)
        if success:
            return True, f"Successfully removed {package_list}"
        return False, output

    def update(self) -> Tuple[bool, str]:
        cmd = "sudo dnf check-update"
        success, output = self.ssh_client.execute_command(cmd, timeout=300)
        # check-update返回100表示有更新，0表示没有，1表示错误
        if success or "No packages marked" in output:
            return True, output
        return False, output


class YumPackageManager(BasePackageManager):
    """YUM包管理器（RHEL 7-, CentOS 7-, EulerOS R9）"""

    def is_installed(self, package: str) -> bool:
        cmd = f"yum list installed {package}"
        success, output = self.ssh_client.execute_command(cmd)
        return success and package in output

    def install(self, packages: List[str]) -> Tuple[bool, str]:
        package_list = ' '.join(packages)
        cmd = f"sudo yum install -y {package_list}"
        self.logger.info(f"安装包: {package_list}")
        success, output = self.ssh_client.execute_command(cmd, timeout=300)
        if success:
            return True, f"Successfully installed {package_list}"
        return False, output

    def uninstall(self, packages: List[str]) -> Tuple[bool, str]:
        package_list = ' '.join(packages)
        cmd = f"sudo yum remove -y {package_list}"
        success, output = self.ssh_client.execute_command(cmd, timeout=300)
        if success:
            return True, f"Successfully removed {package_list}"
        return False, output

    def update(self) -> Tuple[bool, str]:
        cmd = "sudo yum check-update"
        success, output = self.ssh_client.execute_command(cmd, timeout=300)
        if success or "No packages marked" in output:
            return True, output
        return False, output


class AptPackageManager(BasePackageManager):
    """APT包管理器（Debian, Ubuntu）"""

    def is_installed(self, package: str) -> bool:
        cmd = f"dpkg -l {package}"
        success, output = self.ssh_client.execute_command(cmd)
        return success and ('ii' in output.split('\n')[-1] if output else False)

    def install(self, packages: List[str]) -> Tuple[bool, str]:
        package_list = ' '.join(packages)
        # 先更新索引，再安装
        cmd = f"sudo apt-get update && sudo apt-get install -y {package_list}"
        self.logger.info(f"安装包: {package_list}")
        success, output = self.ssh_client.execute_command(cmd, timeout=300)
        if success:
            return True, f"Successfully installed {package_list}"
        return False, output

    def uninstall(self, packages: List[str]) -> Tuple[bool, str]:
        package_list = ' '.join(packages)
        cmd = f"sudo apt-get remove -y {package_list}"
        success, output = self.ssh_client.execute_command(cmd, timeout=300)
        if success:
            return True, f"Successfully removed {package_list}"
        return False, output

    def update(self) -> Tuple[bool, str]:
        cmd = "sudo apt-get update"
        success, output = self.ssh_client.execute_command(cmd, timeout=300)
        if success:
            return True, "Package index updated"
        return False, output


class ZypperPackageManager(BasePackageManager):
    """Zypper包管理器（SLES, openSUSE）"""

    def is_installed(self, package: str) -> bool:
        cmd = f"zypper info {package}"
        success, output = self.ssh_client.execute_command(cmd)
        return success and 'Installed: No' not in output if output else False

    def install(self, packages: List[str]) -> Tuple[bool, str]:
        package_list = ' '.join(packages)
        cmd = f"sudo zypper install -y {package_list}"
        self.logger.info(f"安装包: {package_list}")
        success, output = self.ssh_client.execute_command(cmd, timeout=300)
        if success:
            return True, f"Successfully installed {package_list}"
        return False, output

    def uninstall(self, packages: List[str]) -> Tuple[bool, str]:
        package_list = ' '.join(packages)
        cmd = f"sudo zypper remove -y {package_list}"
        success, output = self.ssh_client.execute_command(cmd, timeout=300)
        if success:
            return True, f"Successfully removed {package_list}"
        return False, output

    def update(self) -> Tuple[bool, str]:
        cmd = "sudo zypper refresh"
        success, output = self.ssh_client.execute_command(cmd, timeout=300)
        if success:
            return True, "Package repository refreshed"
        return False, output


class PackageManager:
    """包管理器工厂"""

    _MANAGERS = {
        'dnf': DnfPackageManager,
        'yum': YumPackageManager,
        'apt': AptPackageManager,
        'zypper': ZypperPackageManager,
    }

    @classmethod
    def get_manager(cls, ssh_client, package_manager: str = None, os_info=None) -> BasePackageManager:
        """
        获取包管理器实例

        Args:
            ssh_client: SSHClient实例
            package_manager: 包管理器名称（'dnf', 'yum', 'apt', 'zypper'）
            os_info: OSInfo对象（如果不知道package_manager可以传入）

        Returns:
            对应的包管理器实例
        """
        if package_manager is None and os_info is not None:
            package_manager = os_info.package_manager

        manager_class = cls._MANAGERS.get(package_manager.lower())
        if manager_class:
            return manager_class(ssh_client)

        raise ValueError(f"Unsupported package manager: {package_manager}")

    @classmethod
    def detect_and_get_manager(cls, ssh_client) -> Tuple[BasePackageManager, str]:
        """
        检测可用的包管理器并返回

        Returns:
            (包管理器实例, 包管理器名称)
        """
        # 按优先级检测
        for pm_name in ['dnf', 'yum', 'apt', 'zypper']:
            cmd = f"which {pm_name}"
            success, _ = ssh_client.execute_command(cmd)
            if success:
                manager_class = cls._MANAGERS.get(pm_name)
                if manager_class:
                    return manager_class(ssh_client), pm_name

        # 默认使用yum
        return YumPackageManager(ssh_client), 'yum'
