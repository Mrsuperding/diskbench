#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试任务详情返回的数据"""

import requests
import json

# 获取任务列表
response = requests.get('http://localhost:5003/api/tasks')
tasks = response.json()['data']
if not tasks:
    print("没有任务")
    exit(1)

task_id = tasks[0]['id']
print(f"任务ID: {task_id}")

# 获取任务详情
detail_response = requests.get(f'http://localhost:5003/api/tasks/{task_id}')
if detail_response.status_code == 200:
    detail = detail_response.json()['data']
    print(f"\n任务详情中的io_test_cases:")
    print(json.dumps(detail.get('io_test_cases', []), indent=2, ensure_ascii=False))
else:
    print(f"获取任务详情失败: {detail_response.status_code}")
