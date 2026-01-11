import requests
import json

# 配置
base_url = 'http://localhost:5002/api'
username = 'admin'
password = 'adminpassword'

# 1. 登录获取token
def login():
    url = f'{base_url}/auth/login'
    data = {'username': username, 'password': password}
    response = requests.post(url, json=data)
    print(f'登录状态码: {response.status_code}')
    print(f'登录响应: {response.text}')
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            return result.get('data', {}).get('token')
    return None

# 2. 测试获取任务日志
def test_get_task_logs(token, task_id, node_id=None):
    url = f'{base_url}/logs/task/{task_id}'
    headers = {'Authorization': f'Bearer {token}'}
    params = {'node_id': node_id} if node_id else {}
    
    print(f'\n测试获取任务日志: {url}')
    print(f'参数: {params}')
    
    response = requests.get(url, headers=headers, params=params)
    print(f'状态码: {response.status_code}')
    print(f'响应: {response.text}')
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            logs = result.get('data', [])
            print(f'成功获取到 {len(logs)} 条日志')
            return logs
    return None

# 3. 测试获取IOSTAT指标
def test_get_iostat_metrics(token, log_id):
    url = f'{base_url}/logs/{log_id}/iostat-metrics'
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f'\n测试获取IOSTAT指标: {url}')
    
    response = requests.get(url, headers=headers)
    print(f'状态码: {response.status_code}')
    print(f'响应: {response.text}')
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            metrics = result.get('data', [])
            print(f'成功获取到 {len(metrics)} 条IOSTAT指标')
            # 提取设备名称
            devices = list(set([metric.get('device') for metric in metrics]))
            print(f'设备列表: {devices}')
            return metrics
    return None

# 主测试流程
def main():
    print('=== API修复测试 ===')
    
    # 登录获取token
    token = login()
    if not token:
        print('登录失败，无法进行后续测试')
        return
    print(f'登录成功，获取到token: {token[:20]}...')
    
    # 测试1: 不指定node_id获取所有日志
    print('\n=== 测试1: 不指定node_id获取所有日志 ===')
    logs = test_get_task_logs(token, task_id=28)
    print(f'测试1结果: 获取到 {len(logs)} 条日志')
    
    # 测试2: 指定node_id获取日志（使用字符串类型的node_id）
    print('\n=== 测试2: 指定node_id获取日志（字符串类型） ===')
    logs_with_node = test_get_task_logs(token, task_id=28, node_id='4')
    print(f'测试2结果: 获取到 {len(logs_with_node)} 条日志')
    
    # 测试3: 直接测试获取IOSTAT指标（使用实际的log_id）
    print('\n=== 测试3: 直接测试获取IOSTAT指标 ===')
    test_get_iostat_metrics(token, log_id=32)  # 使用测试中返回的iostat日志ID
    
    print('\n=== 测试完成 ===')

if __name__ == '__main__':
    main()
