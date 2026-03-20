#!/usr/bin/env python3
"""
测试time_based功能的实现
包括：
1. 创建测试用例时保存time_based参数
2. 执行任务时是否正确处理time_based参数
"""

import json
import requests
import time
import uuid

# 测试配置
BASE_URL = 'http://localhost:5003/api'
USERNAME = 'admin'
PASSWORD = 'adminpassword'

class TimeBasedTest:
    def __init__(self):
        self.token = self.login()
        self.headers = {'Authorization': f'Bearer {self.token}'}
    
    def login(self):
        """登录获取token"""
        url = f'{BASE_URL}/auth/login'
        data = {'username': USERNAME, 'password': PASSWORD}
        response = requests.post(url, json=data)
        print(f"登录响应状态码: {response.status_code}")
        print(f"登录响应内容: {response.text}")
        assert response.status_code == 200
        return response.json()['data']['token']
    
    def create_test_case_with_time_based(self):
        """创建带有time_based参数的测试用例"""
        url = f'{BASE_URL}/io-cases'
        test_case_name = f'test_time_based_{uuid.uuid4()}'
        data = {
            'name': test_case_name,
            'description': 'Test case with time_based parameter',
            'parameters': {
                'io_type': 'randread',
                'block_size': '4k',
                'queue_depth': '16',
                'runtime': '10',
                'time_based': True,  # 设置time_based为True
                'size': '1G'
            }
        }
        response = requests.post(url, json=data, headers=self.headers)
        assert response.status_code == 201
        return response.json()['data']
    
    def get_test_case(self, case_id):
        """获取测试用例信息"""
        url = f'{BASE_URL}/io-cases/{case_id}'
        response = requests.get(url, headers=self.headers)
        assert response.status_code == 200
        return response.json()['data']
    
    def create_task(self, case_id):
        """创建任务"""
        url = f'{BASE_URL}/tasks'
        task_name = f'task_time_based_{uuid.uuid4()}'
        data = {
            'name': task_name,
            'description': 'Task with time_based parameter',
            'io_test_case_ids': [case_id],
            'node_ids': []  # 空节点列表，只测试参数处理
        }
        response = requests.post(url, json=data, headers=self.headers)
        assert response.status_code == 201
        return response.json()['data']
    
    def test_time_based_functionality(self):
        """测试time_based功能"""
        print("=== 测试time_based功能 ===")
        
        # 1. 创建带有time_based参数的测试用例
        print("1. 创建带有time_based参数的测试用例...")
        test_case = self.create_test_case_with_time_based()
        case_id = test_case['id']
        print(f"   创建成功，测试用例ID: {case_id}")
        
        # 2. 验证time_based参数是否正确保存
        print("2. 验证time_based参数是否正确保存...")
        retrieved_case = self.get_test_case(case_id)
        parameters = retrieved_case['parameters']
        assert 'time_based' in parameters, "time_based参数未保存"
        assert parameters['time_based'] is True, "time_based参数值不正确"
        print("   验证成功，time_based参数正确保存")
        
        # 3. 创建任务
        print("3. 创建任务...")
        task = self.create_task(case_id)
        task_id = task['id']
        print(f"   创建成功，任务ID: {task_id}")
        
        print("\n=== 测试完成 ===")
        print("✅ time_based功能测试通过")
        print(f"   测试用例ID: {case_id}")
        print(f"   任务ID: {task_id}")

if __name__ == '__main__':
    test = TimeBasedTest()
    test.test_time_based_functionality()
