"""
OS Information - 操作系统信息数据类

存储检测到的操作系统信息
"""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class OSInfo:
    """操作系统信息"""
    name: str           # "EulerOS", "CentOS", "Ubuntu", "openEuler"
    version: str        # "R10", "R9", "HCE", "7.9", "22.04"
    version_major: str  # 主版本号 "R10", "7", "22"
    family: str         # "rhel", "debian"
    arch: str           # "x86_64", "aarch64", "armv7l"
    has_systemd: bool   # 是否有systemd
    has_dnf: bool       # 是否有dnf包管理器
    has_yum: bool       # 是否有yum包管理器
    has_zypper: bool    # 是否有zypper包管理器
    has_apt: bool       # 是否有apt包管理器

    def __str__(self):
        return f"{self.name} {self.version} ({self.arch})"

    @property
    def package_manager(self) -> str:
        """检测首选的包管理器"""
        if self.has_dnf:
            return "dnf"
        elif self.has_yum:
            return "yum"
        elif self.has_zypper:
            return "zypper"
        elif self.has_apt:
            return "apt"
        return "unknown"

    @property
    def is_rhel_based(self) -> bool:
        """是否是RHEL系发行版"""
        return self.family == "rhel"

    @property
    def is_euleros(self) -> bool:
        """是否是华为欧拉系统"""
        return self.name in ("EulerOS", "openEuler")

    @property
    def is_hce(self) -> bool:
        """是否是HCE ARM版本"""
        return self.name == "EulerOS" and self.version == "HCE"

    @property
    def is_r10(self) -> bool:
        """是否是欧拉R10"""
        return self.name == "EulerOS" and self.version == "R10"

    @property
    def is_r9(self) -> bool:
        """是否是欧拉R9"""
        return self.name == "EulerOS" and self.version == "R9"


