"""节点操作API"""

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import tempfile
from datetime import datetime

from app.models import db, Node
from app.utils.responses import success_response, error_response

node_operations_bp = Blueprint('node_operations', __name__)


@node_operations_bp.route('/check-connectivity', methods=['POST'])
@jwt_required()
def check_connectivity():
    """检测节点连通性"""
    try:
        data = request.get_json()
        node_ids = data.get('node_ids', [])

        if not node_ids:
            return error_response('请至少选择一个节点', 400)

        results = []
        for node_id in node_ids:
            node = Node.query.get(node_id)
            if not node:
                results.append({
                    'node_id': node_id,
                    'node_name': 'Unknown',
                    'connected': False,
                    'message': '节点不存在'
                })
                continue

            # TODO: 实现真实SSH连接测试
            # 当前使用模拟数据
            import random
            is_connected = random.choice([True, True, True, False])  # 75%概率连通

            results.append({
                'node_id': node.id,
                'node_name': node.name,
                'ip_address': node.ip_address,
                'connected': is_connected,
                'message': '连接成功' if is_connected else '连接失败',
                'checked_at': datetime.utcnow().isoformat()
            })

        return success_response(results, '连通性检测完成')
    except Exception as e:
        return error_response(f'连通性检测失败: {str(e)}', 500)


