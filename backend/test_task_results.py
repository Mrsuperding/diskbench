import requests
import json

# 配置
BASE_URL = 'http://localhost:5000/api'
LOGIN_ENDPOINT = '/auth/login'
TASK_RESULTS_ENDPOINT = '/tasks/3/results'
USERNAME = 'admin'  # 假设存在admin用户
PASSWORD = 'adminpassword'  # 假设密码是adminpassword

def main():
    try:
        # 1. 登录获取JWT令牌
        print(f'正在登录: {BASE_URL}{LOGIN_ENDPOINT}')
        login_response = requests.post(
            f'{BASE_URL}{LOGIN_ENDPOINT}',
            json={'username': USERNAME, 'password': PASSWORD}
        )
        print(f'登录状态码: {login_response.status_code}')
        print(f'登录响应: {login_response.text}')
        
        if login_response.status_code != 200:
            print('登录失败')
            return
        
        login_data = login_response.json()
        token = login_data.get('data', {}).get('token')
        
        if not token:
            print('未获取到JWT令牌')
            return
        
        # 2. 使用JWT令牌调用任务结果接口
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        print(f'\n正在调用任务结果接口: {BASE_URL}{TASK_RESULTS_ENDPOINT}')
        results_response = requests.get(
            f'{BASE_URL}{TASK_RESULTS_ENDPOINT}',
            headers=headers
        )
        
        print(f'接口状态码: {results_response.status_code}')
        print(f'接口响应: {results_response.text}')
        
        if results_response.status_code == 200:
            print('\n接口调用成功！')
        else:
            print('\n接口调用失败！')
            
    except Exception as e:
        print(f'发生错误: {str(e)}')

if __name__ == '__main__':
    main()