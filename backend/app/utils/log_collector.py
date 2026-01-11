import os
import re
import datetime
import json
import logging
import statistics
from datetime import datetime
from app.models import db, TestLog, IOStatMetric
from loguru import logger

class LogCollector:
    """日志收集器"""
    
    def __init__(self, app=None):
        self.app = app
        self.log_base_dir = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        self.app = app
        log_base_dir = app.config.get('LOG_STORAGE_DIR', '/tmp/io_platform_logs')
        # 规范化路径，统一使用正斜杠
        self.log_base_dir = log_base_dir.replace('\\', '/')
        os.makedirs(self.log_base_dir, exist_ok=True)
        logger.info(f"日志收集器初始化完成，日志存储目录: {self.log_base_dir}")
    
    def collect_iostat_log(self, ssh_client, task_id, execution_id, node_id, io_test_case_id, remote_log_path):
        """收集iostat日志"""
        try:
            # 获取任务名称
            from app.models import TestTask
            test_task = TestTask.query.get(task_id)
            task_name = test_task.name if test_task else f'task_{task_id}'
            
            # 获取IO测试用例名称
            from app.models import IOTestCase
            io_test_case = IOTestCase.query.get(io_test_case_id)
            io_test_case_name = io_test_case.name if io_test_case else f'io_case_{io_test_case_id}'
            
            # 获取节点登录凭证的平台分区路径
            from app.models import Node
            node = Node.query.get(node_id)
            platform_partition = node.login_credential.platform_partition if node and node.login_credential else '/diskbench'
            
            # 规范化路径，统一使用正斜杠
            platform_partition = platform_partition.replace('\\', '/')
            
            # 创建任务专属的目录结构 - 使用正斜杠
            task_data_dir = f"{platform_partition}/data/task_{task_id}"
            iostat_data_dir = f"{task_data_dir}/iostat_data"
            # 再次确保使用正斜杠
            task_data_dir = task_data_dir.replace('\\', '/')
            iostat_data_dir = iostat_data_dir.replace('\\', '/')
            os.makedirs(iostat_data_dir, exist_ok=True)
            
            # 生成唯一标识（使用时间戳）
            unique_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
            
            # 构建本地日志文件名（任务名称+IO模型，包含唯一标识）
            local_log_filename = f'{task_name}_{io_test_case_name}_iostat_{unique_id}.log'
            # 使用正斜杠构建路径
            local_log_path = f"{iostat_data_dir}/{local_log_filename}"
            # 确保使用正斜杠
            local_log_path = local_log_path.replace('\\', '/')
            
            # 下载iostat日志文件
            success, message = ssh_client.download_file(remote_log_path, local_log_path)
            if not success:
                logger.error(f"下载iostat日志失败: {message}")
                return None
            
            logger.info(f"成功下载iostat日志: {local_log_path}")
            
            # 解析iostat日志
            iostat_metrics = self._parse_iostat_log(local_log_path)
            
            # 创建性能数据目录
            performance_data_dir = f"{task_data_dir}/performance_data"
            performance_data_dir = performance_data_dir.replace('\\', '/')
            os.makedirs(performance_data_dir, exist_ok=True)
            
            # 导出性能数据为JSON格式
            performance_data_filename = f'{task_name}_{io_test_case_name}_performance_{unique_id}.json'
            performance_data_path = f"{performance_data_dir}/{performance_data_filename}"
            performance_data_path = performance_data_path.replace('\\', '/')
            
            # 准备性能数据
            performance_data = {
                'task_id': task_id,
                'task_name': task_name,
                'io_test_case_id': io_test_case_id,
                'io_test_case_name': io_test_case_name,
                'node_id': node_id,
                'collection_time': datetime.now().isoformat(),
                'iostat_metrics': iostat_metrics,
                'iostat_log_path': local_log_path
            }
            
            # 保存性能数据到JSON文件
            with open(performance_data_path, 'w') as f:
                json.dump(performance_data, f, default=str, indent=2)
            
            logger.info(f"成功保存性能数据: {performance_data_path}")
            
            # 计算并保存性能抖动数据
            if iostat_metrics:
                # 计算不同指标类型的抖动
                jitter_metrics = {
                    'iops': self.calculate_jitter(iostat_metrics, 'iops'),
                    'bandwidth': self.calculate_jitter(iostat_metrics, 'bandwidth'),
                    'latency': self.calculate_jitter(iostat_metrics, 'latency')
                }
                
                # 保存抖动数据到JSON文件
                jitter_data_filename = f'{task_name}_{io_test_case_name}_jitter_{unique_id}.json'
                jitter_data_path = f"{performance_data_dir}/{jitter_data_filename}"
                jitter_data_path = jitter_data_path.replace('\\', '/')
                
                jitter_data = {
                    'task_id': task_id,
                    'task_name': task_name,
                    'io_test_case_id': io_test_case_id,
                    'io_test_case_name': io_test_case_name,
                    'node_id': node_id,
                    'collection_time': datetime.now().isoformat(),
                    'jitter_metrics': jitter_metrics
                }
                
                with open(jitter_data_path, 'w') as f:
                    json.dump(jitter_data, f, default=str, indent=2)
                
                logger.info(f"成功保存性能抖动数据: {jitter_data_path}")
            
            # 保存日志元数据到数据库
            test_log = TestLog(
                test_task_id=task_id,
                node_id=node_id,
                task_execution_id=execution_id,
                log_type='iostat',
                log_filename=local_log_filename,
                log_path=local_log_path,
                file_size=os.path.getsize(local_log_path),
                collection_time=datetime.utcnow()
            )
            
            db.session.add(test_log)
            db.session.flush()  # 获取test_log.id
            
            # 保存解析后的iostat指标到数据库
            for metric in iostat_metrics:
                iostat_metric = IOStatMetric(
                    test_log_id=test_log.id,
                    collection_time=metric['timestamp'],
                    device=metric['device'],
                    read_kbps=metric['read_kbps'],
                    write_kbps=metric['write_kbps'],
                    read_iops=metric['read_iops'],
                    write_iops=metric['write_iops'],
                    await_time=metric['await_time'],
                    svctm=metric['svctm'],
                    util=metric['util']
                )
                db.session.add(iostat_metric)
            
            db.session.commit()
            logger.info(f"成功保存iostat日志元数据和指标: log_id={test_log.id}")
            logger.info(f"iostat日志文件路径: {local_log_path}")
            
            return test_log
            
        except Exception as e:
            logger.error(f"收集iostat日志失败: {e}", exc_info=True)
            if 'db' in locals() and db.session:
                db.session.rollback()
            return None
    
    def collect_fio_log(self, ssh_client, task_id, execution_id, node_id, io_test_case_id, remote_log_path):
        """收集fio日志"""
        try:
            # 获取任务名称
            from app.models import TestTask
            test_task = TestTask.query.get(task_id)
            task_name = test_task.name if test_task else f'task_{task_id}'
            
            # 获取IO测试用例名称
            from app.models import IOTestCase
            io_test_case = IOTestCase.query.get(io_test_case_id)
            io_test_case_name = io_test_case.name if io_test_case else f'io_case_{io_test_case_id}'
            
            # 获取节点登录凭证的平台分区路径
            from app.models import Node
            node = Node.query.get(node_id)
            platform_partition = node.login_credential.platform_partition if node and node.login_credential else '/diskbench'
            
            # 规范化路径，统一使用正斜杠
            platform_partition = platform_partition.replace('\\', '/')
            
            # 创建任务专属的目录结构 - 使用正斜杠
            task_data_dir = f"{platform_partition}/data/task_{task_id}"
            fio_data_dir = f"{task_data_dir}/fio_data"
            # 再次确保使用正斜杠
            task_data_dir = task_data_dir.replace('\\', '/')
            fio_data_dir = fio_data_dir.replace('\\', '/')
            os.makedirs(fio_data_dir, exist_ok=True)
            
            # 生成唯一标识（使用时间戳）
            unique_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
            
            # 构建本地日志文件名（任务名称+IO模型，包含唯一标识）
            local_log_filename = f'{task_name}_{io_test_case_name}_fio_{unique_id}.log'
            # 使用正斜杠构建路径
            local_log_path = f"{fio_data_dir}/{local_log_filename}"
            # 确保使用正斜杠
            local_log_path = local_log_path.replace('\\', '/')
            
            # 下载fio日志文件
            success, message = ssh_client.download_file(remote_log_path, local_log_path)
            if not success:
                logger.error(f"下载fio日志失败: {message}")
                return None
            
            logger.info(f"成功下载fio日志: {local_log_path}")
            
            # 保存日志元数据到数据库
            test_log = TestLog(
                test_task_id=task_id,
                node_id=node_id,
                task_execution_id=execution_id,
                log_type='fio',
                log_filename=local_log_filename,
                log_path=local_log_path,
                file_size=os.path.getsize(local_log_path),
                collection_time=datetime.utcnow()
            )
            
            db.session.add(test_log)
            db.session.commit()
            logger.info(f"成功保存fio日志元数据: log_id={test_log.id}")
            logger.info(f"fio日志文件路径: {local_log_path}")
            
            return test_log
            
        except Exception as e:
            logger.error(f"收集fio日志失败: {e}", exc_info=True)
            if 'db' in locals() and db.session:
                db.session.rollback()
            return None
    
    def collect_system_log(self, task_id, execution_id, node_id, io_test_case_id, command_logs):
        """收集系统执行指令日志"""
        try:
            # 获取任务名称
            from app.models import TestTask
            test_task = TestTask.query.get(task_id)
            task_name = test_task.name if test_task else f'task_{task_id}'
            
            # 获取IO测试用例名称
            from app.models import IOTestCase
            io_test_case = IOTestCase.query.get(io_test_case_id)
            io_test_case_name = io_test_case.name if io_test_case else f'io_case_{io_test_case_id}'
            
            # 获取节点登录凭证的平台分区路径
            from app.models import Node
            node = Node.query.get(node_id)
            platform_partition = node.login_credential.platform_partition if node and node.login_credential else '/diskbench'
            
            # 规范化路径，统一使用正斜杠
            platform_partition = platform_partition.replace('\\', '/')
            
            # 创建任务专属的目录结构 - 使用正斜杠
            task_data_dir = f"{platform_partition}/data/task_{task_id}"
            system_data_dir = f"{task_data_dir}/system_logs"
            # 再次确保使用正斜杠
            task_data_dir = task_data_dir.replace('\\', '/')
            system_data_dir = system_data_dir.replace('\\', '/')
            os.makedirs(system_data_dir, exist_ok=True)
            
            # 生成唯一标识（使用时间戳）
            unique_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
            
            # 构建本地日志文件名（任务名称+IO模型，包含唯一标识）
            local_log_filename = f'{task_name}_{io_test_case_name}_system_{unique_id}.log'
            # 使用正斜杠构建路径
            local_log_path = f"{system_data_dir}/{local_log_filename}"
            # 确保使用正斜杠
            local_log_path = local_log_path.replace('\\', '/')
            
            # 写入系统日志文件
            with open(local_log_path, 'w') as f:
                for log_entry in command_logs:
                    f.write(f"{log_entry['timestamp']} - {log_entry['command']}\n")
                    if 'output' in log_entry:
                        f.write(f"{log_entry['output']}\n\n")
            
            logger.info(f"成功写入系统日志: {local_log_path}")
            
            # 保存日志元数据到数据库
            test_log = TestLog(
                test_task_id=task_id,
                node_id=node_id,
                task_execution_id=execution_id,
                log_type='system',
                log_filename=local_log_filename,
                log_path=local_log_path,
                file_size=os.path.getsize(local_log_path),
                collection_time=datetime.utcnow()
            )
            
            db.session.add(test_log)
            db.session.commit()
            logger.info(f"成功保存系统日志元数据: log_id={test_log.id}")
            logger.info(f"系统日志文件路径: {local_log_path}")
            
            return test_log
            
        except Exception as e:
            logger.error(f"收集系统日志失败: {e}", exc_info=True)
            if 'db' in locals() and db.session:
                db.session.rollback()
            return None
    
    def _parse_iostat_log(self, log_path):
        """解析iostat日志"""
        metrics = []
        
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()
            
            # iostat -xdm 1 的输出格式示例:
            # Device:         rrqm/s   wrqm/s     r/s     w/s    rMB/s    wMB/s avgrq-sz avgqu-sz   await r_await w_await  svctm  %util
            # sda               0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00
            
            # 查找包含Device行的索引
            header_index = None
            for i, line in enumerate(lines):
                if line.strip().startswith('Device:'):
                    header_index = i
                    break
            
            if header_index is None:
                logger.warning(f"iostat日志格式不正确，未找到设备行: {log_path}")
                return metrics
            
            # 获取当前时间，用于计算采集时间戳
            current_time = datetime.now()
            
            # 解析指标数据
            device_data = []
            in_data_section = False
            for i, line in enumerate(lines[header_index+1:]):
                line = line.strip()
                if not line:
                    # 空行可能是分隔符，重置设备数据
                    device_data = []
                    in_data_section = False
                    continue
                
                if 'Device:' in line:
                    # 新的设备头，重置设备数据
                    device_data = []
                    in_data_section = False
                    continue
                
                # 解析设备数据行
                parts = line.split()
                if len(parts) < 14:
                    continue
                
                device = parts[0]
                metrics.append({
                    'timestamp': current_time - datetime.timedelta(seconds=len(lines[header_index+1:])-i),
                    'device': device,
                    'read_kbps': float(parts[5]) * 1024,  # 转换为KB/s
                    'write_kbps': float(parts[6]) * 1024,  # 转换为KB/s
                    'read_iops': float(parts[2]),
                    'write_iops': float(parts[3]),
                    'await_time': float(parts[9]),
                    'svctm': float(parts[12]),
                    'util': float(parts[13])
                })
            
            logger.info(f"成功解析iostat日志，共解析{len(metrics)}条指标: {log_path}")
            
        except Exception as e:
            logger.error(f"解析iostat日志失败: {e}", exc_info=True)
        
        return metrics
    
    def _parse_fio_log(self, log_path):
        """解析fio日志，提取关键性能指标"""
        metrics = {
            'global': {},
            'jobs': []
        }
        
        try:
            with open(log_path, 'r') as f:
                content = f.read()
            
            # 解析全局结果
            global_result_match = re.search(r'\[global\].*?bw=(.*?), iops=(.*?), lat=(.*?),', content, re.DOTALL)
            if global_result_match:
                metrics['global'] = {
                    'bw': global_result_match.group(1).strip(),
                    'iops': global_result_match.group(2).strip(),
                    'lat': global_result_match.group(3).strip()
                }
            
            # 解析作业结果
            job_results = re.findall(r'\[job (.*?)\].*?bw=(.*?), iops=(.*?), lat=(.*?),', content, re.DOTALL)
            for job_result in job_results:
                metrics['jobs'].append({
                    'name': job_result[0].strip(),
                    'bw': job_result[1].strip(),
                    'iops': job_result[2].strip(),
                    'lat': job_result[3].strip()
                })
            
            # 解析详细的性能指标
            read_write_match = re.search(r'Run status group 0 .*?\n  (read|write):.*?bw=(.*?), iops=(.*?), lat=(.*?)avg.*?\n.*?bw=(.*?), iops=(.*?), lat=(.*?)avg', content, re.DOTALL)
            if read_write_match:
                if read_write_match.group(1) == 'read':
                    metrics['global']['read'] = {
                        'bw': read_write_match.group(2).strip(),
                        'iops': read_write_match.group(3).strip(),
                        'lat': read_write_match.group(4).strip()
                    }
                    metrics['global']['write'] = {
                        'bw': read_write_match.group(5).strip(),
                        'iops': read_write_match.group(6).strip(),
                        'lat': read_write_match.group(7).strip()
                    }
                else:
                    metrics['global']['write'] = {
                        'bw': read_write_match.group(2).strip(),
                        'iops': read_write_match.group(3).strip(),
                        'lat': read_write_match.group(4).strip()
                    }
                    metrics['global']['read'] = {
                        'bw': read_write_match.group(5).strip(),
                        'iops': read_write_match.group(6).strip(),
                        'lat': read_write_match.group(7).strip()
                    }
            
            logger.info(f"成功解析fio日志，提取{len(metrics['jobs'])}个作业的性能指标: {log_path}")
            
        except Exception as e:
            logger.error(f"解析fio日志失败: {e}", exc_info=True)
        
        return metrics
    
    def _parse_fio_json_log(self, log_path):
        """解析fio JSON日志，提取关键性能指标"""
        metrics = {
            'global': {},
            'jobs': [],
            'detailed': {
                'read': {},
                'write': {}
            },
            'start_time': None,
            'end_time': None
        }
        
        try:
            with open(log_path, 'r') as f:
                json_content = json.load(f)
            
            # 提取开始时间和结束时间
            fio_time = json_content.get('time', {})
            metrics['start_time'] = fio_time.get('time', 0)
            metrics['end_time'] = fio_time.get('time', 0) + fio_time.get('runtime', 0)
            
            # 提取全局统计信息
            global_stats = json_content.get('global', {}).get('stats', [{}])[0]
            metrics['global'] = {
                'bw': global_stats.get('bw_bytes', 0) / 1024,  # 转换为KB/s
                'iops': global_stats.get('iops', 0),
                'lat_ns': global_stats.get('lat_ns', {}).get('mean', 0) / 1000000,  # 转换为ms
                'lat_min': global_stats.get('lat_ns', {}).get('min', 0) / 1000000,  # 转换为ms
                'lat_max': global_stats.get('lat_ns', {}).get('max', 0) / 1000000,  # 转换为ms
                'lat_p99': global_stats.get('lat_ns', {}).get('percentile', {}).get('99.000000', 0) / 1000000,  # 转换为ms
                'clat_ns': global_stats.get('clat_ns', {}).get('mean', 0) / 1000000,  # 转换为ms
                'slat_ns': global_stats.get('slat_ns', {}).get('mean', 0) / 1000000,  # 转换为ms
            }
            
            # 添加直接访问的字段，方便后续使用
            metrics['bw'] = metrics['global']['bw']
            metrics['iops'] = metrics['global']['iops']
            metrics['lat_p99'] = metrics['global']['lat_p99']
            metrics['lat_max'] = metrics['global']['lat_max']
            
            # 提取作业统计信息
            jobs = json_content.get('jobs', [])
            for job in jobs:
                job_name = job.get('jobname', 'unknown')
                job_stats = job.get('read', {}).get('stats', [{}])[0]
                metrics['jobs'].append({
                    'name': job_name,
                    'bw': job_stats.get('bw_bytes', 0) / 1024,  # 转换为KB/s
                    'iops': job_stats.get('iops', 0),
                    'lat': job_stats.get('lat_ns', {}).get('mean', 0) / 1000000,  # 转换为ms
                })
            
            # 提取详细的读写统计信息
            for rw_type in ['read', 'write']:
                rw_data = json_content.get('global', {}).get(rw_type, {})
                rw_stats = rw_data.get('stats', [{}])[0]
                metrics['detailed'][rw_type] = {
                    'bw': rw_stats.get('bw_bytes', 0) / 1024,  # 转换为KB/s
                    'iops': rw_stats.get('iops', 0),
                    'lat': rw_stats.get('lat_ns', {}).get('mean', 0) / 1000000,  # 转换为ms
                    'lat_p99': rw_stats.get('lat_ns', {}).get('percentile', {}).get('99.000000', 0) / 1000000,  # 转换为ms
                    'lat_min': rw_stats.get('lat_ns', {}).get('min', 0) / 1000000,  # 转换为ms
                    'lat_max': rw_stats.get('lat_ns', {}).get('max', 0) / 1000000,  # 转换为ms
                    'clat': rw_stats.get('clat_ns', {}).get('mean', 0) / 1000000,  # 转换为ms
                    'slat': rw_stats.get('slat_ns', {}).get('mean', 0) / 1000000,  # 转换为ms
                }
            
            logger.info(f"成功解析fio JSON日志，提取{len(metrics['jobs'])}个作业的性能指标: {log_path}")
            
        except Exception as e:
            logger.error(f"解析fio JSON日志失败: {e}", exc_info=True)
        
        return metrics
    
    def package_task_logs(self, task_id):
        """打包任务日志"""
        try:
            import shutil
            import tempfile
            
            # 获取任务信息
            from app.models import TestTask
            test_task = TestTask.query.get(task_id)
            if not test_task:
                logger.warning(f"任务不存在: task_id={task_id}")
                return None
            
            # 创建临时目录用于打包
            with tempfile.TemporaryDirectory() as temp_dir:
                # 获取任务的所有节点
                nodes = test_task.nodes
                
                # 创建任务目录结构
                task_dir_name = f'task_{task_id}_{test_task.name}'
                task_dir = os.path.join(temp_dir, task_dir_name)
                os.makedirs(task_dir, exist_ok=True)
                
                # 为每个节点打包日志
                for node in nodes:
                    if not node.login_credential:
                        logger.warning(f"节点 {node.ip_address} 没有登录凭证，跳过打包")
                        continue
                    
                    # 获取平台分区路径
                    platform_partition = node.login_credential.platform_partition
                    
                    # 规范化路径，统一使用正斜杠
                    platform_partition = platform_partition.replace('\\', '/')
                    
                    # 创建节点目录
                    node_dir = os.path.join(task_dir, f'node_{node.id}_{node.ip_address}')
                    os.makedirs(node_dir, exist_ok=True)
                    
                    # 获取任务专属的数据目录
                    task_data_dir = f"{platform_partition}/data/task_{task_id}"
                    task_data_dir = task_data_dir.replace('\\', '/')
                    
                    # 复制iostat日志
                    iostat_data_dir = f"{task_data_dir}/iostat_data"
                    iostat_data_dir = iostat_data_dir.replace('\\', '/')
                    if os.path.exists(iostat_data_dir):
                        import glob
                        iostat_files = glob.glob(f"{iostat_data_dir}/*")
                        if iostat_files:
                            node_iostat_dir = os.path.join(node_dir, 'iostat_data')
                            os.makedirs(node_iostat_dir, exist_ok=True)
                            for file in iostat_files:
                                shutil.copy(file, node_iostat_dir)
                    
                    # 复制fio日志
                    fio_data_dir = f"{task_data_dir}/fio_data"
                    fio_data_dir = fio_data_dir.replace('\\', '/')
                    if os.path.exists(fio_data_dir):
                        import glob
                        fio_files = glob.glob(f"{fio_data_dir}/*")
                        if fio_files:
                            node_fio_dir = os.path.join(node_dir, 'fio_data')
                            os.makedirs(node_fio_dir, exist_ok=True)
                            for file in fio_files:
                                shutil.copy(file, node_fio_dir)
                    
                    # 复制系统日志
                    system_data_dir = f"{task_data_dir}/system_logs"
                    system_data_dir = system_data_dir.replace('\\', '/')
                    if os.path.exists(system_data_dir):
                        import glob
                        system_files = glob.glob(f"{system_data_dir}/*")
                        if system_files:
                            node_system_dir = os.path.join(node_dir, 'system_logs')
                            os.makedirs(node_system_dir, exist_ok=True)
                            for file in system_files:
                                shutil.copy(file, node_system_dir)
                    
                    # 复制性能数据
                    performance_data_dir = f"{task_data_dir}/performance_data"
                    performance_data_dir = performance_data_dir.replace('\\', '/')
                    if os.path.exists(performance_data_dir):
                        import glob
                        performance_files = glob.glob(f"{performance_data_dir}/*")
                        if performance_files:
                            node_performance_dir = os.path.join(node_dir, 'performance_data')
                            os.makedirs(node_performance_dir, exist_ok=True)
                            for file in performance_files:
                                shutil.copy(file, node_performance_dir)
                
                # 从配置中获取本地数据存储目录
                from flask import current_app
                local_data_dir = current_app.config.get('LOCAL_DATA_DIR', './local_data')
                # 确保本地数据目录存在
                os.makedirs(local_data_dir, exist_ok=True)
                
                # 构建打包文件路径 - 使用正斜杠
                package_filename = f'task_{task_id}_logs.tar.gz'
                package_path = f"{local_data_dir}/{package_filename}"
                # 确保使用正斜杠
                package_path = package_path.replace('\\', '/')
                
                # 打包任务日志
                shutil.make_archive(os.path.splitext(package_path)[0], 'gztar', root_dir=temp_dir)
                
                logger.info(f"成功打包任务日志: {package_path}")
                return package_path
                
        except Exception as e:
            logger.error(f"打包任务日志失败: {e}", exc_info=True)
            return None
    
    def get_task_logs(self, task_id, node_id=None):
        """获取任务日志"""
        try:
            if node_id:
                # 确保node_id是整数类型
                node_id = int(node_id)
                # 获取指定节点的日志
                logs = TestLog.query.filter_by(
                    test_task_id=task_id,
                    node_id=node_id
                ).order_by(TestLog.collection_time.desc()).all()
            else:
                # 获取所有节点的日志
                logs = TestLog.query.filter_by(
                    test_task_id=task_id
                ).order_by(TestLog.node_id, TestLog.collection_time.desc()).all()
            
            return [log.to_dict() for log in logs]
            
        except Exception as e:
            logger.error(f"获取任务日志失败: {e}", exc_info=True)
    
    def get_realtime_metrics(self, task_id, node_id_list, device_list):
        """获取FIO日志指标数据（从本地日志文件获取，不上节点查询）"""
        try:
            logger.info(f"获取任务 {task_id} 的FIO日志指标数据，节点列表: {node_id_list}，设备列表: {device_list}")
            
            # 查询任务的所有FIO日志记录
            query = TestLog.query.filter_by(test_task_id=task_id, log_type='fio')
            
            # 如果提供了节点ID列表，添加节点过滤
            if node_id_list:
                query = query.filter(TestLog.node_id.in_(node_id_list))
            
            # 获取所有符合条件的日志记录
            logs = query.all()
            
            # 收集所有指标数据
            all_metrics = []
            
            for log in logs:
                try:
                    # 检查日志文件是否存在
                    if not os.path.exists(log.log_path):
                        logger.warning(f"日志文件不存在: {log.log_path}")
                        continue
                    
                    # 尝试解析FIO日志文件
                    fio_results = None
                    log_filename = os.path.basename(log.log_path)
                    
                    # 从文件名中提取设备信息
                    # 当前日志文件名格式：任务名_测试用例名_fio_时间戳.log
                    # 由于没有明确的设备信息，我们使用默认设备名
                    device = 'sda'  # 使用默认设备名
                    
                    # 检查设备是否在过滤列表中
                    # 如果设备列表为空，则返回所有设备的数据
                    if device_list and device not in device_list:
                        continue
                    
                    # 检查是否为JSON格式日志
                    if log_filename.endswith('.json'):
                        # 解析FIO JSON日志
                        fio_results = self._parse_fio_json_log(log.log_path)
                        
                        if not fio_results:
                            logger.warning(f"解析FIO JSON日志失败，结果为空: {log.log_path}")
                            continue
                        
                        # 提取IO模型名称（如果有）
                        io_model_name = fio_results.get('jobname', '未知IO模型')
                        
                        # 提取详细的读写指标
                        # 从global中获取全局指标
                        global_metrics = fio_results.get('global', {})
                        
                        # 构建读写指标
                        read_metrics = {
                            'iops': global_metrics.get('iops', 0),
                            'bw': global_metrics.get('bw', 0),
                            'lat': global_metrics.get('lat_ns', 0),
                            'lat_p99': global_metrics.get('lat_p99', 0),
                            'lat_max': global_metrics.get('lat_max', 0)
                        }
                        write_metrics = {
                            'iops': global_metrics.get('iops', 0),
                            'bw': global_metrics.get('bw', 0),
                            'lat': global_metrics.get('lat_ns', 0),
                            'lat_p99': global_metrics.get('lat_p99', 0),
                            'lat_max': global_metrics.get('lat_max', 0)
                        }
                        
                        # 提取开始时间和结束时间
                        start_time = fio_results.get('start_time', 0)
                        end_time = fio_results.get('end_time', 0)
                        
                        # 转换为统一格式
                        metric_data = {
                            'node_id': log.node_id,
                            'device': device,
                            'collection_time': log.collection_time,
                            'io_model_name': io_model_name,
                            'io_start_time': datetime.fromtimestamp(start_time),
                            'io_end_time': datetime.fromtimestamp(end_time),
                            'read_iops': read_metrics.get('iops', 0),
                            'write_iops': write_metrics.get('iops', 0),
                            'read_kbps': read_metrics.get('bw', 0),
                            'write_kbps': write_metrics.get('bw', 0),
                            'await_time': read_metrics.get('lat', 0),
                            'lat_p99': (read_metrics.get('lat_p99', 0) + write_metrics.get('lat_p99', 0)) / 2,  # 平均p99延迟
                            'lat_max': max(read_metrics.get('lat_max', 0), write_metrics.get('lat_max', 0)),  # 最大延迟
                            'svctm': 0,  # FIO日志中可能没有这个字段，使用默认值
                            'util': 0  # FIO日志中可能没有这个字段，使用默认值
                        }
                    else:
                        # 解析普通FIO日志
                        fio_results = self._parse_fio_log(log.log_path)
                        
                        # 处理FIO日志解析结果
                        if isinstance(fio_results, dict):
                            # 提取IO模型名称（如果有）
                            io_model_name = fio_results.get('jobs', [{}])[0].get('name', '未知IO模型')
                            
                            # 提取全局指标
                            global_metrics = fio_results.get('global', {})
                            
                            # 处理读写指标
                            # 检查是否有read/write字段，如果没有，直接使用global_metrics
                            if 'read' in global_metrics and 'write' in global_metrics:
                                read_metrics = global_metrics.get('read', {})
                                write_metrics = global_metrics.get('write', {})
                            else:
                                # 如果没有read/write字段，使用全局指标作为读写指标
                                read_metrics = {
                                    'iops': global_metrics.get('iops', 0),
                                    'bw': global_metrics.get('bw', 0),
                                    'lat': global_metrics.get('lat_ns', 0)
                                }
                                write_metrics = {
                                    'iops': global_metrics.get('iops', 0),
                                    'bw': global_metrics.get('bw', 0),
                                    'lat': global_metrics.get('lat_ns', 0)
                                }
                            
                            # 转换为统一格式
                            metric_data = {
                                'node_id': log.node_id,
                                'device': device,
                                'collection_time': log.collection_time,
                                'io_model_name': io_model_name,
                                'io_start_time': log.collection_time,  # 普通FIO日志中没有开始时间，使用收集时间
                                'io_end_time': log.collection_time,  # 普通FIO日志中没有结束时间，使用收集时间
                                'read_iops': float(read_metrics.get('iops', 0)),
                                'write_iops': float(write_metrics.get('iops', 0)),
                                'read_kbps': float(read_metrics.get('bw', 0)),
                                'write_kbps': float(write_metrics.get('bw', 0)),
                                'await_time': float(read_metrics.get('lat', 0)) if read_metrics.get('lat') else float(write_metrics.get('lat', 0)),
                                'lat_p99': float(global_metrics.get('lat_p99', 0)),
                                'lat_max': float(global_metrics.get('lat_max', 0)),
                                'svctm': 0,  # FIO日志中可能没有这个字段，使用默认值
                                'util': 0  # FIO日志中可能没有这个字段，使用默认值
                            }
                        else:
                            logger.warning(f"解析普通FIO日志失败，结果不是字典: {log.log_path}")
                            continue
                    
                    all_metrics.append(metric_data)
                except Exception as e:
                    logger.error(f"解析日志 {log.log_path} 失败: {e}")
                    continue
            
            logger.info(f"成功获取任务 {task_id} 的FIO日志指标数据，共 {len(all_metrics)} 条记录")
            return all_metrics
        except Exception as e:
            logger.error(f"获取FIO日志指标数据失败: {e}")
            return []
    
    def get_iostat_metrics(self, log_id, start_time=None, end_time=None):
        """获取iostat指标或FIO性能指标"""
        try:
            # 查询日志记录
            log = TestLog.query.get(log_id)
            if not log:
                logger.warning(f"日志不存在: log_id={log_id}")
                return []
            
            # 检查日志类型
            if log.log_type == 'iostat':
                # 获取iostat指标
                if start_time and end_time:
                    metrics = IOStatMetric.query.filter(
                        IOStatMetric.test_log_id == log_id,
                        IOStatMetric.collection_time >= start_time,
                        IOStatMetric.collection_time <= end_time
                    ).order_by(IOStatMetric.collection_time).all()
                else:
                    metrics = IOStatMetric.query.filter_by(
                        test_log_id=log_id
                    ).order_by(IOStatMetric.collection_time).all()
                
                return [metric.to_dict() for metric in metrics]
            elif log.log_type == 'fio':
                # 检查日志文件是否存在
                if not os.path.exists(log.log_path):
                    logger.warning(f"FIO日志文件不存在: {log.log_path}")
                    return []
                
                # 解析FIO日志
                log_filename = os.path.basename(log.log_path)
                if log_filename.endswith('.json'):
                    # 解析FIO JSON日志
                    fio_results = self._parse_fio_json_log(log.log_path)
                else:
                    # 解析普通FIO日志
                    fio_results = self._parse_fio_log(log.log_path)
                
                # 转换为统一格式
                metrics = []
                if isinstance(fio_results, dict):
                    # 从文件名中提取设备信息
                    device_match = re.search(r'_(\w+)\.(log|json)$', log_filename)
                    device = device_match.group(1) if device_match else 'unknown'
                    
                    if log_filename.endswith('.json'):
                        # 处理JSON格式日志
                        read_metrics = fio_results.get('detailed', {}).get('read', {})
                        write_metrics = fio_results.get('detailed', {}).get('write', {})
                        
                        # 提取开始时间和结束时间
                        start_time = fio_results.get('start_time', 0)
                        end_time = fio_results.get('end_time', 0)
                        
                        # 转换为统一格式
                        metric_data = {
                            'test_log_id': log_id,
                            'node_id': log.node_id,
                            'device': device,
                            'collection_time': log.collection_time,
                            'io_start_time': datetime.fromtimestamp(start_time),
                            'io_end_time': datetime.fromtimestamp(end_time),
                            'read_iops': read_metrics.get('iops', 0),
                            'write_iops': write_metrics.get('iops', 0),
                            'read_kbps': read_metrics.get('bw', 0),
                            'write_kbps': write_metrics.get('bw', 0),
                            'await_time': read_metrics.get('lat', 0),
                            'lat_p99': (read_metrics.get('lat_p99', 0) + write_metrics.get('lat_p99', 0)) / 2,
                            'lat_max': max(read_metrics.get('lat_max', 0), write_metrics.get('lat_max', 0)),
                            'svctm': 0,
                            'util': 0
                        }
                        metrics.append(metric_data)
                    else:
                        # 处理普通FIO日志
                        global_metrics = fio_results.get('global', {})
                        read_metrics = global_metrics.get('read', {})
                        write_metrics = global_metrics.get('write', {})
                        
                        # 转换为统一格式
                        metric_data = {
                            'test_log_id': log_id,
                            'node_id': log.node_id,
                            'device': device,
                            'collection_time': log.collection_time,
                            'read_iops': read_metrics.get('iops', '0'),
                            'write_iops': write_metrics.get('iops', '0'),
                            'read_kbps': read_metrics.get('bw', '0'),
                            'write_kbps': write_metrics.get('bw', '0'),
                            'await_time': read_metrics.get('lat', '0') if read_metrics.get('lat') else write_metrics.get('lat', '0'),
                            'lat_p99': 0,
                            'lat_max': 0,
                            'svctm': 0,
                            'util': 0
                        }
                        metrics.append(metric_data)
                
                return metrics
            else:
                logger.warning(f"不支持的日志类型: {log.log_type}")
                return []
            
        except Exception as e:
            logger.error(f"获取性能指标失败: {e}", exc_info=True)
            return []
    
    def calculate_jitter(self, metrics, metric_type):
        """计算性能抖动
        
        Args:
            metrics: 性能指标列表
            metric_type: 指标类型 (iops, bandwidth, latency)
            
        Returns:
            dict: 抖动计算结果
        """
        try:
            if not metrics:
                return {
                    'count': 0,
                    'mean': 0,
                    'std_dev': 0,
                    'jitter_percent': 0,
                    'min': 0,
                    'max': 0,
                    'p50': 0,
                    'p90': 0,
                    'p99': 0
                }
            
            # 提取指标值
            values = []
            for metric in metrics:
                if metric_type == 'iops':
                    value = metric.get('read_iops', 0) + metric.get('write_iops', 0)
                elif metric_type == 'bandwidth':
                    value = metric.get('read_kbps', 0) + metric.get('write_kbps', 0)
                elif metric_type == 'latency':
                    value = metric.get('await_time', 0)
                else:
                    continue
                values.append(value)
            
            if not values:
                return {
                    'count': 0,
                    'mean': 0,
                    'std_dev': 0,
                    'jitter_percent': 0,
                    'min': 0,
                    'max': 0,
                    'p50': 0,
                    'p90': 0,
                    'p99': 0
                }
            
            # 计算统计值
            count = len(values)
            mean = statistics.mean(values)
            std_dev = statistics.stdev(values) if count > 1 else 0
            min_val = min(values)
            max_val = max(values)
            
            # 计算抖动百分比
            jitter_percent = (std_dev / mean * 100) if mean > 0 else 0
            
            # 计算百分位
            sorted_values = sorted(values)
            p50 = sorted_values[int(count * 0.5)]
            p90 = sorted_values[int(count * 0.9)]
            p99 = sorted_values[int(count * 0.99)]
            
            return {
                'count': count,
                'mean': round(mean, 2),
                'std_dev': round(std_dev, 2),
                'jitter_percent': round(jitter_percent, 2),
                'min': round(min_val, 2),
                'max': round(max_val, 2),
                'p50': round(p50, 2),
                'p90': round(p90, 2),
                'p99': round(p99, 2)
            }
            
        except Exception as e:
            logger.error(f"计算性能抖动失败: {e}", exc_info=True)
            return {
                'count': 0,
                'mean': 0,
                'std_dev': 0,
                'jitter_percent': 0,
                'min': 0,
                'max': 0,
                'p50': 0,
                'p90': 0,
                'p99': 0
            }
    
    def get_performance_jitter(self, log_id, metric_type='iops'):
        """获取性能抖动数据"""
        try:
            # 获取iostat指标或FIO性能指标
            metrics = self.get_iostat_metrics(log_id)
            if not metrics:
                return {
                    'metric_type': metric_type,
                    'jitter': {
                        'count': 0,
                        'mean': 0,
                        'std_dev': 0,
                        'jitter_percent': 0,
                        'min': 0,
                        'max': 0,
                        'p50': 0,
                        'p90': 0,
                        'p99': 0
                    },
                    'raw_data': []
                }
            
            # 计算抖动
            jitter = self.calculate_jitter(metrics, metric_type)
            
            return {
                'metric_type': metric_type,
                'jitter': jitter,
                'raw_data': metrics
            }
            
        except Exception as e:
            logger.error(f"获取性能抖动数据失败: {e}", exc_info=True)
            return {
                'metric_type': metric_type,
                'jitter': {
                    'count': 0,
                    'mean': 0,
                    'std_dev': 0,
                    'jitter_percent': 0,
                    'min': 0,
                    'max': 0,
                    'p50': 0,
                    'p90': 0,
                    'p99': 0
                },
                'raw_data': []
            }

# 创建日志收集器实例
log_collector = LogCollector()