@node_operations_bp.route('/execute-command', methods=['POST'])
@jwt_required()
def execute_command():
    """执行Shell命令"""
    try:
        data = request.get_json()
        node_ids = data.get('node_ids', [])
        command = data.get('command', '')

        if not node_ids:
            return error_response('请至少选择一个节点', 400)

        if not command:
            return error_response('命令不能为空', 400)

        results = []
        for node_id in node_ids:
            node = Node.query.get(node_id)
            if not node:
                results.append({
                    'node_id': node_id,
                    'node_name': 'Unknown',
                    'success': False,
                    'message': '节点不存在'
                })
                continue

            # TODO: 实现真实SSH命令执行
            # 当前使用模拟数据 - 生成各种极端场景的测试数据
            import random

            # 随机选择不同的场景
            scenario = random.choice(['success_short', 'success_long', 'success_very_long', 'error', 'timeout'])

            if scenario == 'success_short':
                # 场景1: 简短的成功输出
                sample_output = f"""执行命令: {command}
节点: {node.name} ({node.ip_address})
========================================
total 48K
drwxr-xr-x 12 root root 4.0K Mar 28 10:00 .
drwxr-xr-x 20 root root 4.0K Mar 20 10:30 ..
-rw-r--r--  1 root root  220 Mar 15 09:00 test.log
drwxr-xr-x  2 root root 4.0K Mar 27 20:00 backup
========================================
命令执行成功"""
                results.append({
                    'node_id': node.id,
                    'node_name': node.name,
                    'success': True,
                    'message': '命令执行成功',
                    'output': sample_output,
                    'exit_code': 0,
                    'executed_at': datetime.utcnow().isoformat()
                })

            elif scenario == 'success_long':
                # 场景2: 较长的成功输出（模拟大量文件列表）
                file_list = "\n".join([
                    f"-rw-r--r--  1 root root {random.randint(100, 999999):8d} Mar {random.randint(1,28):2d} {random.randint(0,23):02d}:{random.randint(0,59):02d} file_{i:04d}.log"
                    for i in range(50)
                ])
                sample_output = f"""执行命令: {command}
节点: {node.name} ({node.ip_address})
========================================
磁盘空间检查结果:
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       500G  350G  150G  70% /
/dev/sdb1       1.0T  800G  200G  80% /data
/dev/sdc1       2.0T  1.5T  500G  75% /backup

文件列表 (共50个文件):
{file_list}

内存使用情况:
              total        used        free      shared  buff/cache   available
Mem:           62Gi        45Gi       5.0Gi       1.2Gi        12Gi        15Gi
Swap:          8.0Gi       2.1Gi       5.9Gi

进程信息:
  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
15234 root      20   0 1234567 456789  12345 S  25.3   5.2  12:34.56 fio
15235 mysql     20   0 9876543 234567  45678 S  15.7   3.1  56:78.90 mysqld
15236 nginx     20   0 5432109 123456  23456 S   8.3   1.5  23:45.67 nginx
========================================
命令执行成功，输出包含{len(file_list.split())}行数据"""
                results.append({
                    'node_id': node.id,
                    'node_name': node.name,
                    'success': True,
                    'message': '命令执行成功（大量输出）',
                    'output': sample_output,
                    'exit_code': 0,
                    'executed_at': datetime.utcnow().isoformat()
                })

            elif scenario == 'success_very_long':
                # 场景3: 超长输出（模拟日志查看）
                log_lines = "\n".join([
                    f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}.{random.randint(0,999):03d}] [{'INFO' if random.random() > 0.3 else 'WARN'}] "
                    f"[Thread-{random.randint(1,20)}] Processing request {i:06d} - "
                    f"{'Success' if random.random() > 0.2 else 'Retry'} - "
                    f"Duration: {random.randint(10,5000)}ms"
                    for i in range(100)
                ])
                sample_output = f"""执行命令: {command}
节点: {node.name} ({node.ip_address})
========================================
应用日志 (最近100条):

{log_lines}

========================================
日志总计: 100 条记录
INFO: 70 条 | WARN: 25 条 | ERROR: 5 条
平均响应时间: {random.randint(100,500)}ms
========================================
命令执行成功"""
                results.append({
                    'node_id': node.id,
                    'node_name': node.name,
                    'success': True,
                    'message': '命令执行成功（超长输出）',
                    'output': sample_output,
                    'exit_code': 0,
                    'executed_at': datetime.utcnow().isoformat()
                })

            elif scenario == 'error':
                # 场景4: 各种错误场景
                error_type = random.choice(['not_found', 'permission', 'syntax', 'disk_full'])

                if error_type == 'not_found':
                    error_output = f"""执行命令: {command}
节点: {node.name} ({node.ip_address})
========================================
bash: {command.split()[0] if command else 'command'}: command not found

可能的原因:
1. 命令不存在或未安装
2. 命令不在PATH环境变量中
3. 命令名称拼写错误

建议检查:
- 使用 'which {command.split()[0] if command else 'command'}' 查找命令位置
- 使用 'yum search' 或 'apt search' 搜索相关包
- 检查命令名称是否正确
========================================
命令执行失败 - 退出码: 127"""
                elif error_type == 'permission':
                    error_output = f"""执行命令: {command}
节点: {node.name} ({node.ip_address})
========================================
bash: {command}: Permission denied

错误详情:
- 当前用户: {random.choice(['nginx', 'mysql', 'app'])}
- 所需权限: root 或 sudo
- 文件权限: -rwx------ (仅所有者可执行)

解决方案:
1. 使用 sudo 执行命令
2. 切换到 root 用户
3. 修改文件权限: chmod +x filename
========================================
命令执行失败 - 退出码: 126"""
                elif error_type == 'syntax':
                    error_output = f"""执行命令: {command}
节点: {node.name} ({node.ip_address})
========================================
bash: syntax error near unexpected token `{random.choice(['(', ')', '|', '&', ';'])}'

语法错误详情:
第 1 行: {command}
             ^
             |
         错误位置

常见语法错误:
- 括号不匹配
- 管道符使用错误
- 引号未闭合
- 特殊字符未转义
========================================
命令执行失败 - 退出码: 2"""
                else:  # disk_full
                    error_output = f"""执行命令: {command}
节点: {node.name} ({node.ip_address})
========================================
write error: No space left on device

磁盘空间检查:
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       500G  500G     0 100% /
/dev/sdb1       1.0T  1.0T     0 100% /data

已满的分区:
/ : 100% (0 bytes available)
/data : 100% (0 bytes available)

建议操作:
1. 清理临时文件: rm -rf /tmp/*
2. 清理日志文件: find /var/log -name "*.log" -mtime +7 -delete
3. 检查大文件: du -sh /* | sort -rh | head -10
4. 扩展磁盘空间
========================================
命令执行失败 - 退出码: 1"""

                results.append({
                    'node_id': node.id,
                    'node_name': node.name,
                    'success': False,
                    'message': f'命令执行失败 - {error_type}',
                    'output': error_output,
                    'exit_code': random.randint(1, 127),
                    'executed_at': datetime.utcnow().isoformat()
                })

            else:  # timeout
                # 场景5: 超时场景
                timeout_output = f"""执行命令: {command}
节点: {node.name} ({node.ip_address})
========================================
命令执行中...
等待响应...
等待响应...
等待响应...

========================================
错误: 命令执行超时

超时信息:
- 设置的超时时间: 30 秒
- 实际执行时间: 30+ 秒
- 命令状态: 被强制终止

可能原因:
1. 命令执行时间过长
2. 进程卡死或等待输入
3. 网络I/O阻塞
4. 系统资源不足

建议:
- 增加超时时间
- 检查命令是否需要交互式输入
- 使用 nohup 或 & 放入后台执行
- 检查系统负载: top, htop
========================================
命令执行超时 - 进程已终止"""
                results.append({
                    'node_id': node.id,
                    'node_name': node.name,
                    'success': False,
                    'message': '命令执行超时',
                    'output': timeout_output,
                    'exit_code': 124,
                    'executed_at': datetime.utcnow().isoformat()
                })

        return success_response(results, '命令执行完成')
    except Exception as e:
        return error_response(f'命令执行失败: {str(e)}', 500)


