"""
EulerOS Adapter - 华为欧拉操作系统适配器

支持 EulerOS R10, R9, HCE (ARM)
基于RHEL系列，兼容CentOS/RHEL命令
"""

from typing import List, Tuple
from .base import BaseOSAdapter


class EulerOSAdapter(BaseOSAdapter):
    """华为欧拉操作系统适配器"""

    # EulerOS版本对应的包管理器
    VERSION_PACKAGE_MANAGER = {
        'R10': 'dnf',  # EulerOS R10 基于RHEL 8，使用dnf
        'R9': 'yum',   # EulerOS R9 基于RHEL 7，使用yum
        'HCE': 'dnf',  # HCE基于RHEL 8，使用dnf
    }

    def __init__(self, os_info, ssh_client=None):
        super().__init__(os_info, ssh_client)
        self._package_manager = None

    def detect_package_manager(self) -> str:
        """检测EulerOS的包管理器"""
        if self._package_manager:
            return self._package_manager

        # 优先使用dnf（EulerOS R10和HCE）
        if self.os_info.has_dnf:
            self._package_manager = 'dnf'
        elif self.os_info.has_yum:
            self._package_manager = 'yum'
        else:
            # 根据版本推断
            self._package_manager = self.VERSION_PACKAGE_MANAGER.get(
                self.os_info.version, 'yum'
            )

        return self._package_manager

    def install_packages(self, packages: List[str]) -> Tuple[bool, str]:
        """安装软件包"""
        if self.ssh_client is None:
            return False, "SSH client not available"

        pm = self.detect_package_manager()
        package_list = ' '.join(packages)

        if pm == 'dnf':
            cmd = f"sudo dnf install -y {package_list}"
        elif pm == 'yum':
            cmd = f"sudo yum install -y {package_list}"
        else:
            return False, f"Unsupported package manager: {pm}"

        self.log('info', f"安装包: {package_list} (使用{pm})")
        success, output = self.ssh_client.execute_command(cmd)

        if success:
            return True, f"Successfully installed {package_list}"
        else:
            return False, f"Failed to install {package_list}: {output}"

    # ==================== 系统命令实现 ====================

    def get_hostname_cmd(self) -> str:
        """获取主机名命令"""
        return "hostname"

    def get_kernel_cmd(self) -> str:
        """获取内核版本命令"""
        return "uname -r"

    def get_cpu_count_cmd(self) -> str:
        """获取CPU核心数命令"""
        return "nproc"

    def get_memory_cmd(self) -> str:
        """获取内存信息命令（返回字节单位）"""
        return "free -b | grep Mem | awk '{print $2}'"

    def get_disk_space_cmd(self, path: str = '/') -> str:
        """获取磁盘空间命令"""
        # 使用df -B1获取字节单位
        return f"df -B1 {path} | tail -1 | awk '{{print $2}}'"

    def get_uptime_cmd(self) -> str:
        """获取运行时间命令"""
        return "uptime -s"

    # ==================== 系统日志命令实现 ====================

    def get_system_log_cmd(self, lines: int = 200) -> str:
        """
        获取系统日志命令

        EulerOS可能有systemd也可能没有，根据has_systemd决定：
        - 有systemd: 使用journalctl
        - 无systemd: 使用/var/log/messages或直接读取日志文件
        """
        if self.os_info.has_systemd:
            return f"journalctl -n {lines}"
        else:
            # EulerOS R9等老版本可能没有systemd
            # 尝试读取传统的日志文件
            return f"tail -n {lines} /var/log/messages"

    def get_dmesg_cmd(self, lines: int = 200) -> str:
        """
        获取dmesg命令

        注意: EulerOS的dmesg可能不支持-T参数（显示人类可读时间）
        使用基本dmesg命令
        """
        # 直接使用dmesg，不使用-T参数（某些版本不支持）
        return f"dmesg | tail -n {lines}"

    # ==================== 监控工具命令实现 ====================

    def get_iostat_cmd(self, interval: int = 1, device: str = None) -> str:
        """
        获取iostat命令

        iostat -xdm: 扩展模式，磁盘为单位，MB为单位
        """
        cmd = f"iostat -xdm {interval}"
        if device:
            cmd += f" {device}"
        return cmd

    def get_mpstat_cmd(self, interval: int = 1) -> str:
        """获取mpstat命令"""
        return f"mpstat {interval} 1"

    def get_free_cmd(self) -> str:
        """获取free命令"""
        return "free -h"

    def get_netstat_cmd(self) -> str:
        """获取netstat命令"""
        # EulerOS可能没有netstat，使用ss作为替代
        return "ss -s || netstat -ant"

    # ==================== 进程管理命令实现 ====================

    def get_process_list_cmd(self) -> str:
        """获取进程列表命令"""
        return "ps aux"

    def kill_process_cmd(self, pid: int, signal: int = 15) -> str:
        """终止进程命令"""
        return f"kill -{signal} {pid}"

    # ==================== 文件操作命令实现 ====================

    def get_file_size_cmd(self, path: str) -> str:
        """获取文件大小命令"""
        return f"stat -c%s {path}"

    def get_file_content_cmd(self, path: str, lines: int = None) -> str:
        """获取文件内容命令"""
        if lines:
            return f"head -n {lines} {path}"
        return f"cat {path}"

    # ==================== FIO相关命令 ====================

    def get_fio_stop_cmd(self, pattern: str = "fio") -> str:
        """停止fio进程"""
        # 使用pkill，支持模式匹配
        return f"pkill -f '{pattern}'"


class EulerOSR10Adapter(EulerOSAdapter):
    """华为欧拉R10适配器（基于RHEL 8）"""

    def __init__(self, os_info, ssh_client=None):
        super().__init__(os_info, ssh_client)
        self._package_manager = 'dnf'


class EulerOSR9Adapter(EulerOSAdapter):
    """华为欧拉R9适配器（基于RHEL 7）"""

    def __init__(self, os_info, ssh_client=None):
        super().__init__(os_info, ssh_client)
        self._package_manager = 'yum'

    def get_system_log_cmd(self, lines: int = 200) -> str:
        """
        EulerOS R9 使用journalctl或/var/log/messages

        R9版本通常有systemd，但某些定制版本可能没有
        """
        if self.os_info.has_systemd:
            return f"journalctl -n {lines}"
        else:
            # R9传统方式
            if self.os_info.has_yum:
                # 检查是否有messages文件
                return f"tail -n {lines} /var/log/messages"
            return f"journalctl -n {lines}"


class EulerOSHCEAdapter(EulerOSAdapter):
    """华为欧拉HCE适配器（ARM架构，基于RHEL 8）"""

    def __init__(self, os_info, ssh_client=None):
        super().__init__(os_info, ssh_client)
        self._package_manager = 'dnf'

    def detect_package_manager(self) -> str:
        """HCE使用dnf"""
        return 'dnf'
