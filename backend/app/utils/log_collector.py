import os
import re
import datetime
import json
import logging
import statistics
from datetime import datetime, timedelta
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
        # 确保日志目录存在，递归创建
        os.makedirs(self.log_base_dir, exist_ok=True)
        # 验证目录权限
        if os.access(self.log_base_dir, os.W_OK):
            logger.info(f"日志收集器初始化完成，日志存储目录: {self.log_base_dir}")
            logger.info(f"目录权限检查: 可写")
        else:
            logger.warning(f"日志目录权限不足: {self.log_base_dir}")
            logger.warning(f"目录权限检查: 不可写")
    
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
        """解析iostat日志 - 使用动态列头解析"""
        metrics = []

        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()

            # iostat -xdm 1 的输出格式示例:
            # Device:         rrqm/s   wrqm/s     r/s     w/s    rMB/s    wMB/s avgrq-sz avgqu-sz   await r_await w_await  svctm  %util
            # sda               0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00    0.00    0.00   0.00   0.00

            # 查找包含Device行的索引并解析列头
            header_index = None
            col_map = {}

            for i, line in enumerate(lines):
                if line.strip().startswith('Device:') or ('Device' in line and ('rrqm/s' in line or 'r/s' in line)):
                    header_index = i
                    # 解析列头，建立列名到索引的映射
                    headers = line.split()
                    for idx, col_name in enumerate(headers):
                        # 去掉冒号
                        col_name = col_name.rstrip(':')
                        col_map[col_name] = idx
                    logger.info(f"iostat列头映射: {col_map}")
                    break

            if header_index is None or not col_map:
                logger.warning(f"iostat日志格式不正确，未找到设备行: {log_path}")
                return metrics

            # 定义需要的列名及其可能的别名
            # 不同版本的iostat可能使用不同的列名
            col_aliases = {
                'r/s': ['r/s', 'rs', 'read_io'],
                'w/s': ['w/s', 'ws', 'write_io'],
                'rMB/s': ['rMB/s', 'rkB/s', 'rKB/s', 'read_mb', 'rmb'],
                'wMB/s': ['wMB/s', 'wkB/s', 'wKB/s', 'write_mb', 'wmb'],
                'await': ['await', 'wait', 'avg_wait'],
                'svctm': ['svctm', 'svc_time', 'service_time'],
                '%util': ['%util', 'util', 'utilization', '%utilization']
            }

            # 根据别名查找实际的列索引
            def find_col_index(aliases):
                for alias in aliases:
                    if alias in col_map:
                        return col_map[alias]
                return None

            # 获取关键列的索引
            idx_r_s = find_col_index(col_aliases['r/s'])
            idx_w_s = find_col_index(col_aliases['w/s'])
            idx_rMB_s = find_col_index(col_aliases['rMB/s'])
            idx_wMB_s = find_col_index(col_aliases['wMB/s'])
            idx_await = find_col_index(col_aliases['await'])
            idx_svctm = find_col_index(col_aliases['svctm'])
            idx_util = find_col_index(col_aliases['%util'])

            logger.info(f"iostat关键列索引: r/s={idx_r_s}, w/s={idx_w_s}, rMB/s={idx_rMB_s}, wMB/s={idx_wMB_s}, await={idx_await}, svctm={idx_svctm}, %util={idx_util}")

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

                if 'Device:' in line or 'Device' in line:
                    # 新的设备头，重新解析列头
                    headers = line.split()
                    col_map = {}
                    for idx, col_name in enumerate(headers):
                        col_name = col_name.rstrip(':')
                        col_map[col_name] = idx

                    # 重新获取列索引
                    idx_r_s = find_col_index(col_aliases['r/s'])
                    idx_w_s = find_col_index(col_aliases['w/s'])
                    idx_rMB_s = find_col_index(col_aliases['rMB/s'])
                    idx_wMB_s = find_col_index(col_aliases['wMB/s'])
                    idx_await = find_col_index(col_aliases['await'])
                    idx_svctm = find_col_index(col_aliases['svctm'])
                    idx_util = find_col_index(col_aliases['%util'])

                    device_data = []
                    in_data_section = False
                    continue

                # 解析设备数据行
                parts = line.split()
                if len(parts) < 5:  # 至少需要设备名和几个数据字段
                    continue

                try:
                    device = parts[0]

                    # 使用动态索引提取数据
                    read_iops = float(parts[idx_r_s]) if idx_r_s is not None and len(parts) > idx_r_s else 0
                    write_iops = float(parts[idx_w_s]) if idx_w_s is not None and len(parts) > idx_w_s else 0

                    # 读写吞吐量，如果是rMB/s则转换为KB/s，如果是rkB/s则直接使用
                    read_throughput = float(parts[idx_rMB_s]) if idx_rMB_s is not None and len(parts) > idx_rMB_s else 0
                    write_throughput = float(parts[idx_wMB_s]) if idx_wMB_s is not None and len(parts) > idx_wMB_s else 0

                    # 判断单位是MB还是KB
                    read_col_name = None
                    for alias in col_aliases['rMB/s']:
                        if alias in col_map:
                            read_col_name = alias
                            break

                    if read_col_name and ('MB' in read_col_name or 'mb' in read_col_name):
                        read_kbps = read_throughput * 1024  # MB/s → KB/s
                        write_kbps = write_throughput * 1024
                    else:
                        read_kbps = read_throughput  # 已经是KB/s
                        write_kbps = write_throughput

                    await_time = float(parts[idx_await]) if idx_await is not None and len(parts) > idx_await else 0
                    svctm = float(parts[idx_svctm]) if idx_svctm is not None and len(parts) > idx_svctm else 0
                    util = float(parts[idx_util]) if idx_util is not None and len(parts) > idx_util else 0

                    metrics.append({
                        'timestamp': current_time - timedelta(seconds=len(lines[header_index+1:])-i),
                        'device': device,
                        'read_kbps': read_kbps,
                        'write_kbps': write_kbps,
                        'read_iops': read_iops,
                        'write_iops': write_iops,
                        'await_time': await_time,
                        'svctm': svctm,
                        'util': util
                    })
                except Exception as e:
                    logger.warning(f"解析iostat行失败: {e}, 行内容: {line}")
                    continue
            
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
            
            # 解析作业结果
            # 查找所有作业结果部分
            job_sections = re.findall(r'diskbench_test: \(groupid=0, jobs=1\):.*?Run status group 0 \(all jobs\):', content, re.DOTALL)
            
            for job_section in job_sections:
                # 提取作业名称
                job_name = 'diskbench_test'
                
                # 提取读写类型 - 在作业配置行查找
                rw_type_match = re.search(r'rw=(read|write|randread|randwrite|randrw|rw)', content)
                rw_type = rw_type_match.group(1) if rw_type_match else 'unknown'
                
                # 提取读性能指标
                read_match = re.search(r'  read: IOPS=(.*?), BW=(.*?)\(.*?\)', job_section)
                read_iops = read_match.group(1).strip() if read_match else '0'
                read_bw = read_match.group(2).strip() if read_match else '0'
                
                # 提取写性能指标
                write_match = re.search(r'  write: IOPS=(.*?), BW=(.*?)\(.*?\)', job_section)
                write_iops = write_match.group(1).strip() if write_match else '0'
                write_bw = write_match.group(2).strip() if write_match else '0'
                
                # 提取延迟指标
                lat_match = re.search(r'clat \(nsec\):.*?avg=(.*?),', job_section)
                lat = lat_match.group(1).strip() if lat_match else '0'
                
                # 提取最大延迟指标
                lat_max_match = re.search(r'clat \(nsec\):.*?max=(.*?)(,|\s)', job_section, re.DOTALL)
                lat_max = lat_max_match.group(1).strip() if lat_max_match else '0'
                
                # 提取P99延迟指标
                lat_p99_match = re.search(r'clat percentiles \(nsec\):.*?99\.00th=\[(.*?)\]', job_section, re.DOTALL)
                lat_p99 = lat_p99_match.group(1).strip() if lat_p99_match else '0'
                
                # 提取P9999延迟指标
                lat_p9999_match = re.search(r'clat percentiles \(nsec\):.*?99\.99th=\[(.*?)\]', job_section, re.DOTALL)
                lat_p9999 = lat_p9999_match.group(1).strip() if lat_p9999_match else '0'
                
                # 检查lat_p99的值，如果是小数形式（秒级），直接使用
                try:
                    lat_p99_val = float(lat_p99)
                    if lat_p99_val < 1000:
                        # 如果是小数，已经是秒级，直接使用
                        pass
                except:
                    pass
                
                # 转换IOPS值（处理k, M等单位）
                def convert_iops(iops_str):
                    iops_str = iops_str.strip()
                    if 'k' in iops_str:
                        return float(iops_str.replace('k', '')) * 1000
                    elif 'M' in iops_str:
                        return float(iops_str.replace('M', '')) * 1000000
                    else:
                        return float(iops_str)
                
                # 转换带宽值（处理MiB/s, KiB/s等单位）
                def convert_bw(bw_str):
                    bw_str = bw_str.strip()
                    if 'MiB/s' in bw_str:
                        return float(bw_str.replace('MiB/s', '')) * 1024  # 转换为KB/s
                    elif 'KiB/s' in bw_str:
                        return float(bw_str.replace('KiB/s', ''))
                    elif 'MB/s' in bw_str:
                        return float(bw_str.replace('MB/s', '')) * 1000  # 转换为KB/s
                    elif 'KB/s' in bw_str:
                        return float(bw_str.replace('KB/s', ''))
                    else:
                        return float(bw_str)
                
                # 转换延迟值（处理不同单位）
                def convert_lat(lat_str):
                    try:
                        lat_val = float(lat_str.strip())
                        
                        # 检查值的范围和格式
                        if lat_val < 0.1:
                            # 如果值小于0.1，很可能是秒级，转换为毫秒
                            return lat_val * 1000
                        elif lat_val < 1000:
                            # 如果值在0.1-1000之间，直接返回（已经是毫秒）
                            return lat_val
                        elif lat_val < 1000000:
                            # 如果值在1000-1000000之间，可能是微秒，转换为毫秒
                            return lat_val / 1000
                        else:
                            # 否则是纳秒，转换为毫秒
                            return lat_val / 1000000
                    except:
                        return 0.0
                
                # 添加作业指标
                metrics['jobs'].append({
                    'name': job_name,
                    'rw_type': rw_type,
                    'read_iops': convert_iops(read_iops),
                    'read_bw': convert_bw(read_bw),
                    'write_iops': convert_iops(write_iops),
                    'write_bw': convert_bw(write_bw),
                    'lat': convert_lat(lat),
                    'lat_p99': convert_lat(lat_p99),  # 添加P99延迟
                    'lat_p9999': convert_lat(lat_p9999),  # 添加P9999延迟
                    'lat_max': convert_lat(lat_max)  # 添加最大延迟
                })
            
            # 解析全局指标
            # 提取最后一个运行状态组的信息
            run_status_match = re.search(r'Run status group 0 \(all jobs\):.*?\n.*?\n', content, re.DOTALL)
            if run_status_match:
                run_status_content = run_status_match.group(0)
                
                # 提取读指标
                read_global_match = re.search(r'   READ: bw=(.*?)\(.*?\)', run_status_content)
                if read_global_match:
                    metrics['global']['read'] = {
                        'bw': convert_bw(read_global_match.group(1).strip()),
                        'iops': '0',
                        'lat': '0'
                    }
                
                # 提取写指标
                write_global_match = re.search(r'   WRITE: bw=(.*?)\(.*?\)', run_status_content)
                if write_global_match:
                    metrics['global']['write'] = {
                        'bw': convert_bw(write_global_match.group(1).strip()),
                        'iops': '0',
                        'lat': '0'
                    }
            
            # 如果没有找到全局指标，使用第一个作业的指标
            if not metrics['global'] and metrics['jobs']:
                first_job = metrics['jobs'][0]
                metrics['global'] = {
                    'read': {
                        'bw': first_job['read_bw'],
                        'iops': first_job['read_iops'],
                        'lat': first_job['lat'],
                        'lat_p99': first_job.get('lat_p99', 0),  # 添加P99延迟
                        'lat_p9999': first_job.get('lat_p9999', 0)  # 添加P9999延迟
                    },
                    'write': {
                        'bw': first_job['write_bw'],
                        'iops': first_job['write_iops'],
                        'lat': first_job['lat'],
                        'lat_p99': first_job.get('lat_p99', 0),  # 添加P99延迟
                        'lat_p9999': first_job.get('lat_p9999', 0)  # 添加P9999延迟
                    }
                }
            
            logger.info(f"成功解析fio日志，提取{len(metrics['jobs'])}个作业的性能指标: {log_path}")
            logger.debug(f"解析结果: {metrics}")
            
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
                'lat_p9999': global_stats.get('lat_ns', {}).get('percentile', {}).get('99.990000', 0) / 1000000,  # 转换为ms
                'clat_ns': global_stats.get('clat_ns', {}).get('mean', 0) / 1000000,  # 转换为ms
                'slat_ns': global_stats.get('slat_ns', {}).get('mean', 0) / 1000000,  # 转换为ms
            }
            
            # 添加直接访问的字段，方便后续使用
            metrics['bw'] = metrics['global']['bw']
            metrics['iops'] = metrics['global']['iops']
            metrics['lat_p99'] = metrics['global']['lat_p99']
            metrics['lat_p9999'] = metrics['global']['lat_p9999']
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
                    'lat_p9999': rw_stats.get('lat_ns', {}).get('percentile', {}).get('99.990000', 0) / 1000000,  # 转换为ms
                    'lat_min': rw_stats.get('lat_ns', {}).get('min', 0) / 1000000,  # 转换为ms
                    'lat_max': rw_stats.get('lat_ns', {}).get('max', 0) / 1000000,  # 转换为ms
                    'clat': rw_stats.get('clat_ns', {}).get('mean', 0) / 1000000,  # 转换为ms
                    'slat': rw_stats.get('slat_ns', {}).get('mean', 0) / 1000000,  # 转换为ms
                }
            
            logger.info(f"成功解析fio JSON日志，提取{len(metrics['jobs'])}个作业的性能指标: {log_path}")
            
        except Exception as e:
            logger.error(f"解析fio JSON日志失败: {e}", exc_info=True)
        
        return metrics
    
    def generate_io_model_name(self, node_count, vol_count, block_size, rw_type, queue_depth, thread_count):
        """生成IO模型名称

        格式: {节点数量}VM_{卷数量}VOL_{块大小}_{读写模式}_{队列深度}d_{线程数量}n
        """
        try:
            # 确保参数有效
            node_count = int(node_count) if node_count else 1
            vol_count = int(vol_count) if vol_count else 1
            block_size = block_size or '4k'
            rw_type = rw_type or 'randread'
            queue_depth = int(queue_depth) if queue_depth else 1
            thread_count = int(thread_count) if thread_count else 1

            # 生成模型名称
            io_model_name = f"{node_count}VM_{vol_count}VOL_{block_size}_{rw_type}_{queue_depth}d_{thread_count}n"
            logger.info(f"生成IO模型名称: {io_model_name}")
            return io_model_name
        except Exception as e:
            logger.error(f"生成IO模型名称失败: {e}")
            return "未知IO模型"
    
    def extract_test_config(self, content):
        """从日志内容中提取测试配置信息"""
        try:
            # 提取块大小，同时支持bs和blocksize参数
            block_size_match = re.search(r'(bs|blocksize)=(.*?),', content)
            block_size = block_size_match.group(2).strip() if block_size_match else '4k'
            
            # 提取读写模式
            rw_type_match = re.search(r'rw=(read|write|randread|randwrite|randrw|rw)', content)
            rw_type = rw_type_match.group(1).strip() if rw_type_match else 'randread'
            
            # 提取队列深度
            iodepth_match = re.search(r'iodepth=(\d+)', content)
            queue_depth = iodepth_match.group(1).strip() if iodepth_match else '1'
            
            # 提取线程数量
            numjobs_match = re.search(r'numjobs=(\d+)', content)
            thread_count = numjobs_match.group(1).strip() if numjobs_match else '1'
            
            return {
                'block_size': block_size,
                'rw_type': rw_type,
                'queue_depth': queue_depth,
                'thread_count': thread_count
            }
        except Exception as e:
            logger.error(f"提取测试配置失败: {e}")
            return {
                'block_size': '4k',
                'rw_type': 'randread',
                'queue_depth': '1',
                'thread_count': '1'
            }
    
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
        """获取实时FIO日志指标数据（从数据库中获取）"""
        try:
            logger.info(f"获取任务 {task_id} 的实时FIO日志指标数据，节点列表: {node_id_list}，设备列表: {device_list}")
            
            # 从数据库中获取性能数据
            from app.models.test_log import IOPerformanceData
            
            # 查询性能数据
            performance_data_list = IOPerformanceData.get_by_task_and_node_and_device(
                test_task_id=task_id,
                node_id_list=node_id_list,
                device_list=device_list
            )
            
            # 转换为前端需要的格式
            all_metrics = []
            for data in performance_data_list:
                metric_data = data.to_dict()
                # 转换时间格式为ISO格式字符串
                if metric_data['io_start_time']:
                    metric_data['io_start_time'] = data.io_start_time.isoformat()
                if metric_data['io_end_time']:
                    metric_data['io_end_time'] = data.io_end_time.isoformat()
                metric_data['collection_time'] = data.collection_time.isoformat()
                all_metrics.append(metric_data)
            
            # 按节点和分区分组，便于前端聚合
            grouped_metrics = {}
            for metric in all_metrics:
                key = f"{metric['node_id']}_{metric['device']}"
                if key not in grouped_metrics:
                    grouped_metrics[key] = []
                grouped_metrics[key].append(metric)
            
            logger.info(f"成功从数据库获取任务 {task_id} 的实时FIO日志指标数据，共 {len(all_metrics)} 条记录，分组后: {len(grouped_metrics)} 组")
            return all_metrics
        except Exception as e:
            logger.error(f"获取实时FIO日志指标数据失败: {e}")
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
                            'lat_p9999': (read_metrics.get('lat_p9999', 0) + write_metrics.get('lat_p9999', 0)) / 2,
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
                        jobs = fio_results.get('jobs', [])
                        
                        # 从jobs中获取lat_p99、lat_p9999和lat_max值
                        lat_p99 = 0
                        lat_p9999 = 0
                        lat_max = 0
                        if jobs:
                            first_job = jobs[0]
                            lat_p99 = (first_job.get('lat_p99', 0) + first_job.get('lat_p99', 0)) / 2
                            lat_p9999 = (first_job.get('lat_p9999', 0) + first_job.get('lat_p9999', 0)) / 2
                            lat_max = first_job.get('lat_max', 0)
                        
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
                            'lat_p99': lat_p99,
                            'lat_p9999': lat_p9999,
                            'lat_max': lat_max,
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