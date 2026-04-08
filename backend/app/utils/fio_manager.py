"""
FIO Manager - FIO工具管理器

提供FIO的自动检测、安装和版本管理功能
支持跨架构（x86_64, aarch64）和跨OS安装
"""

from typing import Tuple, Optional, Dict
import logging
import os


class FIOManager:
    """FIO工具管理器"""

    # 预编译FIO二进制路径模板
    # 可以配置本地预编译二进制路径
    FIO_BINARY_PATHS = {
        # x86_64架构
        ('x86_64', 'EulerOS', 'R10'): '/opt/fio/bin/fio_x86_64',
        ('x86_64', 'EulerOS', 'R9'): '/opt/fio/bin/fio_x86_64',
        ('x86_64', 'openEuler', None): '/opt/fio/bin/fio_x86_64',
        ('x86_64', 'CentOS', None): '/opt/fio/bin/fio_x86_64',
        ('x86_64', 'RHEL', None): '/opt/fio/bin/fio_x86_64',
        ('x86_64', 'Ubuntu', None): '/opt/fio/bin/fio_x86_64',
        ('x86_64', 'Debian', None): '/opt/fio/bin/fio_x86_64',
        ('x86_64', 'Fedora', None): '/opt/fio/bin/fio_x86_64',

        # aarch64 (ARM64) 架构
        ('aarch64', 'EulerOS', 'HCE'): '/opt/fio/bin/fio_aarch64',
        ('aarch64', 'EulerOS', 'R10'): '/opt/fio/bin/fio_aarch64',
        ('aarch64', 'openEuler', None): '/opt/fio/bin/fio_aarch64',
        ('aarch64', 'CentOS', None): '/opt/fio/bin/fio_aarch64',
        ('aarch64', 'Ubuntu', None): '/opt/fio/bin/fio_aarch64',
        ('aarch64', 'Debian', None): '/opt/fio/bin/fio_aarch64',

        # 默认路径
        ('x86_64', None, None): '/opt/fio/bin/fio_x86_64',
        ('aarch64', None, None): '/opt/fio/bin/fio_aarch64',
    }

    # 预编译二进制是否可用（需要在配置中启用）
    USE_PRECOMPILED = os.getenv('FIO_USE_PRECOMPILED', 'false').lower() == 'true'
    PRECOMPILED_BASE_PATH = os.getenv('FIO_PRECOMPILED_BASE', '/opt/fio/bin')

    def __init__(self, ssh_client, os_info, local_binary_dir: str = None):
        """
        初始化FIO管理器

        Args:
            ssh_client: SSHClient实例
            os_info: OSInfo对象
            local_binary_dir: 本地预编译二进制目录（可选）
        """
        self.ssh_client = ssh_client
        self.os_info = os_info
        self.local_binary_dir = local_binary_dir or self.PRECOMPILED_BASE_PATH
        self.logger = logging.getLogger(__name__)

    def check_fio_installed(self) -> Tuple[bool, str]:
        """
        检查FIO是否已安装

        Returns:
            (是否已安装, fio版本或路径)
        """
        # 首先检查fio命令是否存在
        success, output = self.ssh_client.execute_command('which fio')
        if success and output.strip():
            # 检查版本
            success, version_output = self.ssh_client.execute_command('fio --version')
            if success:
                return True, version_output.strip()

        return False, "FIO not found"

    def get_fio_version(self) -> Tuple[bool, str]:
        """获取FIO版本"""
        success, output = self.ssh_client.execute_command('fio --version')
        if success:
            return True, output.strip()
        return False, "Failed to get fio version"

    def ensure_fio_installed(self) -> Tuple[bool, str]:
        """
        确保FIO已安装，自动选择最佳安装方式

        安装优先级：
        1. 检查是否已安装
        2. 尝试上传预编译二进制（如果启用）
        3. 通过包管理器安装

        Returns:
            (是否成功, 消息)
        """
        # 1. 检查是否已安装
        installed, info = self.check_fio_installed()
        if installed:
            self.logger.info(f"FIO已安装: {info}")
            return True, f"FIO already installed: {info}"

        # 2. 尝试预编译二进制
        if self.USE_PRECOMPILED:
            success, msg = self._install_from_precompiled()
            if success:
                return True, msg

        # 3. 通过包管理器安装
        success, msg = self._install_via_package_manager()
        if success:
            return True, msg

        return False, "Failed to install FIO"

    def _install_from_precompiled(self) -> Tuple[bool, str]:
        """从预编译二进制安装"""
        try:
            # 获取本地二进制路径
            local_path = self._get_local_binary_path()
            if not local_path or not os.path.exists(local_path):
                self.logger.warning(f"预编译FIO不存在: {local_path}")
                return False, "Precompiled binary not found"

            remote_path = f"/tmp/fio_{self.os_info.arch}"
            remote_dir = "/tmp"

            self.logger.info(f"上传预编译FIO: {local_path} -> {remote_path}")

            # 上传二进制文件
            success, msg = self.ssh_client.upload_file(local_path, remote_path)
            if not success:
                return False, f"Failed to upload fio: {msg}"

            # 设置执行权限
            success, msg = self.ssh_client.execute_command(f"chmod +x {remote_path}")
            if not success:
                return False, f"Failed to set execute permission: {msg}"

            # 验证安装
            success, version = self.ssh_client.execute_command(f"{remote_path} --version")
            if success:
                # 创建符号链接到系统路径
                self.ssh_client.execute_command(f"sudo ln -sf {remote_path} /usr/local/bin/fio")
                return True, f"FIO installed from precompiled: {version.strip()}"

            return False, "Failed to verify fio installation"

        except Exception as e:
            self.logger.error(f"从预编译安装失败: {e}")
            return False, str(e)

    def _get_local_binary_path(self) -> Optional[str]:
        """获取本地预编译二进制路径"""
        key = (self.os_info.arch, self.os_info.name, self.os_info.version)
        binary_name = f"fio_{self.os_info.arch}"

        # 尝试键查找
        if key in self.FIO_BINARY_PATHS:
            return self.FIO_BINARY_PATHS[key]

        # 尝试更宽泛的查找
        generic_key = (self.os_info.arch, None, None)
        if generic_key in self.FIO_BINARY_PATHS:
            return self.FIO_BINARY_PATHS[generic_key]

        # 在本地目录中查找
        if os.path.exists(self.local_binary_dir):
            for f in os.listdir(self.local_binary_dir):
                if f.startswith('fio') and self.os_info.arch in f:
                    return os.path.join(self.local_binary_dir, f)

        return None

    def _install_via_package_manager(self) -> Tuple[bool, str]:
        """通过包管理器安装FIO"""
        from .package_manager import PackageManager

        try:
            # 获取包管理器
            pm, pm_name = PackageManager.detect_and_get_manager(self.ssh_client)
            self.logger.info(f"使用包管理器安装FIO: {pm_name}")

            # 安装 fio 和 sysstat（iostat）
            packages = ['fio']
            if not pm.is_installed('sysstat'):  # sysstat包含iostat
                packages.append('sysstat')

            success, msg = pm.install(packages)
            if success:
                # 验证安装
                success, version = self.get_fio_version()
                if success:
                    return True, f"FIO installed via {pm_name}: {version.strip()}"

            return False, f"Failed to install fio via {pm_name}: {msg}"

        except Exception as e:
            self.logger.error(f"通过包管理器安装FIO失败: {e}")
            return False, str(e)

    def install_sysstat(self) -> Tuple[bool, str]:
        """安装sysstat（包含iostat）"""
        from .package_manager import PackageManager

        try:
            pm, pm_name = PackageManager.detect_and_get_manager(self.ssh_client)

            if pm.is_installed('sysstat'):
                return True, "sysstat already installed"

            success, msg = pm.install(['sysstat'])
            if success:
                return True, f"sysstat installed via {pm_name}"

            return False, f"Failed to install sysstat: {msg}"

        except Exception as e:
            self.logger.error(f"安装sysstat失败: {e}")
            return False, str(e)

    def get_fio_command(self, fio_params: dict, working_dir: str = '/tmp') -> str:
        """
        生成FIO命令

        Args:
            fio_params: FIO参数字典
            working_dir: 工作目录

        Returns:
            完整的FIO命令字符串
        """
        cmd_parts = ['fio']

        # 添加参数
        for key, value in fio_params.items():
            if value is True:
                cmd_parts.append(f'--{key}')
            else:
                cmd_parts.append(f'--{key}={value}')

        return ' '.join(cmd_parts)

    def run_fio_test(self, fio_params: dict, log_file: str = '/tmp/fio.log',
                     working_dir: str = '/tmp') -> Tuple[bool, str]:
        """
        运行FIO测试

        Args:
            fio_params: FIO参数字典
            log_file: 日志文件路径
            working_dir: 工作目录

        Returns:
            (是否成功, 输出或错误消息)
        """
        # 确保FIO已安装
        success, msg = self.ensure_fio_installed()
        if not success:
            return False, msg

        # 生成命令
        fio_cmd = self.get_fio_command(fio_params, working_dir)
        fio_cmd += f" --output={log_file}"

        self.logger.info(f"执行FIO测试: {fio_cmd}")

        # 执行命令
        success, output = self.ssh_client.execute_command(fio_cmd, timeout=3600)

        if success:
            return True, log_file
        return False, output

    def stop_fio(self) -> Tuple[bool, str]:
        """停止FIO进程"""
        cmd = "pkill -f 'fio'"
        success, output = self.ssh_client.execute_command(cmd)
        if success:
            return True, "FIO processes stopped"
        return False, output
