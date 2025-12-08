import re
from datetime import datetime

def validate_login_data(data):
    """验证登录数据"""
    if not data:
        return False, '请求数据不能为空'
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not (username or email):
        return False, '用户名或邮箱不能为空'
    
    if not password:
        return False, '密码不能为空'
    
    if username and (len(username) < 3 or len(username) > 50):
        return False, '用户名长度应在3-50个字符之间'
    
    if email:
        valid, msg = validate_email(email)
        if not valid:
            return valid, msg
    
    if len(password) < 6 or len(password) > 20:
        return False, '密码长度应在6-20个字符之间'
    
    return True, None

def validate_password_data(data):
    """验证密码数据"""
    if not data:
        return False, '请求数据不能为空'
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password:
        return False, '旧密码不能为空'
    
    if not new_password:
        return False, '新密码不能为空'
    
    if len(new_password) < 6 or len(new_password) > 20:
        return False, '新密码长度应在6-20个字符之间'
    
    if old_password == new_password:
        return False, '新密码不能与旧密码相同'
    
    return True, None

def validate_email(email):
    """验证邮箱格式"""
    if not email:
        return False, '邮箱不能为空'
    
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if not re.match(pattern, email):
        return False, '邮箱格式不正确'
    
    return True, None

def validate_username(username):
    """验证用户名格式"""
    if not username:
        return False, '用户名不能为空'
    
    if len(username) < 3 or len(username) > 50:
        return False, '用户名长度应在3-50个字符之间'
    
    # 只允许字母、数字、下划线和连字符
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, username):
        return False, '用户名只能包含字母、数字、下划线和连字符'
    
    return True, None

def validate_ip_address(ip):
    """验证IP地址格式"""
    if not ip:
        return False, 'IP地址不能为空'
    
    pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    if not re.match(pattern, ip):
        return False, 'IP地址格式不正确'
    
    return True, None

def validate_port(port):
    """验证端口号"""
    if not port:
        return False, '端口号不能为空'
    
    try:
        port_num = int(port)
        if port_num < 1 or port_num > 65535:
            return False, '端口号应在1-65535之间'
        return True, None
    except ValueError:
        return False, '端口号必须是数字'

def validate_fio_params(params):
    """验证fio参数"""
    errors = []
    
    # 必需参数
    required_params = ['filename', 'size', 'runtime']
    for param in required_params:
        if not params.get(param):
            errors.append(f'{param} 是必需参数')
    
    # 验证数值参数
    numeric_params = ['iodepth', 'numjobs', 'runtime', 'size']
    for param in numeric_params:
        if param in params:
            try:
                value = params[param]
                if isinstance(value, str):
                    # 处理带单位的数值
                    numeric_value = ''.join(filter(str.isdigit, str(value)))
                    if not numeric_value:
                        errors.append(f'{param} 必须是有效的数值')
                else:
                    int(value)
            except (ValueError, TypeError):
                errors.append(f'{param} 必须是有效的数值')
    
    # 验证块大小
    if 'bs' in params:
        bs = params['bs']
        valid_bs = ['512', '1k', '2k', '4k', '8k', '16k', '32k', '64k', '128k', '256k', '512k', '1m']
        if bs not in valid_bs:
            errors.append('bs 必须是有效的块大小')
    
    # 验证读写模式
    if 'rw' in params:
        rw = params['rw']
        valid_rw = ['read', 'write', 'randread', 'randwrite', 'rw', 'randrw']
        if rw not in valid_rw:
            errors.append('rw 必须是有效的读写模式')
    
    return len(errors) == 0, errors

def validate_vdbench_params(params):
    """验证vdbench参数"""
    errors = []
    
    # 必需参数
    if not params.get('f'):
        errors.append('f (parameter file) 是必需参数')
    
    return len(errors) == 0, errors

def validate_task_data(data):
    """验证任务数据"""
    errors = []
    
    if not data.get('name'):
        errors.append('任务名称不能为空')
    
    if not data.get('test_case_id'):
        errors.append('测试用例不能为空')
    
    if not data.get('target_nodes'):
        errors.append('目标节点不能为空')
    
    # 验证目标节点格式
    target_nodes = data.get('target_nodes', [])
    if not isinstance(target_nodes, list):
        errors.append('目标节点必须是数组')
    elif len(target_nodes) == 0:
        errors.append('至少选择一个目标节点')
    
    return len(errors) == 0, errors

def validate_node_data(data):
    """验证节点数据"""
    errors = []
    
    if not data.get('name'):
        errors.append('节点名称不能为空')
    
    if not data.get('login_credential_id'):
        errors.append('登录凭证不能为空')
    
    # 验证IP地址列表
    ip_list = data.get('ip_list', [])
    if not isinstance(ip_list, list):
        errors.append('IP地址列表必须是数组')
    elif len(ip_list) == 0:
        errors.append('至少需要一个IP地址')
    else:
        for ip in ip_list:
            valid, msg = validate_ip_address(ip)
            if not valid:
                errors.append(f'IP地址 {ip} 格式不正确')
                break
    
    # 验证分区列表
    partition_list = data.get('partition_list', [])
    if not isinstance(partition_list, list):
        errors.append('分区列表必须是数组')
    elif len(partition_list) == 0:
        errors.append('至少需要一个分区')
    
    return len(errors) == 0, errors

def validate_io_case_data(data):
    """验证IO用例数据"""
    errors = []
    
    if not data.get('name'):
        errors.append('用例名称不能为空')
    
    if not data.get('tool_type'):
        errors.append('工具类型不能为空')
    elif data['tool_type'] not in ['fio', 'vdbench']:
        errors.append('工具类型必须是 fio 或 vdbench')
    
    if not data.get('parameters'):
        errors.append('测试参数不能为空')
    
    return len(errors) == 0, errors

def sanitize_filename(filename):
    """清理文件名"""
    # 移除危险字符
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '../', './']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # 限制长度
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename.strip()

def validate_file_path(path):
    """验证文件路径"""
    if not path:
        return False, '文件路径不能为空'
    
    # 检查路径遍历攻击
    if '..' in path or path.startswith('/'):
        return False, '文件路径包含非法字符'
    
    return True, None