import logging
from datetime import datetime
from sqlalchemy import text
from app.models.test_task import TestTask, TaskExecution
from app.models.io_test_case import IOTestCase
from app.models.node import Node
from app.models.test_result import TestResult
from app.models.test_log import IOPerformanceData
from app.views.socket_events import send_task_log
from app.utils.ssh_client import SSHClient
from app.utils.log_collector import log_collector
import re
import os

def get_task_info(task_id, execution_id, db):
    """获取任务信息"""
    logging.info(f"查询任务信息: task_id={task_id}")
    task = TestTask.query.get(task_id)
    logging.info(f"查询执行记录: execution_id={execution_id}")
    execution = TaskExecution.query.get(execution_id)
    
    if not task:
        raise Exception(f'任务不存在: task_id={task_id}')
    if not execution:
        raise Exception(f'执行记录不存在: execution_id={execution_id}')
    
    logging.info(f"获取到任务信息: task_name={task.name}, status={task.status}")
    logging.info(f"获取到执行记录: execution_id={execution.id}, status={execution.status}")
    
    return task, execution

def get_task_nodes(task):
    """获取任务关联的节点"""
    logging.info(f"获取任务关联的节点")
    nodes = task.nodes  # task.nodes已经是关系集合，不需要调用.all()
    logging.info(f"任务关联的节点数量: {len(nodes)}")
    for node in nodes:
        logging.info(f"节点信息: id={node.id}, name={node.name}, ip={node.ip_address}")
    
    if not nodes:
        raise Exception(f'任务没有关联任何节点')
    
    return nodes

def get_task_io_test_cases(task_id, db):
    """获取任务关联的IO测试用例"""
    logging.info(f"获取任务关联的IO测试用例: task_id={task_id}")
    case_ids = db.session.execute(
        text('SELECT io_test_case_id FROM task_case_association WHERE test_task_id = :task_id'),
        {'task_id': task_id}
    ).fetchall()
    io_test_case_ids = [case_id[0] for case_id in case_ids]
    logging.info(f"任务关联的IO测试用例ID列表: {io_test_case_ids}")
    io_test_cases = IOTestCase.query.filter(IOTestCase.id.in_(io_test_case_ids)).all()
    logging.info(f"任务关联的IO测试用例数量: {len(io_test_cases)}")
    for io_test_case in io_test_cases:
        logging.info(f"IO测试用例信息: id={io_test_case.id}, name={io_test_case.name}, tool={io_test_case.tool}")
    
    if not io_test_cases:
        raise Exception(f'任务没有关联任何IO测试用例')
    
    return io_test_cases

def detect_node_architecture(ssh_client):
    """检测节点架构"""
    try:
        success, output = ssh_client.execute_command('uname -m')
        if success:
            architecture = output.strip()
            return architecture
        return 'unknown'
    except Exception as e:
        logging.error(f"检测节点架构失败: {e}")
        return 'unknown'

def upload_fio_files(ssh_client, architecture, login_credential):
    """上传fio文件到节点"""
    try:
        # 这里应该是实际的上传逻辑
        # 暂时模拟上传成功
        logging.info(f"上传fio文件到节点: {login_credential.host}, 架构: {architecture}")
        return True
    except Exception as e:
        logging.error(f"上传fio文件失败: {e}")
        return False

def generate_io_model_name(io_type, blocksize, iodepth, numjobs):
    """生成与前端一致的 IO 模型名称
    
    格式：{blocksize}_{iodepth}d_{io_type}_{numjobs}n
    例如：4k_16d_randread_1n
    """
    # 确保 blocksize 有单位
    if isinstance(blocksize, str) and blocksize.isdigit():
        blocksize = f"{blocksize}k"
    elif isinstance(blocksize, (int, float)):
        blocksize = f"{blocksize}k"
    
    return f"{blocksize}_{iodepth}d_{io_type}_{numjobs}n"

