# 测试修改后的SSHClient time_based参数处理逻辑

# 模拟修改后的SSHClient中的参数处理逻辑
def build_cmd_parts(params, current_iodepth=None, current_blocksize=None):
    parts = ['fio']
    parts.append('--name=diskbench_test')
    
    # 定义fio支持的核心参数列表
    fio_supported_params = [
        'rw', 'blocksize', 'iodepth', 'filename', 'size', 'runtime', 'numjobs', 
        'iodepth_batch_submit', 'iodepth_batch_complete', 'rwmixread', 'rwmixwrite', 
        'bs', 'ioengine', 'direct', 'sync', 'norandommap', 'randrepeat', 'group_reporting', 
        'name', 'output', 'stonewall', 'overwrite', 'time_based'
    ]
    
    # 定义参数转换映射
    param_mapping = {
        'io_type': 'rw',
        'block_size': 'blocksize',
        'queue_depth': 'iodepth'
    }
    
    # 处理读写比例参数
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
        
        # 特殊处理time_based参数
        if key == 'time_based':
            # 只在time_based为True时添加参数
            if val:
                parts.append('--time_based=1')
            continue
        
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
    
    # 添加默认runtime=30（如果用户未指定）
    if not any('--runtime=' in part for part in parts):
        parts.append('--runtime=30')
    
    # 添加默认group_reporting（如果用户未指定）
    if not any('--group_reporting' in part for part in parts):
        parts.append('--group_reporting')
    
    return parts

def test_time_based_parameter():
    """测试time_based参数是否正确处理"""
    
    # 测试用例1: time_based=True
    print("测试用例1: time_based=True")
    fio_params_with_time_based = {
        "io_type": "randread",
        "block_size": "4",
        "queue_depth": "16",
        "runtime": 30,
        "size": "1G",
        "time_based": True
    }
    cmd_with_time_based = build_cmd_parts(fio_params_with_time_based)
    print(' '.join(cmd_with_time_based))
    has_time_based = any('--time_based=1' in part for part in cmd_with_time_based)
    print(f"包含 --time_based=1: {has_time_based}")
    print()
    
    # 测试用例2: time_based=False
    print("测试用例2: time_based=False")
    fio_params_without_time_based = {
        "io_type": "randread",
        "block_size": "4",
        "queue_depth": "16",
        "runtime": 30,
        "size": "1G",
        "time_based": False
    }
    cmd_without_time_based = build_cmd_parts(fio_params_without_time_based)
    print(' '.join(cmd_without_time_based))
    no_time_based = not any('--time_based' in part for part in cmd_without_time_based)
    print(f"不包含 --time_based: {no_time_based}")
    print()
    
    # 测试用例3: 不指定time_based（默认False）
    print("测试用例3: 不指定time_based")
    fio_params_no_time_based = {
        "io_type": "randread",
        "block_size": "4",
        "queue_depth": "16",
        "runtime": 30,
        "size": "1G"
    }
    cmd_no_time_based = build_cmd_parts(fio_params_no_time_based)
    print(' '.join(cmd_no_time_based))
    no_time_based_default = not any('--time_based' in part for part in cmd_no_time_based)
    print(f"不包含 --time_based: {no_time_based_default}")
    print()
    
    # 检查所有测试用例结果
    all_passed = has_time_based and no_time_based and no_time_based_default
    
    print(f"测试结果:")
    print(f"测试用例1 (time_based=True): {'通过' if has_time_based else '失败'}")
    print(f"测试用例2 (time_based=False): {'通过' if no_time_based else '失败'}")
    print(f"测试用例3 (默认): {'通过' if no_time_based_default else '失败'}")
    
    if all_passed:
        print("\n所有测试用例通过: time_based参数处理正确")
    else:
        print("\n测试失败: time_based参数处理不正确")

if __name__ == "__main__":
    test_time_based_parameter()
