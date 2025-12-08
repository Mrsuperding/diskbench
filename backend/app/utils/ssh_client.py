import os
import paramiko
import socket
from contextlib import contextmanager
from loguru import logger

class SSHClient:
    """SSH客户端"""
    
    def __init__(self, login_credential):
        self.login_credential = login_credential
        self.client = None
        self.connected = False
        self._private_key_file = None
    
    def connect(self, timeout=30):
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': self.login_credential.host,
                'port': self.login_credential.port,
                'username': self.login_credential.username,
                'timeout': timeout
            }
            
            # 自动检测认证方式：先尝试密钥登录，再尝试密码登录
            # 1. 检查是否有可用的私钥
            self._private_key_file = self.login_credential.get_private_key_file()
            if self._private_key_file:
                # 有私钥，使用密钥登录
                logger.info(f"Using private key authentication for {self.login_credential.host}")
                # 获取私钥密码
                passphrase = self.login_credential.get_passphrase()
                if passphrase:
                    # 如果有私钥密码，需要使用RSAKey加载
                    private_key = paramiko.RSAKey.from_private_key_file(self._private_key_file, password=passphrase)
                    connect_kwargs['pkey'] = private_key
                else:
                    # 没有私钥密码，直接使用key_filename
                    connect_kwargs['key_filename'] = self._private_key_file
            else:
                # 没有私钥，使用密码登录
                logger.info(f"Using password authentication for {self.login_credential.host}")
                password = self.login_credential.get_password()
                if password:
                    connect_kwargs['password'] = password
                else:
                    raise ValueError("No authentication method available: neither private key nor password found")
            
            self.client.connect(**connect_kwargs)
            self.connected = True
            logger.info(f"SSH connected to {self.login_credential.host}")
            return True
            
        except Exception as e:
            logger.error(f"SSH connection failed: {e}")
            self.connected = False
            if self.client:
                self.client.close()
            return False
    
    def disconnect(self):
        """断开SSH连接"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info(f"SSH disconnected from {self.login_credential.host}")
        
        # 清理临时私钥文件
        if self._private_key_file:
            self.login_credential.cleanup_private_key_file(self._private_key_file)
            self._private_key_file = None
    
    def execute_command(self, command, timeout=60):
        """执行命令"""
        if not self.connected:
            if not self.connect():
                return False, "Connection failed"
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            
            stdout_data = stdout.read().decode().strip()
            stderr_data = stderr.read().decode().strip()
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                return True, stdout_data
            else:
                return False, stderr_data or stdout_data or f"Command failed with exit code {exit_status}"
                
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return False, str(e)
    
    def upload_file(self, local_path, remote_path):
        """上传文件"""
        try:
            # 确保连接是活跃的
            if not self.connected:
                logger.info("SSH connection not active, trying to connect...")
                if not self.connect():
                    return False, "Connection failed"
            
            sftp = self.client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            logger.info(f"File uploaded: {local_path} -> {remote_path}")
            return True, "File uploaded successfully"
        except (paramiko.ssh_exception.SSHException, OSError) as e:
            logger.error(f"File upload failed: {e}, trying to reconnect...")
            # 尝试重新连接
            self.disconnect()
            if self.connect():
                try:
                    sftp = self.client.open_sftp()
                    sftp.put(local_path, remote_path)
                    sftp.close()
                    logger.info(f"File uploaded after reconnect: {local_path} -> {remote_path}")
                    return True, "File uploaded successfully after reconnect"
                except Exception as re_e:
                    logger.error(f"Reconnect failed: {re_e}")
                    return False, str(re_e)
            else:
                logger.error("Failed to reconnect")
                return False, "Failed to reconnect"
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return False, str(e)
    
    def download_file(self, remote_path, local_path):
        """下载文件"""
        if not self.connected:
            if not self.connect():
                return False, "Connection failed"
        
        try:
            sftp = self.client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            logger.info(f"File downloaded: {remote_path} -> {local_path}")
            return True, "File downloaded successfully"
        except Exception as e:
            logger.error(f"File download failed: {e}")
            return False, str(e)
    
    def test_connection(self):
        """测试连接"""
        try:
            if self.connect(timeout=10):
                # 执行一个简单的命令来测试
                success, output = self.execute_command('echo "connection test"')
                self.disconnect()
                return success, output
            else:
                return False, "Connection failed"
        except Exception as e:
            return False, str(e)
    
    def get_system_info(self):
        """获取系统信息"""
        if not self.connected:
            if not self.connect():
                return None
        
        try:
            commands = {
                'hostname': 'hostname',
                'os_info': 'cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d \'"\'',
                'kernel': 'uname -r',
                'cpu_count': 'nproc',
                'memory_total': 'free -b | grep Mem | awk \'{print $2}\'',
                'disk_info': 'df -h / | tail -1'
            }
            
            system_info = {}
            for key, command in commands.items():
                success, output = self.execute_command(command)
                if success:
                    system_info[key] = output.strip()
            
            return system_info
            
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return None
    
    def check_disk_space(self, path='/tmp'):
        """检查磁盘空间"""
        command = f'df -B1 {path} | tail -1'
        success, output = self.execute_command(command)
        
        if success:
            parts = output.split()
            if len(parts) >= 4:
                total = int(parts[1])
                used = int(parts[2])
                available = int(parts[3])
                return {
                    'total': total,
                    'used': used,
                    'available': available,
                    'usage_percent': (used / total) * 100 if total > 0 else 0
                }
        
        return None
    
    def run_fio_test(self, fio_params, working_dir='/tmp'):
        """运行fio测试"""
        # 直接处理原始参数，不进行预处理，确保转换逻辑被正确执行
        # 构建fio命令
        cmd_parts = ['fio']
        
        # 处理fio参数，转换错误的参数名
        for key, value in fio_params.items():
            # 转换io_type为正确的rw参数
            if key == 'io_type':
                cmd_parts.append(f'--rw={value}')
            # 转换block_size为正确的blocksize参数
            elif key == 'block_size':
                cmd_parts.append(f'--blocksize={value}')
            # 转换queue_depth为正确的iodepth参数
            elif key == 'queue_depth':
                # 如果值包含逗号，逐个执行测试
                if isinstance(value, str) and ',' in value:
                    # 分割多个值
                    values = value.split(',')
                    all_results = []
                    
                    for val in values:
                        # 构建当前值的fio命令
                        single_cmd_parts = ['fio']
                        for k, v in fio_params.items():
                            if k == 'queue_depth':
                                single_cmd_parts.append(f'--iodepth={val.strip()}')
                            elif k == 'io_type':
                                single_cmd_parts.append(f'--rw={v}')
                            elif k == 'block_size':
                                single_cmd_parts.append(f'--blocksize={v}')
                            elif k == 'partitions':
                                continue
                            else:
                                single_cmd_parts.append(f'--{k}={v}')
                        
                        command = ' '.join(single_cmd_parts)
                        
                        # 切换到工作目录
                        if working_dir:
                            command = f'cd {working_dir} && {command}'
                        
                        # 执行fio命令
                        success, output = self.execute_command(command, timeout=3600)  # 1小时超时
                        
                        all_results.append({
                            'success': success,
                            'raw_output': output,
                            'parsed_output': self._parse_fio_output(output) if success else None,
                            'params': {'iodepth': val.strip()}
                        })
                    
                    # 返回所有测试结果的合并结果
                    return {
                        'success': all(r['success'] for r in all_results),
                        'raw_output': '\n\n'.join(r['raw_output'] for r in all_results),
                        'parsed_output': all_results
                    }
                else:
                    cmd_parts.append(f'--iodepth={value}')
            # 跳过partitions参数，分区信息应该从节点信息中获取
            elif key == 'partitions':
                continue
            else:
                cmd_parts.append(f'--{key}={value}')
        
        command = ' '.join(cmd_parts)
        
        # 切换到工作目录
        if working_dir:
            command = f'cd {working_dir} && {command}'
        
        # 执行fio命令
        success, output = self.execute_command(command, timeout=3600)  # 1小时超时
        
        # 返回统一格式的结果
        return {
            'success': success,
            'raw_output': output,
            'parsed_output': self._parse_fio_output(output) if success else None
        }
    
    def _parse_fio_output(self, output):
        """解析fio输出结果"""
        # 简单的fio输出解析，实际项目中可能需要更复杂的解析逻辑
        # 这里返回原始输出作为解析结果，实际项目中应该解析成结构化数据
        return output
    
    def run_vdbench_test(self, vdbench_params, working_dir='/tmp'):
        """运行vdbench测试"""
        # 构建vdbench命令
        cmd_parts = ['vdbench']
        
        for key, value in vdbench_params.items():
            cmd_parts.append(f'-{key}')
            if value is not True:  # 跳过布尔值的值
                cmd_parts.append(str(value))
        
        command = ' '.join(cmd_parts)
        
        # 切换到工作目录
        if working_dir:
            command = f'cd {working_dir} && {command}'
        
        # 执行vdbench命令
        success, output = self.execute_command(command, timeout=3600)  # 1小时超时
        
        # 返回统一格式的结果
        return {
            'success': success,
            'raw_output': output,
            'parsed_output': self._parse_vdbench_output(output) if success else None
        }
    
    def _parse_vdbench_output(self, output):
        """解析vdbench输出结果"""
        # 简单的vdbench输出解析，实际项目中可能需要更复杂的解析逻辑
        # 这里返回原始输出作为解析结果，实际项目中应该解析成结构化数据
        return output

@contextmanager
def ssh_context(login_credential):
    """SSH连接上下文管理器"""
    client = SSHClient(login_credential)
    try:
        if client.connect():
            yield client
        else:
            raise Exception("Failed to connect via SSH")
    finally:
        client.disconnect()