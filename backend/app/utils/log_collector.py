import os
import re
import datetime
import json
import logging
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
        # 设置日志存储目录
        self.log_base_dir = app.config.get('LOG_STORAGE_DIR', '/tmp/io_platform_logs')
        # 创建日志存储目录
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
            
            # 创建所需的目录结构
            iostat_data_dir = os.path.join(platform_partition, 'data', 'iostat_data')
            os.makedirs(iostat_data_dir, exist_ok=True)
            
            # 生成唯一标识（使用时间戳）
            unique_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
            
            # 构建本地日志文件名（任务名称+IO模型，包含唯一标识）
            local_log_filename = f'{task_name}_{io_test_case_name}_iostat_{unique_id}.log'
            local_log_path = os.path.join(iostat_data_dir, local_log_filename)
            
            # 下载iostat日志文件
            success, message = ssh_client.download_file(remote_log_path, local_log_path)
            if not success:
                logger.error(f"下载iostat日志失败: {message}")
                return None
            
            logger.info(f"成功下载iostat日志: {local_log_path}")
            
            # 解析iostat日志
            iostat_metrics = self._parse_iostat_log(local_log_path)
            
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
            
            # 创建所需的目录结构
            fio_data_dir = os.path.join(platform_partition, 'fio_data')
            os.makedirs(fio_data_dir, exist_ok=True)
            
            # 生成唯一标识（使用时间戳）
            unique_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
            
            # 构建本地日志文件名（任务名称+IO模型，包含唯一标识）
            local_log_filename = f'{task_name}_{io_test_case_name}_fio_{unique_id}.log'
            local_log_path = os.path.join(fio_data_dir, local_log_filename)
            
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
                    
                    # 创建节点目录
                    node_dir = os.path.join(task_dir, f'node_{node.id}_{node.ip_address}')
                    os.makedirs(node_dir, exist_ok=True)
                    
                    # 创建iostat_data目录
                    iostat_data_dir = os.path.join(platform_partition, 'data', 'iostat_data')
                    if os.path.exists(iostat_data_dir):
                        # 复制所有包含当前任务名称的iostat日志文件
                        import glob
                        iostat_files = glob.glob(os.path.join(iostat_data_dir, f'{test_task.name}_*.log'))
                        if iostat_files:
                            node_iostat_dir = os.path.join(node_dir, 'iostat_data')
                            os.makedirs(node_iostat_dir, exist_ok=True)
                            for file in iostat_files:
                                shutil.copy(file, node_iostat_dir)
                    
                    # 创建fio_data目录
                    fio_data_dir = os.path.join(platform_partition, 'fio_data')
                    if os.path.exists(fio_data_dir):
                        # 复制所有包含当前任务名称的fio日志文件
                        import glob
                        fio_files = glob.glob(os.path.join(fio_data_dir, f'{test_task.name}_*.log'))
                        if fio_files:
                            node_fio_dir = os.path.join(node_dir, 'fio_data')
                            os.makedirs(node_fio_dir, exist_ok=True)
                            for file in fio_files:
                                shutil.copy(file, node_fio_dir)
                
                # 构建打包文件路径
                package_filename = f'task_{task_id}_logs.tar.gz'
                package_path = os.path.join(self.log_base_dir, package_filename)
                
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
            return []
    
    def get_iostat_metrics(self, log_id, start_time=None, end_time=None):
        """获取iostat指标"""
        try:
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
            
        except Exception as e:
            logger.error(f"获取iostat指标失败: {e}", exc_info=True)
            return []

# 创建日志收集器实例
log_collector = LogCollector()