class OSInfoDetector:
    """操作系统检测器"""

    # /etc/os-release 解析模式
    OS_RELEASE_PATTERNS = {
        # EulerOS / Huawei EulerOS
        r'huawei.*euleros': 'EulerOS',
        r'euleros': 'EulerOS',
        # openEuler
        r'openeuler': 'openEuler',
        # CentOS
        r'centos': 'CentOS',
        # RHEL
        r'red.*hat.*enterprise.*linux': 'RHEL',
        r'rhel': 'RHEL',
        # Ubuntu
        r'ubuntu': 'Ubuntu',
        # Debian
        r'debian': 'Debian',
        # Fedora
        r'fedora': 'Fedora',
        # SLES
        r'sles': 'SLES',
        r'opensuse.*leap': 'openSUSE',
    }

    # 版本提取模式
    VERSION_PATTERNS = {
        'EulerOS': [
            (r'HCE', 'HCE'),
            (r'R10', 'R10'),
            (r'R9', 'R9'),
            (r'R8', 'R8'),
            (r'version\s+(\d+\.?\d*)', None),  # 动态提取
        ],
        'openEuler': [
            (r'(\d+\.\d+)', None),  # 如 22.03, 20.03
        ],
        'CentOS': [
            (r'(\d+\.\d+)', None),  # 如 7.9, 8.5
            (r'CentOS.*?(\d+)', None),  # 如 CentOS 7
        ],
        'Ubuntu': [
            (r'(\d+\.\d+)', None),  # 如 22.04, 20.04
        ],
    }

    # 家族映射
    FAMILY_MAP = {
        'EulerOS': 'rhel',
        'openEuler': 'rhel',
        'CentOS': 'rhel',
        'RHEL': 'rhel',
        'Fedora': 'rhel',
        'Ubuntu': 'debian',
        'Debian': 'debian',
        'SLES': 'sles',
        'openSUSE': 'sles',
    }

    @classmethod
    def detect_from_os_release(cls, os_release_content: str) -> Optional[OSInfo]:
        """
        从/etc/os-release内容解析OS信息

        Args:
            os_release_content: /etc/os-release文件内容

        Returns:
            OSInfo对象，解析失败返回None
        """
        if not os_release_content:
            return None

        info = {}
        for line in os_release_content.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                info[key] = value.strip('"').strip("'")

        if not info:
            return None

        # 检测发行版名称
        pretty_name = info.get('PRETTY_NAME', '')
        name_id = info.get('NAME', '')
        version_id = info.get('VERSION_ID', '')

        os_name = None
        for pattern, name in cls.OS_RELEASE_PATTERNS.items():
            if re.search(pattern, (pretty_name + name_id).lower()):
                os_name = name
                break

        if not os_name:
            os_name = info.get('ID', 'unknown')

        # 提取版本号
        version = version_id
        version_major = version.split('.')[0] if version else ''

        # 尝试从版本ID中提取更精确的版本
        if os_name in cls.VERSION_PATTERNS:
            for pattern, fixed_version in cls.VERSION_PATTERNS[os_name]:
                if fixed_version:
                    version = fixed_version
                    version_major = version
                    break
                else:
                    match = re.search(pattern, version_id)
                    if match:
                        version = match.group(1)
                        version_major = version.split('.')[0]
                        break

        # 特殊处理EulerOS版本
        if os_name == 'EulerOS':
            if 'HCE' in pretty_name.upper() or 'HCE' in version_id.upper():
                version = 'HCE'
                version_major = 'HCE'
            elif 'R10' in pretty_name.upper():
                version = 'R10'
                version_major = 'R10'
            elif 'R9' in pretty_name.upper():
                version = 'R9'
                version_major = 'R9'

        # 检测架构
        arch = info.get('ARCHITECTURE', '')

        # 确定家族
        family = cls.FAMILY_MAP.get(os_name, 'unknown')

        # 检测systemd
        has_systemd = 'systemd' in os_release_content.lower()

        # 包管理器检测（后续通过命令检测）
        return OSInfo(
            name=os_name,
            version=version,
            version_major=version_major,
            family=family,
            arch=arch,
            has_systemd=has_systemd,
            has_dnf=False,  # 将在detect_package_managers中检测
            has_yum=False,
            has_zypper=False,
            has_apt=False,
        )

    @classmethod
    def detect_from_command(cls, ssh_client) -> Optional[OSInfo]:
        """
        通过SSH命令检测远程系统OS信息

        Args:
            ssh_client: SSHClient实例

        Returns:
            OSInfo对象，检测失败返回None
        """
        try:
            # 1. 获取/etc/os-release
            success, output = ssh_client.execute_command('cat /etc/os-release')
            if not success:
                return None

            os_info = cls.detect_from_os_release(output)
            if not os_info:
                return None

            # 2. 获取架构
            success, arch_output = ssh_client.execute_command('uname -m')
            if success:
                os_info.arch = arch_output.strip()

            # 3. 检测包管理器
            os_info = cls.detect_package_managers(ssh_client, os_info)

            return os_info

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"检测操作系统失败: {e}")
            return None

    @classmethod
    def detect_package_managers(cls, ssh_client, os_info: OSInfo) -> OSInfo:
        """检测可用的包管理器"""
        # 检测dnf
        success, _ = ssh_client.execute_command('which dnf')
        os_info.has_dnf = success

        # 检测yum
        success, _ = ssh_client.execute_command('which yum')
        os_info.has_yum = success

        # 检测zypper
        success, _ = ssh_client.execute_command('which zypper')
        os_info.has_zypper = success

        # 检测apt
        success, _ = ssh_client.execute_command('which apt')
        os_info.has_apt = success

        return os_info

    @classmethod
    def detect(cls, ssh_client) -> OSInfo:
        """
        便捷方法：通过SSH检测远程系统OS信息

        Args:
            ssh_client: SSHClient实例

        Returns:
            OSInfo对象，默认值如果检测失败
        """
        os_info = cls.detect_from_command(ssh_client)
        if os_info:
            return os_info

        # 返回默认值
        return OSInfo(
            name='unknown',
            version='unknown',
            version_major='unknown',
            family='unknown',
            arch='unknown',
            has_systemd=True,
            has_dnf=False,
            has_yum=True,
            has_zypper=False,
            has_apt=False,
        )
