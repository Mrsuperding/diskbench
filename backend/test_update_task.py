#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试更新任务的task_space_id"""

import requests
import json

# 先获取一个任务
response = requests.get('http://localhost:5003/api/tasks')
tasks = response.json()['data']
if not tasks:
    print("没有任务")
    exit(1)

task_id = tasks[0]['id']
print(f"选择任务ID: {task_id}")
print(f"当前task_space_id: {tasks[0]['task_space_id']}")

# 获取任务空间列表
spaces_response = requests.get('http://localhost:5003/api/task-spaces')
print(f"\n任务空间API状态: {spaces_response.status_code}")
if spaces_response.status_code == 200:
    spaces_data = spaces_response.json()
    print(f"任务空间响应: {json.dumps(spaces_data, indent=2, ensure_ascii=False)}")

# 尝试更新任务
update_data = {
    'name': tasks[0]['name'],
    'description': tasks[0]['description'],
    'task_space_id': 1,  # 假设有ID为1的任务空间
    'status': tasks[0]['status'],
    'priority': tasks[0]['priority']
}

print(f"\n发送更新请求:")
print(json.dumps(update_data, indent=2, ensure_ascii=False))

update_response = requests.put(
    f'http://localhost:5003/api/tasks/{task_id}',
    json=update_data
)

print(f"\n更新响应状态: {update_response.status_code}")
print(f"更新响应: {json.dumps(update_response.json(), indent=2, ensure_ascii=False)}")

# 再次获取任务验证
verify_response = requests.get('http://localhost:5003/api/tasks')
verify_tasks = verify_response.json()['data']
updated_task = next((t for t in verify_tasks if t['id'] == task_id), None)
if updated_task:
    print(f"\n验证更新后的task_space_id: {updated_task['task_space_id']}")
else:
    print("找不到更新后的任务")
