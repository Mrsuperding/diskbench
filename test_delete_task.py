#!/usr/bin/env python3
# 测试删除任务脚本

import requests
import json

# 测试删除任务的函数
def test_delete_task(task_id):
    """测试删除任务"""
    # API URL
    url = f"http://localhost:5004/api/tasks/{task_id}"
    
    # 请求头，包含JWT token
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3MzU5NzI1NSwianRpIjoiZjI4NDA1MWQtMDRiZC00Yjg4LWJjNGUtMzRiYTc2OTkxZDA1IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MywibmJmIjoxNzczNTk3MjU1LCJleHAiOjE3NzM2ODM2NTV9.qYtQ6v6fCibA87tIrk_qgiIYFEmMHLiidwfV-xfqtOY'
    }
    
    try:
        # 发送DELETE请求
        response = requests.delete(url, headers=headers)
        
        # 打印响应结果
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        return response.status_code, response.json()
    except Exception as e:
        print(f"请求出错: {str(e)}")
        return None, str(e)

if __name__ == "__main__":
    # 测试删除任务id=62
    task_id = 62
    print(f"测试删除任务id={task_id}...")
    status_code, response = test_delete_task(task_id)
    
    if status_code == 200:
        print("删除任务成功！")
    else:
        print("删除任务失败，需要根据错误信息修改代码。")
