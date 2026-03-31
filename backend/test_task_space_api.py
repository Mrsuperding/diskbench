#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试任务空间ID是否正确返回"""

import requests
import json

# 测试获取任务列表
response = requests.get('http://localhost:5003/api/tasks')
data = response.json()

print("API响应状态:", response.status_code)
print("API响应数据结构:")
print(json.dumps(data, indent=2, ensure_ascii=False))

if data.get('success') and data.get('data'):
    tasks = data['data']
    print(f"\n共有 {len(tasks)} 个任务")
    for i, task in enumerate(tasks[:3], 1):  # 只显示前3个
        print(f"\n任务 {i}:")
        print(f"  ID: {task.get('id')}")
        print(f"  名称: {task.get('name')}")
        print(f"  任务空间ID: {task.get('task_space_id')}")
        print(f"  状态: {task.get('status')}")
        print(f"  优先级: {task.get('priority')}")
