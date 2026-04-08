"""
Base OS Adapter - 操作系统适配器基类

定义所有OS适配器需要实现的接口
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import logging


class BaseOSAdapter(ABC):
    """操作系统适配器基类"""

    def __init__(self, os_info, ssh_client=None):
        """
        初始化OS适配器

        Args:
            os_info: OSInfo对象，包含检测到的OS信息
            ssh_client: SSHClient实例（可选，用于执行命令）
        """
        self.os_info = os_info
        self.ssh_client = ssh_client
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    def name(self) -> str:
        """操作系统名称"""
        return self.os_info.name

    @property
    def version(self) -> str:
        """操作系统版本"""
        return self.os_info.version

    @property
    def arch(self) -> str:
        """CPU架构"""
        return self.os_info.arch

    @property
    def family(self) -> str:
        """发行版家族"""
        return self.os_info.family

    def log(self, level: str, msg: str):
        """日志记录"""
        getattr(self.logger, level)(f"[{self.os_info}] {msg}")

    # ==================== 包管理器相关 ====================

    @abstractmethod
    def detect_package_manager(self) -> str:
        """
        检测可用的包管理器

        Returns:
            包管理器名称: 'dnf', 'yum', 'zypper', 'apt', 'unknown'
        """
        pass

    @abstractmethod
    def install_packages(self, packages: List[str]) -> Tuple[bool, str]:
        """
        安装软件包

        Args:
            packages: 包名列表

        Returns:
            (是否成功, 消息)
        """
        pass

    def check_package_installed(self, package: str) -> bool:
        """检查包是否已安装"""
        if self.ssh_client is None:
            return False

        pm = self.detect_package_manager()
        if pm == 'dnf':
            cmd = f"dnf list installed {package}"
        elif pm == 'yum':
            cmd = f"yum list installed {package}"
        elif pm == 'zypper':
            cmd = f"zypper info {package}"
        elif pm == 'apt':
            cmd = f"dpkg -l {package}"
        else:
            cmd = f"which {package}"

        success, output = self.ssh_client.execute_command(cmd)
        return success and package in output

    # ==================== 系统命令 ====================

    @abstractmethod
    def get_hostname_cmd(self) -> str:
        """获取主机名命令"""
        pass

    @abstractmethod
    def get_kernel_cmd(self) -> str:
        """获取内核版本命令"""
        pass

    @abstractmethod
    def get_cpu_count_cmd(self) -> str:
        """获取CPU核心数命令"""
        pass

    @abstractmethod
    def get_memory_cmd(self) -> str:
        """获取内存信息命令（返回字节单位）"""
        pass

    @abstractmethod
    def get_disk_space_cmd(self, path: str = '/') -> str:
        """获取磁盘空间命令"""
        pass

    @abstractmethod
    def get_uptime_cmd(self) -> str:
        """获取运行时间命令"""
        pass

    # ==================== 系统日志命令 ====================

    @abstractmethod
    def get_system_log_cmd(self, lines: int = 200) -> str:
        """
        获取系统日志命令

        Args:
            lines: 日志行数

        Returns:
            命令字符串
        """
        pass

    @abstractmethod
    def get_dmesg_cmd(self, lines: int = 200) -> str:
        """
        获取dmesg命令

        Args:
            lines: 日志行数

        Returns:
            命令字符串
        """
        pass

    # ==================== 监控工具命令 ====================

    @abstractmethod
    def get_iostat_cmd(self, interval: int = 1, device: str = None) -> str:
        """
        获取iostat命令

        Args:
            interval: 采样间隔（秒）
            device: 设备名（如sda），None表示所有设备

        Returns:
            命令字符串
        """
        pass

    @abstractmethod
    def get_mpstat_cmd(self, interval: int = 1) -> str:
        """
        获取mpstat命令

        Args:
            interval: 采样间隔（秒）

        Returns:
            命令字符串
        """
        pass

    @abstractmethod
    def get_free_cmd(self) -> str:
        """获取free命令"""
        pass

    @abstractmethod
    def get_netstat_cmd(self) -> str:
        """获取netstat命令"""
        pass

    # ==================== 进程管理命令 ====================

    @abstractmethod
    def get_process_list_cmd(self) -> str:
        """获取进程列表命令"""
        pass

    @abstractmethod
    def kill_process_cmd(self, pid: int, signal: int = 15) -> str:
        """
        终止进程命令

        Args:
            pid: 进程ID
            signal: 信号（15=SIGTERM, 9=SIGKILL）

        Returns:
            命令字符串
        """
        pass

    # ==================== 文件操作命令 ====================

    @abstractmethod
    def get_file_size_cmd(self, path: str) -> str:
        """获取文件大小命令"""
        pass

    @abstractmethod
    def get_file_content_cmd(self, path: str, lines: int = None) -> str:
        """
        获取文件内容命令

        Args:
            path: 文件路径
            lines: 行数限制，None表示全部

        Returns:
            命令字符串
        """
        pass

    # ==================== FIO相关命令 ====================

    def get_fio_install_check_cmd(self) -> str:
        """检查fio是否安装"""
        return "which fio"

    def get_fio_version_cmd(self) -> str:
        """获取fio版本"""
        return "fio --version"

    def get_fio_stop_cmd(self, pattern: str = "fio") -> str:
        """
        停止fio进程

        Args:
            pattern: 进程匹配模式

        Returns:
            命令字符串
        """
        return f"pkill -f '{pattern}'"

    # ==================== iostat进程管理 ====================

    def get_iostat_start_cmd(self, log_path: str, interval: int = 1) -> str:
        """
        启动iostat后台监控

        Args:
            log_path: 日志文件路径
            interval: 采样间隔

        Returns:
            命令字符串
        """
        device_flag = ""
        cmd = f"sh -c 'iostat -xdm {interval} > {log_path} 2>&1 & echo $! > /tmp/iostat_pid.txt'"
        return cmd

    def get_iostat_stop_cmd(self) -> str:
        """停止iostat监控"""
        return "pkill -f 'iostat -xdm'"

    def get_iostat_pid_cmd(self) -> str:
        """获取iostat进程PID文件路径"""
        return "cat /tmp/iostat_pid.txt 2>/dev/null || echo ''"

    # ==================== 辅助方法 ====================

    def is_connected(self) -> bool:
        """检查SSH连接是否正常"""
        if self.ssh_client is None:
            return False
        success, _ = self.ssh_client.execute_command("echo ok")
        return success

    def get_system_info(self) -> dict:
        """获取完整系统信息"""
        if self.ssh_client is None:
            return {}

        info = {}

        # 主机名
        success, output = self.ssh_client.execute_command(self.get_hostname_cmd())
        if success:
            info['hostname'] = output.strip()

        # 内核
        success, output = self.ssh_client.execute_command(self.get_kernel_cmd())
        if success:
            info['kernel'] = output.strip()

        # CPU核心数
        success, output = self.ssh_client.execute_command(self.get_cpu_count_cmd())
        if success:
            try:
                info['cpu_count'] = int(output.strip())
            except ValueError:
                pass

        # 内存
        success, output = self.ssh_client.execute_command(self.get_memory_cmd())
        if success:
            info['memory_raw'] = output.strip()

        # 磁盘
        success, output = self.ssh_client.execute_command(self.get_disk_space_cmd())
        if success:
            info['disk_raw'] = output.strip()

        return info
