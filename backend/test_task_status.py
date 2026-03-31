#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试任务状态和进度"""

import requests
import json
import time

# 获取任务列表
response = requests.get('http://localhost:5003/api/tasks')
tasks = response.json()['data']

print(f"当前任务状态和进度:")
for task in tasks[:5]:
    print(f"  任务 {task['id']}: {task['name']}")
    print(f"    状态: {task['status']}")
    print(f"    进度: {task['progress']}%")
    print(f"    节点数: {len(task.get('nodes', []))}")
    print(f"    IO用例数: {len(task.get('io_test_cases', []))}")
    print()