@node_operations_bp.route('/upload-file', methods=['POST'])
@jwt_required()
def upload_file():
    """上传文件到节点"""
    try:
        # 获取表单数据
        node_ids = request.form.getlist('node_ids[]')
        remote_path = request.form.get('remote_path', '')
        file = request.files.get('file')

        if not node_ids:
            return error_response('请至少选择一个节点', 400)

        if not remote_path:
            return error_response('远程路径不能为空', 400)

        if not file:
            return error_response('请选择要上传的文件', 400)

        # 保存上传的文件到临时目录
        filename = secure_filename(file.filename)
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, filename)
        file.save(temp_file_path)

        results = []
        for node_id in node_ids:
            node = Node.query.get(int(node_id))
            if not node:
                results.append({
                    'node_id': int(node_id),
                    'node_name': 'Unknown',
                    'success': False,
                    'message': '节点不存在'
                })
                continue

            # TODO: 实现真实SSH文件上传
            # 当前使用模拟数据
            import random
            success = random.choice([True, True, False])

            if success:
                results.append({
                    'node_id': node.id,
                    'node_name': node.name,
                    'success': True,
                    'local_file': filename,
                    'remote_path': remote_path,
                    'file_size': os.path.getsize(temp_file_path),
                    'message': f'文件已上传到 {remote_path}',
                    'uploaded_at': datetime.utcnow().isoformat()
                })
            else:
                results.append({
                    'node_id': node.id,
                    'node_name': node.name,
                    'success': False,
                    'message': '文件上传失败',
                    'uploaded_at': datetime.utcnow().isoformat()
                })

        # 清理临时文件
        try:
            os.remove(temp_file_path)
        except:
            pass

        return success_response(results, '文件上传完成')
    except Exception as e:
        return error_response(f'文件上传失败: {str(e)}', 500)


@node_operations_bp.route('/download-file', methods=['POST'])
@jwt_required()
def download_file():
    """从节点下载文件"""
    try:
        data = request.get_json()
        node_id = data.get('node_id')
        remote_path = data.get('remote_path', '')

        if not node_id:
            return error_response('请选择节点', 400)

        if not remote_path:
            return error_response('远程路径不能为空', 400)

        node = Node.query.get(node_id)
        if not node:
            return error_response('节点不存在', 404)

        # TODO: 实现真实SSH文件下载
        # 当前返回模拟数据
        return success_response({
            'node_id': node.id,
            'node_name': node.name,
            'remote_path': remote_path,
            'message': '文件下载功能待实现（Phase 2）'
        })
    except Exception as e:
        return error_response(f'文件下载失败: {str(e)}', 500)


@node_operations_bp.route('/replace-file', methods=['POST'])
@jwt_required()
def replace_file():
    """替换节点上的文件（备份 + 上传）"""
    try:
        # 获取表单数据
        node_ids = request.form.getlist('node_ids[]')
        remote_path = request.form.get('remote_path', '')
        backup = request.form.get('backup', 'true') == 'true'
        file = request.files.get('file')

        if not node_ids:
            return error_response('请至少选择一个节点', 400)

        if not remote_path:
            return error_response('远程路径不能为空', 400)

        if not file:
            return error_response('请选择要上传的文件', 400)

        # 保存上传的文件
        filename = secure_filename(file.filename)
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, filename)
        file.save(temp_file_path)

        results = []
        for node_id in node_ids:
            node = Node.query.get(int(node_id))
            if not node:
                results.append({
                    'node_id': int(node_id),
                    'node_name': 'Unknown',
                    'success': False,
                    'message': '节点不存在'
                })
                continue

            # TODO: 实现真实SSH文件替换
            # 1. 如果需要备份，先备份原文件
            # 2. 上传新文件
            import random
            success = random.choice([True, True, False])

            if success:
                backup_path = f"{remote_path}.backup.{datetime.utcnow().strftime('%Y%m%d%H%M%S')}" if backup else None

                results.append({
                    'node_id': node.id,
                    'node_name': node.name,
                    'success': True,
                    'remote_path': remote_path,
                    'backup_path': backup_path,
                    'file_size': os.path.getsize(temp_file_path),
                    'message': '文件替换成功' + (f'，原文件已备份到 {backup_path}' if backup else ''),
                    'replaced_at': datetime.utcnow().isoformat()
                })
            else:
                results.append({
                    'node_id': node.id,
                    'node_name': node.name,
                    'success': False,
                    'message': '文件替换失败',
                    'replaced_at': datetime.utcnow().isoformat()
                })

        # 清理临时文件
        try:
            os.remove(temp_file_path)
        except:
            pass

        return success_response(results, '文件替换完成')
    except Exception as e:
        return error_response(f'文件替换失败: {str(e)}', 500)
