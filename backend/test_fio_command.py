#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 FIO 命令构建逻辑"""

import sys
sys.path.insert(0, '.')

# 模拟 fio_params
fio_params = {
    'io_type': ['read', 'write'],  # 多个 IO 类型
    'block_size': '4',
    'queue_depth': '16',
    'size': '1G',
    'runtime': '30',
    'time_based': True,
    'ioengine': 'libaio',
    'direct': True,
    'sync': False,
    'numjobs': '1',
    'filename': '/dev/vdb'
}

# 模拟回调函数
commands_logged = []

def log_callback(fio_cmd, io_type, iodepth, blocksize):
    commands_logged.append({
        'command': fio_cmd,
        'io_type': io_type,
        'iodepth': iodepth,
        'blocksize': blocksize
    })
    print(f"\n=== IO组合: io_type={io_type}, iodepth={iodepth}, blocksize={blocksize} ===")
    print(f"FIO命令: {fio_cmd}\n")

# 导入 SSHClient 的相关代码
from app.utils.ssh_client import SSHClient
from app.models import LoginCredential

# 创建一个模拟的登录凭证
class MockCredential:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 22
        self.username = 'test'
        self.password = 'test'

# 创建 SSH 客户端（不真正连接）
credential = MockCredential()
ssh = SSHClient.__new__(SSHClient)
ssh.credential = credential
ssh.hostname = '127.0.0.1'
ssh.client = None

# 测试命令构建
print("=" * 80)
print("测试多 IO 类型的 FIO 命令构建")
print("=" * 80)
print(f"\n输入参数: {fio_params}\n")

# 直接调用内部逻辑
# 这里我们手动模拟 run_fio_test 的逻辑
io_type = fio_params.get('io_type', fio_params.get('rw', 'read'))
io_types = []
if isinstance(io_type, list):
    io_types = [str(it).strip() for it in io_type if it.strip()]
elif isinstance(io_type, str) and ',' in io_type:
    io_types = [it.strip() for it in io_type.split(',') if it.strip()]
elif io_type:
    io_types = [str(io_type).strip()]
else:
    io_types = ['read']

print(f"解析出的 IO 类型列表: {io_types}\n")

# 获取队列深度和块大小
queue_depth = fio_params.get('queue_depth', '16')
block_size = fio_params.get('block_size', '4k')

# 处理块大小单位
if isinstance(block_size, str) and block_size.isdigit():
    block_size = f'{block_size}k'

print(f"队列深度: {queue_depth}")
print(f"块大小: {block_size}\n")

# 生成所有组合
all_combinations = []
for io in io_types:
    all_combinations.append({'io_type': io, 'iodepth': queue_depth, 'blocksize': block_size})

print(f"生成的组合数量: {len(all_combinations)}")
for i, combo in enumerate(all_combinations, 1):
    print(f"  组合 {i}: {combo}")

print("\n" + "=" * 80)
print("每个组合应该生成独立的 FIO 命令，而不是包含列表")
print("=" * 80)

# 模拟每个组合
for combo in all_combinations:
    io = combo['io_type']
    qd = combo['iodepth']
    bs = combo['blocksize']

    # 创建当前组合的参数
    current_params = fio_params.copy()
    current_params['io_type'] = io  # 单个值
    current_params['queue_depth'] = qd
    current_params['block_size'] = bs

    # 构建命令（简化版）
    cmd_parts = ['fio', '--name=diskbench_test']

    # 参数映射
    param_mapping = {'io_type': 'rw', 'block_size': 'bs', 'queue_depth': 'iodepth'}

    for key, value in current_params.items():
        if key in ['template_id', 'partitions', 'read_write_ratio', 'description']:
            continue

        mapped_key = param_mapping.get(key, key)

        if isinstance(value, bool):
            if value and key != 'time_based':
                cmd_parts.append(f'--{mapped_key}')
            elif key == 'time_based' and value:
                cmd_parts.append(f'--time_based')
        elif value:
            # 这里是关键：value 应该是单个值，不是列表
            val_str = str(value)
            cmd_parts.append(f'--{mapped_key}={val_str}')

    cmd = ' '.join(cmd_parts)
    log_callback(cmd, io, qd, bs)

print("=" * 80)
print("测试完成")
print(f"总共生成了 {len(commands_logged)} 个命令")
print("=" * 80)

# 检查是否有错误的列表格式
has_error = False
for i, logged in enumerate(commands_logged, 1):
    cmd = logged['command']
    if '[' in cmd and ']' in cmd:
        print(f"\n❌ 错误：命令 {i} 包含列表格式: {cmd}")
        has_error = True

if not has_error:
    print("\n✓ 所有命令格式正确，没有包含列表")
else:
    print("\n✗ 发现错误的命令格式")