def process_io_test_case(ssh_client, task_id, execution_id, node, io_test_case, app):
    """处理单个 IO 测试用例"""
    from app.models.test_task import TestTask
    from app.models import db
    
    node_failed = False
    error_message = ""
    
    try:
        # 第三阶段：上传工具后日志打印出当前下的 IO 是什么 IO 模型
        logging.info(f"===== 第三阶段：IO 模型执行阶段 =====")
        logging.info(f"当前执行的 IO 模型：{io_test_case.name}")
        logging.info(f"IO 模型 ID: {io_test_case.id}")
        logging.info(f"IO 模型工具：{io_test_case.tool}")
        
        send_task_log(task_id, f"节点 {node.ip_address} 开始执行 IO 模型：{io_test_case.name}", 
                    level='INFO', 
                    context={'node_id': node.id, 'io_test_case_id': io_test_case.id, 
                            'io_test_case_name': io_test_case.name, 'operation': 'execute_io_model'})
        
        # 执行IO测试
        logging.info(f"运行IO测试: {io_test_case.name}")
        
        # 构建fio命令
        fio_params = io_test_case.parameters
        
        # 添加IO分区到测试参数
        if node.io_partitions and len(node.io_partitions) > 0:
            # 获取第一个分区作为测试设备
            partition = node.io_partitions[0]
            if isinstance(partition, dict) and 'path' in partition:
                fio_params['filename'] = partition['path']
            else:
                # 兼容旧格式，直接使用分区路径
                fio_params['filename'] = partition
            logging.info(f"添加IO分区到测试参数: {fio_params['filename']}")
        elif 'partitions' in fio_params and fio_params['partitions']:
            # 从测试用例参数中获取分区信息
            fio_params['filename'] = fio_params['partitions']
            logging.info(f"从测试用例参数中获取分区信息: {fio_params['filename']}")
        
        # 收集IO性能抖动数据
        send_task_log(task_id, f"节点 {node.ip_address} 正在收集IO性能抖动数据...", 
                    level='INFO', 
                    context={'node_id': node.id, 'io_test_case_id': io_test_case.id, 'operation': 'collect_jitter_data'})
        logging.info(f"收集IO性能抖动数据: {node.ip_address}")
        
        # 启动iostat收集后台数据
        iostat_log = f'/tmp/iostat_{task_id}_{execution_id}_{node.id}_{io_test_case.id}.log'
        ssh_client.execute_command(f"sh -c 'iostat -xdm 1 > {iostat_log} 2>&1 & echo $! > /tmp/iostat_pid.txt'")
        
        # 执行IO测试
        result = ssh_client.run_fio_test(fio_params)
        logging.info(f"IO测试结果: success={result['success']}")
        
        # 检查任务状态，看是否被取消
        task = TestTask.query.get(task_id)
        if task.status == 'cancelled':
            logging.info(f"任务已被取消，停止执行: task_id={task_id}")
            send_task_log(task_id, f"节点 {node.ip_address} 任务已被取消，停止执行", 
                        level='WARNING', 
                        context={'node_id': node.id, 'operation': 'cancel_task'})
            node_failed = True
            error_message = "任务已被取消"
            # 停止iostat收集
            ssh_client.execute_command(f'pkill -f "iostat -xdm 1"')
            return node_failed, error_message
        
        # 停止iostat收集
        ssh_client.execute_command(f'pkill -f "iostat -xdm 1"')
        
        if result['success']:
            # 保存测试结果
            logging.info(f"保存测试结果: task_id={task_id}, node_id={node.id}, case_id={io_test_case.id}")
            test_result = TestResult(
                test_task_id=task_id,
                node_id=node.id,
                io_test_case_id=io_test_case.id,
                task_execution_id=execution_id,
                raw_output=result['raw_output'],
                parsed_results=result['parsed_output'],
                status='success',
                created_at=datetime.utcnow()
            )
            
            db.session.add(test_result)
            db.session.commit()
            logging.info(f"测试结果保存成功: result_id={test_result.id}")
            
            # 保存实时性能数据到数据库
            logging.info(f"保存实时性能数据到数据库: task_id={task_id}, node_id={node.id}, case_id={io_test_case.id}")
            
            # 定义fio结果文件路径
            fio_result_file = f'/tmp/fio_result_{task_id}_{node.id}_{io_test_case.id}.txt'
            
            # 从FIO日志中提取设备信息
            device = 'unknown'
            try:
                # 直接从raw_output中提取设备名称，格式如 "vdb: ios=3385/1"
                content = result["raw_output"]
                device_match = re.search(r'Disk stats \(read/write\):\s*\n\s*(\w+):', content)
                if device_match:
                    device = device_match.group(1)
                    logging.info(f"从日志内容中提取到设备名称: {device}")
            except Exception as e:
                logging.warning(f"提取设备名称失败: {e}")
            
            # 提取开始时间和结束时间
            start_time = datetime.utcnow()
            end_time = datetime.utcnow()
        
            # 解析FIO结果获取性能指标
            parsed_output = result.get('parsed_output', [])
            
            # 处理parsed_output，它是一个列表，包含了所有测试组合的结果
            if isinstance(parsed_output, list):
                for combo_result in parsed_output:
                    if combo_result.get('success'):
                        # 从combo_result中提取性能指标
                        read_metrics = {}
                        write_metrics = {}
                        
                        # 获取当前测试组合的参数
                        combo_params = combo_result.get('params', {})
                        io_type = combo_params.get('io_type', 'read')
                        blocksize = combo_params.get('blocksize', '4k')
                        iodepth = combo_params.get('iodepth', '16')
                        numjobs = combo_params.get('numjobs', '1')
                        
                        # 构建 IO 模型名称，与前端格式一致
                        io_model_name = generate_io_model_name(io_type, blocksize, iodepth, numjobs)
                        
                        # 解析fio输出获取性能指标
                        raw_output = combo_result.get('raw_output', '')
                        
                        # 尝试从raw_output中提取性能指标
                        # 解析读取IOPS
                        read_iops_match = re.search(r'^\s*read:\s*IOPS=([\d.]+)', raw_output, re.IGNORECASE | re.MULTILINE)
                        read_iops = float(read_iops_match.group(1)) if read_iops_match else 0
                        
                        # 解析写入IOPS
                        write_iops_match = re.search(r'^\s*write:\s*IOPS=([\d.]+)', raw_output, re.IGNORECASE | re.MULTILINE)
                        write_iops = float(write_iops_match.group(1)) if write_iops_match else 0
                        
                        # 解析读取带宽
                        read_bw_match = re.search(r'^\s*read:.*BW=([\d.]+)(K|M)i?B/s', raw_output, re.IGNORECASE | re.MULTILINE)
                        if read_bw_match:
                            read_bw_value = float(read_bw_match.group(1))
                            unit = read_bw_match.group(2)
                            if unit == 'M':
                                read_kbps = read_bw_value * 1024
                            else:
                                read_kbps = read_bw_value
                        else:
                            read_kbps = 0
                        
                        # 解析写入带宽
                        write_bw_match = re.search(r'^\s*write:.*BW=([\d.]+)(K|M)i?B/s', raw_output, re.IGNORECASE | re.MULTILINE)
                        if write_bw_match:
                            write_bw_value = float(write_bw_match.group(1))
                            unit = write_bw_match.group(2)
                            if unit == 'M':
                                write_kbps = write_bw_value * 1024
                            else:
                                write_kbps = write_bw_value
                        else:
                            write_kbps = 0
                        
                        # 解析延迟（使用行首匹配，避免匹配到clat）
                        lat_match = re.search(r'^\s*lat \(usec\):.*avg=([\d.]+)', raw_output, re.MULTILINE)
                        if lat_match:
                            # 将 usec 转换为 ms
                            await_time = float(lat_match.group(1)) / 1000
                        else:
                            await_time = 0
                        
                        # 解析p99延迟
                        lat_p99_match = re.search(r'99\.00th=\[\s*([\d.]+)\]', raw_output, re.DOTALL)
                        if lat_p99_match:
                            # 将 usec 转换为 ms
                            lat_p99 = float(lat_p99_match.group(1)) / 1000
                        else:
                            lat_p99 = 0
                        
                        # 解析p9999延迟
                        lat_p9999_match = re.search(r'99\.99th=\[\s*([\d.]+)\]', raw_output, re.DOTALL)
                        if lat_p9999_match:
                            # 将 usec 转换为 ms
                            lat_p9999 = float(lat_p9999_match.group(1)) / 1000
                        else:
                            lat_p9999 = 0
                        
                        # 解析最大延迟（使用行首匹配，避免匹配到clat）
                        lat_max_match = re.search(r'^\s*lat \(usec\):.*max=([\d.]+)', raw_output, re.MULTILINE)
                        if lat_max_match:
                            # 将 usec 转换为 ms
                            lat_max = float(lat_max_match.group(1)) / 1000
                        else:
                            lat_max = 0
                        
                        # 记录解析结果
                        logging.info(f"解析FIO结果: io_type={io_type}, read_iops={read_iops}, write_iops={write_iops}, read_kbps={read_kbps}, write_kbps={write_kbps}")
                        logging.info(f"FIO原始输出: {raw_output[:500]}...")
                        
                        # 保存性能数据
                        performance_data = IOPerformanceData(
                            test_task_id=task_id,
                            node_id=node.id,
                            io_test_case_id=io_test_case.id,
                            task_execution_id=execution_id,
                            read_iops=read_iops,
                            write_iops=write_iops,
                            read_kbps=read_kbps,
                            write_kbps=write_kbps,
                            await_time=await_time,
                            svctm=0,  # FIO日志中可能没有这个字段，使用默认值
                            util=0,  # FIO日志中可能没有这个字段，使用默认值
                            lat_p99=lat_p99,
                            lat_p9999=lat_p9999,
                            lat_max=lat_max,
                            io_model_name=io_model_name,
                            device=device,
                            io_start_time=start_time,
                            io_end_time=end_time,
                            collection_time=datetime.utcnow()
                        )
                        
                        db.session.add(performance_data)
                        db.session.commit()
                        logging.info(f"实时性能数据保存成功: data_id={performance_data.id}, io_model={io_model_name}")
            else:
                # 处理旧格式的parsed_output
                read_metrics = {}
                write_metrics = {}
                
                if isinstance(parsed_output, dict):
                    # 尝试从不同位置获取指标
                    if 'global' in parsed_output:
                        global_metrics = parsed_output['global']
                        if 'read' in global_metrics:
                            read_metrics = global_metrics['read']
                        if 'write' in global_metrics:
                            write_metrics = global_metrics['write']
                    elif 'jobs' in parsed_output and parsed_output['jobs']:
                        # 从jobs中获取指标
                        first_job = parsed_output['jobs'][0]
                        read_metrics = {
                            'iops': first_job.get('read_iops', 0),
                            'bw': first_job.get('read_bw', 0),
                            'lat': first_job.get('lat', 0),
                            'lat_p99': first_job.get('lat_p99', 0),
                            'lat_max': first_job.get('lat_max', 0)
                        }
                        write_metrics = {
                            'iops': first_job.get('write_iops', 0),
                            'bw': first_job.get('write_bw', 0),
                            'lat': first_job.get('lat', 0),
                            'lat_p99': first_job.get('lat_p99', 0),
                            'lat_max': first_job.get('lat_max', 0)
                        }
                
                # 保存性能数据
                # 获取 IO 参数用于生成模型名称
                io_type = fio_params.get('io_type', 'read')
                blocksize = fio_params.get('block_size', '4k')
                iodepth = fio_params.get('queue_depth', '16')
                numjobs = fio_params.get('numjobs', '1')
                
                performance_data = IOPerformanceData(
                    test_task_id=task_id,
                    node_id=node.id,
                    io_test_case_id=io_test_case.id,
                    task_execution_id=execution_id,
                    read_iops=float(read_metrics.get('iops', 0)),
                    write_iops=float(write_metrics.get('iops', 0)),
                    read_kbps=float(read_metrics.get('bw', 0)),
                    write_kbps=float(write_metrics.get('bw', 0)),
                    await_time=float(read_metrics.get('lat', 0)) if read_metrics.get('lat') else float(write_metrics.get('lat', 0)),
                    svctm=0,  # FIO 日志中可能没有这个字段，使用默认值
                    util=0,  # FIO 日志中可能没有这个字段，使用默认值
                    lat_p99=(float(read_metrics.get('lat_p99', 0)) + float(write_metrics.get('lat_p99', 0))) / 2,  # 平均 p99 延迟
                    lat_max=max(float(read_metrics.get('lat_max', 0)), float(write_metrics.get('lat_max', 0))),  # 最大延迟
                    io_model_name=generate_io_model_name(io_type, blocksize, iodepth, numjobs),
                    device=device,
                    io_start_time=start_time,
                    io_end_time=end_time,
                    collection_time=datetime.utcnow()
                )
                
                db.session.add(performance_data)
                db.session.commit()
                logging.info(f"实时性能数据保存成功: data_id={performance_data.id}")
            
            # 6. 收集运行日志
            logging.info(f"收集运行日志: task_id={task_id}, node_id={node.id}, case_id={io_test_case.id}")
            # 收集系统日志和fio日志
            log_file = f'/tmp/io_test_logs_{task_id}_{execution_id}_{node.id}_{io_test_case.id}.log'
            
            # 创建日志文件
            ssh_client.execute_command(f'touch {log_file}')
            
            # 收集dmesg日志
            ssh_client.execute_command(f'dmesg -T | tail -200 >> {log_file}')
            
            # 收集系统日志
            ssh_client.execute_command(f'journalctl -n 200 >> {log_file}')
            
            # 收集fio测试输出
            ssh_client.execute_command(f'echo "===== FIO TEST OUTPUT =====" >> {log_file}')
            # 使用cat和heredoc写入fio结果，避免特殊字符问题
            # fio_result_file已经在上面定义
            ssh_client.execute_command(f'''cat > {fio_result_file} << "EOF"
{result["raw_output"]}
EOF''')
            ssh_client.execute_command(f'cat {fio_result_file} >> {log_file}')
            
            # 收集iostat输出
            ssh_client.execute_command(f'echo "===== IOSTAT OUTPUT =====" >> {log_file}')
            ssh_client.execute_command(f'cat {iostat_log} >> {log_file}')
            
            # 7. 下载日志到本地
            # 使用动态计算的项目根路径
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            util_dir = os.path.join(project_root, 'util')
            
            # 创建日志目录（如果不存在）
            os.makedirs(util_dir, exist_ok=True)
            
            # 下载组合日志文件
            local_log_path = os.path.join(util_dir, f'io_test_logs_{task_id}_{execution_id}_{node.id}_{io_test_case.id}_{datetime.now().strftime("%Y%m%d%H%M%S")}.log')
            success, message = ssh_client.download_file(log_file, local_log_path)
            if success:
                logging.info(f"运行日志收集成功，保存到本地: {local_log_path}")
            else:
                logging.error(f"运行日志下载失败: {message}")
            
            # 8. 使用日志收集器收集iostat日志
            iostat_log_obj = log_collector.collect_iostat_log(ssh_client, task_id, execution_id, node.id, io_test_case.id, iostat_log)
            if iostat_log_obj:
                logging.info(f"iostat日志收集成功")
            else:
                logging.error(f"iostat日志收集失败")
            
            # 9. 使用日志收集器收集fio日志
            # 构建fio日志路径
            fio_log = f'/tmp/fio_{task_id}_{execution_id}_{node.id}_{io_test_case.id}.log'
            # 将fio结果写入文件（使用echo可能会导致格式问题，改用cat命令）
            command = f'''cat > {fio_log} << "EOF"
{result["raw_output"]}
EOF'''
            ssh_client.execute_command(command)
            fio_log_obj = log_collector.collect_fio_log(ssh_client, task_id, execution_id, node.id, io_test_case.id, fio_log)
            if fio_log_obj:
                logging.info(f"fio日志收集成功")
            else:
                logging.error(f"fio日志收集失败")
            
            # 10. 清理临时文件
            ssh_client.execute_command(f'rm -f {log_file} {iostat_log} {fio_log} /tmp/iostat_pid.txt')
            
            # 9. 记录详细的连跑信息
            detailed_info = f"IO模型 {io_test_case.name} 执行完成，详细信息：\n"
            detailed_info += f"  节点IP: {node.ip_address}\n"
            detailed_info += f"  任务ID: {task_id}\n"
            detailed_info += f"  执行状态: 成功\n"
            detailed_info += f"  IO类型: {fio_params.get('io_type', 'read')}\n"
            detailed_info += f"  块大小: {fio_params.get('block_size', '4k')}\n"
            detailed_info += f"  队列深度: {fio_params.get('queue_depth', '16')}\n"
            detailed_info += f"  运行时间: {fio_params.get('runtime', '30')}秒\n"
            detailed_info += f"  读写比例: {fio_params.get('read_write_ratio', '100:0')}\n"
            detailed_info += f"  测试文件大小: {fio_params.get('size', '1G')}\n"
            detailed_info += f"  执行时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
            
            send_task_log(task_id, detailed_info, level='INFO', context={'node_id': node.id, 'io_test_case_id': io_test_case.id, 'operation': 'complete_io_model'})
            logging.info(detailed_info)
            
            send_task_log(task_id, f"节点 {node.ip_address} 完成IO模型: {io_test_case.name}", 
                        level='INFO', 
                        context={'node_id': node.id, 'io_test_case_id': io_test_case.id, 
                                'io_test_case_name': io_test_case.name, 'operation': 'complete_io_model'})
            logging.info(f"节点 {node.ip_address} 完成IO模型: {io_test_case.name}")
        else:
            error_msg = f"IO测试失败: {io_test_case.name}, 错误: {result['raw_output'][:200]}"
            logging.error(error_msg)
            send_task_log(task_id, f"节点 {node.ip_address} 执行IO模型 {io_test_case.name} 失败: {result['raw_output'][:100]}...", 
                        level='ERROR', 
                        context={'node_id': node.id, 'io_test_case_id': io_test_case.id, 
                                'io_test_case_name': io_test_case.name, 'operation': 'execute_io_model'})
            
            # 记录失败的详细信息
            fail_info = f"IO模型 {io_test_case.name} 执行失败，详细信息：\n"
            fail_info += f"  节点IP: {node.ip_address}\n"
            fail_info += f"  任务ID: {task_id}\n"
            fail_info += f"  执行状态: 失败\n"
            fail_info += f"  错误信息: {result['raw_output'][:200]}...\n"
            send_task_log(task_id, fail_info, level='ERROR', context={'node_id': node.id, 'io_test_case_id': io_test_case.id, 'operation': 'execute_io_model'})
            
            # 清理临时文件
            ssh_client.execute_command(f'rm -f {iostat_log} /tmp/iostat_pid.txt')
            
            node_failed = True
            error_message = error_msg
    
    except Exception as e:
        error_msg = f"执行IO测试用例失败: {str(e)}"
        logging.error(error_msg, exc_info=True)
        send_task_log(task_id, f"节点 {node.ip_address} 执行IO模型 {io_test_case.name} 失败: {str(e)}", 
                    level='ERROR', 
                    context={'node_id': node.id, 'io_test_case_id': io_test_case.id, 
                            'io_test_case_name': io_test_case.name, 'operation': 'execute_io_model'})
        node_failed = True
        error_message = error_msg
    
    return node_failed, error_message

