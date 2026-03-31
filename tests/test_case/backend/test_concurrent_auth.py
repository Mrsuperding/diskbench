import pytest
import requests
import json
import threading
import time
from queue import Queue

class TestConcurrentAuth:
    """并发认证测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        self.base_url = "http://localhost:5003/api"
        self.test_results = Queue()
    
    def register_user(self, user_id):
        """注册用户"""
        test_data = {
            "username": f"testuser_{user_id}",
            "email": f"test_{user_id}@example.com",
            "password": "test123456"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=test_data
            )
            self.test_results.put({
                "user_id": user_id,
                "action": "register",
                "status_code": response.status_code,
                "response": response.json()
            })
            return response.status_code
        except Exception as e:
            self.test_results.put({
                "user_id": user_id,
                "action": "register",
                "error": str(e)
            })
            return None
    
    def login_user(self, user_id):
        """登录用户"""
        login_data = {
            "username": f"testuser_{user_id}",
            "password": "test123456"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=login_data
            )
            self.test_results.put({
                "user_id": user_id,
                "action": "login",
                "status_code": response.status_code,
                "response": response.json()
            })
            return response.status_code
        except Exception as e:
            self.test_results.put({
                "user_id": user_id,
                "action": "login",
                "error": str(e)
            })
            return None
    
    def test_concurrent_users(self, user_count=10):
        """测试并发用户注册和登录"""
        print(f"开始测试：{user_count}个用户并发注册和登录")
        
        # 重置测试结果
        self.test_results = Queue()
        
        # 创建注册线程
        register_threads = []
        for i in range(user_count):
            thread = threading.Thread(target=self.register_user, args=(i,))
            register_threads.append(thread)
            thread.start()
        
        # 等待所有注册线程完成
        for thread in register_threads:
            thread.join()
        
        # 等待1秒，确保注册完成
        time.sleep(1)
        
        # 创建登录线程
        login_threads = []
        for i in range(user_count):
            thread = threading.Thread(target=self.login_user, args=(i,))
            login_threads.append(thread)
            thread.start()
        
        # 等待所有登录线程完成
        for thread in login_threads:
            thread.join()
        
        # 统计测试结果
        register_success = 0
        login_success = 0
        errors = 0
        
        # 从队列中获取所有结果
        results = []
        while not self.test_results.empty():
            results.append(self.test_results.get())
        
        for result in results:
            if result.get("action") == "register" and result.get("status_code") in [200, 400]:
                register_success += 1
            elif result.get("action") == "login" and result.get("status_code") == 200:
                login_success += 1
            elif result.get("error"):
                errors += 1
        
        print(f"测试完成：")
        print(f"注册成功：{register_success}/{user_count}")
        print(f"登录成功：{login_success}/{user_count}")
        print(f"错误数量：{errors}")
        
        # 验证测试结果
        assert register_success == user_count, f"注册成功数不匹配，预期：{user_count}，实际：{register_success}"
        assert login_success == user_count, f"登录成功数不匹配，预期：{user_count}，实际：{login_success}"
        assert errors == 0, f"出现错误，错误数：{errors}"
        
        print(f"{user_count}个用户并发注册和登录测试通过")
    
    def test_concurrent_users_0(self):
        """测试0个用户（边界测试）"""
        print("开始测试：0个用户并发注册和登录")
        self.test_concurrent_users(0)
    
    def test_concurrent_users_1(self):
        """测试1个用户"""
        print("开始测试：1个用户并发注册和登录")
        self.test_concurrent_users(1)
    
    def test_concurrent_users_10(self):
        """测试10个用户"""
        print("开始测试：10个用户并发注册和登录")
        self.test_concurrent_users(10)
    
    def test_concurrent_users_50(self):
        """测试50个用户"""
        print("开始测试：50个用户并发注册和登录")
        self.test_concurrent_users(50)
    
    def test_concurrent_users_100(self):
        """测试100个用户"""
        print("开始测试：100个用户并发注册和登录")
        self.test_concurrent_users(100)