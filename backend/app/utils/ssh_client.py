import os
import paramiko
import socket
from contextlib import contextmanager
from loguru import logger

class SSHClient:
    """SSH客户端"""
    
    def __init__(self, login_credential, hostname=None):
        self.login_credential = login_credential
        self.client = None
        self.connected = False
        self._private_key_file = None
        self._hostname = hostname or login_credential.host
    
    def connect(self, timeout=30):
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': self._hostname,
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
            logger.info(f"[SSH执行命令] 主机: {self._hostname}, 命令: {command}")
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            
            stdout_data = stdout.read().decode().strip()
            stderr_data = stderr.read().decode().strip()
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                logger.info(f"[SSH命令执行成功] 主机: {self._hostname}, 退出码: {exit_status}")
                if stdout_data:
                    logger.info(f"[SSH命令结果] 主机: {self._hostname}, 输出:\n{stdout_data}")
                return True, stdout_data
            else:
                logger.warning(f"[SSH命令执行失败] 主机: {self._hostname}, 退出码: {exit_status}")
                if stderr_data:
                    logger.warning(f"[SSH命令错误] 主机: {self._hostname}, 错误:\n{stderr_data}")
                elif stdout_data:
                    logger.warning(f"[SSH命令输出] 主机: {self._hostname}, 输出:\n{stdout_data}")
                return False, stderr_data or stdout_data or f"Command failed with exit code {exit_status}"
                
        except Exception as e:
            logger.error(f"命令执行失败: 主机: {self._hostname}, 错误: {e}")
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
                'os_info': "cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"'",
                'kernel': 'uname -r',
                'cpu_count': 'nproc',
                'memory_total': "free -b | grep Mem | awk '{print $2}'",
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
        # 定义fio支持的核心参数列表
        fio_supported_params = [
            'rw', 'blocksize', 'iodepth', 'filename', 'size', 'runtime', 'numjobs', 
            'iodepth_batch_submit', 'iodepth_batch_complete', 'rwmixread', 'rwmixwrite', 
            'bs', 'ioengine', 'direct', 'sync', 'norandommap', 'randrepeat', 'group_reporting', 
            'name', 'output', 'stonewall', 'overwrite'
        ]
        
        # 定义参数转换映射
        param_mapping = {
            'io_type': 'rw',
            'block_size': 'blocksize',
            'queue_depth': 'iodepth'
        }
        
        # 处理read_write_ratio参数的辅助函数
        def process_read_write_ratio(ratio_value):
            try:
                if isinstance(ratio_value, str):
                    if ':' in ratio_value:
                        read_ratio_str, _ = ratio_value.split(':')
                        read_ratio = int(read_ratio_str.strip())
                    else:
                        read_ratio = int(ratio_value.strip())
                else:
                    read_ratio = int(ratio_value)
                return max(0, min(100, read_ratio))
            except (ValueError, TypeError):
                return None
        
        # 构建fio命令的辅助函数
        def build_cmd_parts(params, current_iodepth=None, current_blocksize=None):
            parts = ['fio']
            
            # 添加默认作业名称
            parts.append('--name=diskbench_test')
            
            # 处理读写比例参数
            ratio = process_read_write_ratio(params.get('read_write_ratio'))
            if ratio is not None:
                parts.append(f'--rwmixread={ratio}')
            else:
                # 默认读写比例：70%读，30%写
                parts.append('--rwmixread=70')
            
            # 处理用户定义的参数
            for key, value in params.items():
                # 跳过无效参数
                if key in ['template_id', 'partitions', 'read_write_ratio']:
                    continue
                
                # 转换参数名
                mapped_key = param_mapping.get(key, key)
                
                # 获取当前值
                val = value
                if key == 'queue_depth' and current_iodepth is not None:
                    val = current_iodepth.strip()
                elif (key == 'block_size' or key == 'blocksize') and current_blocksize is not None:
                    val = current_blocksize.strip()
                
                # 转换为字符串
                if isinstance(val, bool):
                    val = '1' if val else '0'
                elif not isinstance(val, str):
                    val = str(val).strip()
                else:
                    val = val.strip()
                
                # 跳过空值
                if not val:
                    continue
                
                # 如果是支持的参数，使用--key=value格式
                if mapped_key in fio_supported_params:
                    parts.append(f'--{mapped_key}={val}')
                else:
                    # 否则作为自定义参数直接添加到命令末尾
                    parts.append(f'--{mapped_key}={val}')
            
            # 确保包含必要的参数
            # 添加默认numjobs=1（如果用户未指定）
            if not any('--numjobs=' in part for part in parts):
                parts.append('--numjobs=1')
            
            # 处理time_based选项
            time_based = params.get('time_based', False)
            if time_based:
                parts.append('--time_based=1')
            
            # 添加默认runtime=30（如果用户未指定）
            if not any('--runtime=' in part for part in parts):
                parts.append('--runtime=30')
            
            # 添加默认group_reporting（如果用户未指定）
            if not any('--group_reporting' in part for part in parts):
                parts.append('--group_reporting')
            
            return parts
        
        # 获取读写模式列表
        io_type = fio_params.get('io_type', fio_params.get('rw', 'read'))
        io_types = []
        if isinstance(io_type, str) and ',' in io_type:
            io_types = [it.strip() for it in io_type.split(',') if it.strip()]
        elif io_type:
            io_types = [str(io_type).strip()]
        else:
            io_types = ['read']  # 默认读写模式
        
        # 验证并修正读写模式参数
        valid_rw_modes = ['read', 'write', 'randread', 'randwrite', 'rw', 'readwrite', 'randrw']
        corrected_io_types = []
        for io in io_types:
            if io in valid_rw_modes:
                corrected_io_types.append(io)
            elif io == 'randrwrite':
                # 修正常见错误
                corrected_io_types.append('randrw')
            else:
                # 使用默认值
                corrected_io_types.append('read')
        io_types = corrected_io_types
        
        # 获取队列深度列表
        queue_depth = fio_params.get('queue_depth')
        queue_depths = []
        if queue_depth and isinstance(queue_depth, str) and ',' in queue_depth:
            queue_depths = [qd.strip() for qd in queue_depth.split(',') if qd.strip()]
        elif queue_depth:
            queue_depths = [str(queue_depth).strip()]
        else:
            queue_depths = ['16']  # 默认队列深度
        
        # 获取块大小列表
        block_size = fio_params.get('block_size', fio_params.get('blocksize'))
        block_sizes = []
        if block_size and isinstance(block_size, str) and ',' in block_size:
            block_sizes = [bs.strip() for bs in block_size.split(',') if bs.strip()]
        elif block_size:
            block_sizes = [str(block_size).strip()]
        else:
            block_sizes = ['4k']  # 默认块大小
        
        # 处理块大小单位，确保每个块大小都有单位
        processed_block_sizes = []
        for bs in block_sizes:
            # 如果块大小没有单位，添加kb单位
            if bs.isdigit():
                processed_block_sizes.append(f'{bs}k')
            else:
                processed_block_sizes.append(bs)
        block_sizes = processed_block_sizes
        
        # 生成所有组合
        all_combinations = []
        for io in io_types:
            for qd in queue_depths:
                for bs in block_sizes:
                    all_combinations.append({'io_type': io, 'iodepth': qd, 'blocksize': bs})
        
        # 执行所有组合测试
        all_results = []
        for combo in all_combinations:
            io = combo['io_type']
            qd = combo['iodepth']
            bs = combo['blocksize']
            
            # 构建当前组合的fio命令
            # 创建副本，避免修改原参数
            current_params = fio_params.copy()
            # 设置当前组合的参数
            current_params['io_type'] = io
            
            single_cmd_parts = build_cmd_parts(current_params, current_iodepth=qd, current_blocksize=bs)
            
            command = ' '.join(single_cmd_parts)
            
            # 切换到工作目录
            if working_dir:
                command = f'cd {working_dir} && {command}'
            
            # 记录当前组合的详细信息
            logger.info(f"执行fio测试组合: io_type={io}, iodepth={qd}, blocksize={bs}")
            logger.info(f"执行fio命令: {command}")
            
            # 执行fio命令
            success, output = self.execute_command(command, timeout=3600)  # 1小时超时
            
            all_results.append({
                'success': success,
                'raw_output': output,
                'parsed_output': self._parse_fio_output(output) if success else None,
                'params': {'io_type': io, 'iodepth': qd, 'blocksize': bs},
                'command': command  # 保存完整命令
            })
        
        # 返回所有测试结果的合并结果
        return {
            'success': all(r['success'] for r in all_results),
            'raw_output': '\n\n'.join(r['raw_output'] for r in all_results),
            'parsed_output': all_results
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