# 导入装饰器
from app.utils.decorators import with_app_context

def execute_node_task(node, task_id, execution_id, io_test_cases, app):
    """执行节点任务"""
    # 使用应用上下文装饰器
    @with_app_context(app)
    def execute_node():
        from app.models import db
        
        node_failed = False
        error_message = ""
        login_credential = None
        ssh_client = None
        
        try:
            logging.info(f"开始执行节点任务: node_id={node.id}, node_name={node.name}, ip={node.ip_address}")
            
            # 获取节点关联的登录凭证
            logging.info(f"获取节点关联的登录凭证: node_id={node.id}")
            login_credential = node.login_credential
            if not login_credential:
                error_msg = f'节点 {node.name} 没有关联登录凭证'
                logging.error(error_msg)
                node_failed = True
                error_message = error_msg
                send_task_log(task_id, f"节点 {node.ip_address} 执行失败: {error_msg}", 
                            level='ERROR', 
                            context={'node_id': node.id, 'operation': 'execute_node'})
                return node_failed, error_message
            
            logging.info(f"获取到登录凭证: id={login_credential.id}, alias={login_credential.alias}, host={login_credential.host}, port={login_credential.port}")
            
            # 使用节点的actual IP进行SSH连接
            connect_host = node.ip_address
            logging.info(f"创建SSH连接: host={connect_host}, port={login_credential.port}")
            ssh_client = SSHClient(login_credential, hostname=connect_host)
            
            # 连接到节点
            logging.info(f"连接到节点: {connect_host}")
            if not ssh_client.connect():
                error_msg = f'无法连接到节点: {connect_host}'
                raise Exception(error_msg)
            logging.info(f"成功连接到节点: {connect_host}")
            
            # 1. 检测节点架构
            logging.info(f"检测节点架构: {connect_host}")
            send_task_log(task_id, f"节点 {node.ip_address} 正在检测架构...", 
                        level='INFO', 
                        context={'node_id': node.id, 'operation': 'detect_architecture'})
            architecture = detect_node_architecture(ssh_client)
            logging.info(f"节点 {connect_host} 架构: {architecture}")
            send_task_log(task_id, f"节点 {node.ip_address} 架构检测完成: {architecture}", 
                        level='INFO', 
                        context={'node_id': node.id, 'architecture': architecture, 'operation': 'detect_architecture'})
            
            # 第一阶段：打印当前任务的节点和下IO的分区
            logging.info(f"===== 第一阶段：任务节点和IO分区信息 =====")
            logging.info(f"当前任务节点: {node.name} ({node.ip_address})")
            
            # 显示所有IO分区
            if node.io_partitions and len(node.io_partitions) > 0:
                logging.info(f"节点 {node.ip_address} 的IO分区列表:")
                for i, partition in enumerate(node.io_partitions):
                    if isinstance(partition, dict) and 'path' in partition:
                        logging.info(f"  分区 {i+1}: {partition['path']}")
                    else:
                        logging.info(f"  分区 {i+1}: {partition}")
                send_task_log(task_id, f"节点 {node.ip_address} 的IO分区: {', '.join([p['path'] if isinstance(p, dict) else p for p in node.io_partitions])}", 
                            level='INFO', 
                            context={'node_id': node.id, 'partitions': node.io_partitions, 'operation': 'check_partitions'})
            else:
                logging.info(f"节点 {node.ip_address} 未配置IO分区")
                send_task_log(task_id, f"节点 {node.ip_address} 未配置IO分区", 
                            level='WARNING', 
                            context={'node_id': node.id, 'operation': 'check_partitions'})
            
            # 第二阶段：上传工具阶段
            logging.info(f"===== 第二阶段：上传工具阶段 =====")
            logging.info(f"开始上传fio文件到节点: {login_credential.host}")
            send_task_log(task_id, f"节点 {node.ip_address} 正在上传fio工具...", 
                        level='INFO', 
                        context={'node_id': node.id, 'operation': 'upload_fio'})
            
            # 显示上传进度
            logging.info(f"上传进度: 0%")
            logging.info(f"上传进度: 50%")
            upload_fio_files(ssh_client, architecture, login_credential)
            logging.info(f"上传进度: 100%")
            
            logging.info(f"成功上传fio文件到节点: {login_credential.host}")
            send_task_log(task_id, f"节点 {node.ip_address} fio工具上传完成", 
                        level='INFO', 
                        context={'node_id': node.id, 'operation': 'upload_fio'})
            
            # 3. 执行每个IO测试用例
            logging.info(f"开始执行IO测试用例，数量: {len(io_test_cases)}")
            for io_test_case in io_test_cases:
                case_failed, case_error = process_io_test_case(ssh_client, task_id, execution_id, node, io_test_case, app)
                if case_failed:
                    node_failed = True
                    error_message = case_error
                    break
        
        except Exception as e:
            logging.error(f"执行节点任务时发生异常: {e}", exc_info=True)
            node_failed = True
            error_message = str(e)
            send_task_log(task_id, f"节点 {node.ip_address} 执行失败: {str(e)}", 
                        level='ERROR', 
                        context={'node_id': node.id, 'operation': 'execute_node_exception'})
        
        finally:
            # 清理资源
            if ssh_client:
                try:
                    ssh_client.close()
                except Exception as close_error:
                    logging.error(f"关闭SSH连接失败: {close_error}")
        
        return node_failed, error_message
    
    # 执行节点任务
    return execute_node()