"""
CentOS/RHEL Adapter - CentOS和RHEL操作系统适配器

CentOS 7.x使用yum，CentOS 8.x使用dnf
RHEL 7.x使用yum，RHEL 8.x使用dnf
"""

from typing import List, Tuple
from .base import BaseOSAdapter


class CentOSAdapter(BaseOSAdapter):
    """CentOS/RHEL操作系统适配器"""

    def __init__(self, os_info, ssh_client=None):
        super().__init__(os_info, ssh_client)
        self._package_manager = None

    def detect_package_manager(self) -> str:
        """检测CentOS/RHEL的包管理器"""
        if self._package_manager:
            return self._package_manager

        # CentOS 8+ 和 RHEL 8+ 使用 dnf
        # CentOS 7 和 RHEL 7 使用 yum
        if self.os_info.has_dnf:
            self._package_manager = 'dnf'
        elif self.os_info.has_yum:
            self._package_manager = 'yum'
        else:
            # 根据版本号推断
            version = self.os_info.version_major
            if version and version.isdigit():
                major = int(version)
                self._package_manager = 'yum' if major < 8 else 'dnf'
            else:
                self._package_manager = 'yum'

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
        """使用journalctl（CentOS 7+通常有systemd）"""
        if self.os_info.has_systemd:
            return f"journalctl -n {lines}"
        else:
            return f"tail -n {lines} /var/log/messages"

    def get_dmesg_cmd(self, lines: int = 200) -> str:
        """CentOS 7.2+支持dmesg -T"""
        # 先检查是否支持-T参数
        return f"dmesg | tail -n {lines}"

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


class RHELAdapter(CentOSAdapter):
    """RHEL操作系统适配器（与CentOS基本兼容）"""

    def __init__(self, os_info, ssh_client=None):
        super().__init__(os_info, ssh_client)
        # RHEL通常使用yum（部分8.x版本使用dnf）
        self._package_manager = 'yum'
