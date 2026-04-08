"""
Fedora Adapter - Fedora操作系统适配器

Fedora使用dnf包管理器
"""

from typing import List, Tuple
from .base import BaseOSAdapter


class FedoraAdapter(BaseOSAdapter):
    """Fedora操作系统适配器"""

    def __init__(self, os_info, ssh_client=None):
        super().__init__(os_info, ssh_client)

    def detect_package_manager(self) -> str:
        """Fedora使用dnf"""
        return 'dnf'

    def install_packages(self, packages: List[str]) -> Tuple[bool, str]:
        """安装软件包"""
        if self.ssh_client is None:
            return False, "SSH client not available"

        package_list = ' '.join(packages)
        cmd = f"sudo dnf install -y {package_list}"

        self.log('info', f"安装包: {package_list}")
        success, output = self.ssh_client.execute_command(cmd)

        if success:
            return True, f"Successfully installed {package_list}"
        else:
            return False, f"Failed to install {package_list}: {output}"

    # ==================== 系统命令实现 ====================

    def get_hostname_cmd(self) -> str:
        return "hostname"

    def get_kernel_cmd(self) -> str:
        return "uname -r"

    def get_cpu_count_cmd(self) -> str:
        return "nproc"

    def get_memory_cmd(self) -> str:
        return "free -b | grep Mem | awk '{print $2}'"

    def get_disk_space_cmd(self, path: str = '/') -> str:
        return f"df -B1 {path} | tail -1 | awk '{{print $2}}'"

    def get_uptime_cmd(self) -> str:
        return "uptime -s"

    # ==================== 系统日志命令实现 ====================

    def get_system_log_cmd(self, lines: int = 200) -> str:
        """Fedora使用journalctl"""
        return f"journalctl -n {lines}"

    def get_dmesg_cmd(self, lines: int = 200) -> str:
        """Fedora支持dmesg -T"""
        return f"dmesg -T | tail -n {lines}"

    # ==================== 监控工具命令实现 ====================

    def get_iostat_cmd(self, interval: int = 1, device: str = None) -> str:
        cmd = f"iostat -xdm {interval}"
        if device:
            cmd += f" {device}"
        return cmd

    def get_mpstat_cmd(self, interval: int = 1) -> str:
        return f"mpstat {interval} 1"

    def get_free_cmd(self) -> str:
        return "free -h"

    def get_netstat_cmd(self) -> str:
        return "ss -s || netstat -ant"

    # ==================== 进程管理命令实现 ====================

    def get_process_list_cmd(self) -> str:
        return "ps aux"

    def kill_process_cmd(self, pid: int, signal: int = 15) -> str:
        return f"kill -{signal} {pid}"

    # ==================== 文件操作命令实现 ====================

    def get_file_size_cmd(self, path: str) -> str:
        return f"stat -c%s {path}"

    def get_file_content_cmd(self, path: str, lines: int = None) -> str:
        if lines:
            return f"head -n {lines} {path}"
        return f"cat {path}"

    def get_fio_stop_cmd(self, pattern: str = "fio") -> str:
        return f"pkill -f '{pattern}'"
