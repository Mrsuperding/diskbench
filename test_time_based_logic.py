# 测试time_based参数处理逻辑

def test_time_based_parameter():
    """测试time_based参数是否正确处理"""
    
    # 模拟fio参数
    fio_params_with_time_based = {
        "io_type": "randread",
        "block_size": "4",
        "queue_depth": "16",
        "runtime": 30,
        "size": "1G",
        "time_based": True
    }
    
    fio_params_without_time_based = {
        "io_type": "randread",
        "block_size": "4",
        "queue_depth": "16",
        "runtime": 30,
        "size": "1G",
        "time_based": False
    }
    
    # 模拟SSHClient中的参数处理逻辑
    def build_cmd_parts(params):
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
        
        # 处理用户定义的参数
        for key, value in params.items():
            if key in ['template_id', 'partitions', 'read_write_ratio']:
                continue
            
            mapped_key = param_mapping.get(key, key)
            val = value
            
            # 特殊处理time_based参数
            if key == 'time_based':
                # 只在time_based为True时添加参数
                if val:
                    parts.append('--time_based=1')
                continue
            
            if isinstance(val, bool):
                val = '1' if val else '0'
            elif not isinstance(val, str):
                val = str(val).strip()
            else:
                val = val.strip()
            
            if not val:
                continue
            
            if mapped_key in fio_supported_params:
                parts.append(f'--{mapped_key}={val}')
            else:
                parts.append(f'--{mapped_key}={val}')
        
        return parts
    
    # 测试带time_based的参数
    cmd_with_time_based = build_cmd_parts(fio_params_with_time_based)
    print("带time_based参数的命令:")
    print(' '.join(cmd_with_time_based))
    print()
    
    # 测试不带time_based的参数
    cmd_without_time_based = build_cmd_parts(fio_params_without_time_based)
    print("不带time_based参数的命令:")
    print(' '.join(cmd_without_time_based))
    print()
    
    # 检查结果
    has_time_based = any('--time_based=1' in part for part in cmd_with_time_based)
    no_time_based = not any('--time_based=' in part for part in cmd_without_time_based)
    
    print(f"测试结果:")
    print(f"带time_based参数的命令包含 --time_based=1: {has_time_based}")
    print(f"不带time_based参数的命令不包含 --time_based: {no_time_based}")
    
    if has_time_based and no_time_based:
        print("\n测试通过: time_based参数处理正确")
    else:
        print("\n测试失败: time_based参数处理不正确")

if __name__ == "__main__":
    test_time_based_parameter()
