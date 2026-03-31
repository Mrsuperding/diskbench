#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查FIO命令记录"""

import requests
import json

# 获取一个任务的IO用例
response = requests.get('http://localhost:5003/api/tasks')
tasks = response.json()['data']

if tasks:
    task = tasks[0]
    task_id = task['id']
    print(f"任务ID: {task_id}")
    print(f"节点数: {len(task.get('nodes', []))}")
    print(f"IO用例数: {len(task.get('io_test_cases', []))}")
    
    # 显示IO用例的参数，计算会生成多少FIO命令
    for io_case in task.get('io_test_cases', []):
        print(f"\nIO用例: {io_case['name']}")
        params = io_case.get('parameters', {})
        
        # 获取各个参数的组合数
        io_types = params.get('io_type', [])
        if isinstance(io_types, str):
            io_types = [io_types]
        
        queue_depths = params.get('queue_depth', '16')
        if isinstance(queue_depths, str) and ',' in queue_depths:
            queue_depths = queue_depths.split(',')
        else:
            queue_depths = [queue_depths]
        
        block_sizes = params.get('block_size', '4k')
        if isinstance(block_sizes, str) and ',' in block_sizes:
            block_sizes = block_sizes.split(',')
        else:
            block_sizes = [block_sizes]
        
        total_combinations = len(io_types) * len(queue_depths) * len(block_sizes)
        
        print(f"  IO类型: {io_types} ({len(io_types)})")
        print(f"  队列深度: {queue_depths} ({len(queue_depths)})")
        print(f"  块大小: {block_sizes} ({len(block_sizes)})")
        print(f"  总FIO命令数: {total_combinations}")
    
    # 计算总的FIO命令数
    total_fio_commands = 0
    for io_case in task.get('io_test_cases', []):
        params = io_case.get('parameters', {})
        io_types = params.get('io_type', [])
        if isinstance(io_types, str):
            io_types = [io_types]
        
        queue_depths = params.get('queue_depth', '16')
        if isinstance(queue_depths, str) and ',' in queue_depths:
            queue_depths = queue_depths.split(',')
        else:
            queue_depths = [queue_depths]
        
        block_sizes = params.get('block_size', '4k')
        if isinstance(block_sizes, str) and ',' in block_sizes:
            block_sizes = block_sizes.split(',')
        else:
            block_sizes = [block_sizes]
        
        total_fio_commands += len(io_types) * len(queue_depths) * len(block_sizes)
    
    total_fio_commands *= len(task.get('nodes', []))
    
    print(f"\n总计:")
    print(f"  每个节点的FIO命令数: {total_fio_commands // max(len(task.get('nodes', [])), 1)}")
    print(f"  所有节点的FIO命令总数: {total_fio_commands}")
    
    # 检查已完成的测试结果
    print(f"\n检查test_results表...")
    # 这里需要直接查询数据库
