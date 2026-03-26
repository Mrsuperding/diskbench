import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import random
import string
import os
import json

# 生成随机字符串用于测试数据
def generate_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

@pytest.fixture(scope="session")
def driver():
    """初始化WebDriver并在测试结束后清理"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    driver.implicitly_wait(10)
    
    yield driver
    
    print("测试结束，关闭浏览器")
    driver.quit()

@pytest.fixture(scope="module")
def test_data():
    """生成测试数据"""
    random_str = generate_random_string()
    return {
        "username": f"testuser_{random_str}",
        "email": f"test_{random_str}@example.com",
        "password": "test123456",
        "credential_alias": f"credential_{random_str}",
        "credential_host": "127.0.0.1",
        "credential_port": "22",
        "credential_username": "testuser",
        "credential_password": "testpass",
        "node_name": f"node_{random_str}",
        "node_ip": "127.0.0.1",
        "io_case_name": f"io_case_{random_str}",
        "task_name": f"io_task_{random_str}"
    }

@pytest.fixture(scope="session")
def base_url():
    """测试基础URL"""
    return "http://localhost:8081"

@pytest.fixture(scope="session")
def backend_url():
    """后端API基础URL"""
    return "http://localhost:5003/api"

@pytest.fixture(scope="function")
def api_client():
    """API客户端fixture，可用于发送HTTP请求"""
    import requests
    session = requests.Session()
    yield session
    session.close()

@pytest.fixture(scope="session")
def test_data_file():
    """测试数据文件路径"""
    return os.path.join(os.path.dirname(__file__), "testdata", "test_data.json")

@pytest.fixture(scope="session")
def load_test_data(test_data_file):
    """加载测试数据文件"""
    if os.path.exists(test_data_file):
        with open(test_data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """钩子函数，用于生成测试报告"""
    outcome = yield
    rep = outcome.get_result()
    
    # 设置测试结果属性，可在teardown中访问
    setattr(item, "rep_" + rep.when, rep)

@pytest.fixture(scope="function")
def test_results(request):
    """测试结果收集fixture"""
    results = {}
    
    def fin():
        """测试结束时收集结果"""
        for when in ["setup", "call", "teardown"]:
            rep = getattr(request.node, "rep_" + when, None)
            if rep:
                results[when] = {
                    "outcome": rep.outcome,
                    "duration": rep.duration,
                    "longrepr": str(rep.longrepr) if rep.longrepr else None
                }
        
        # 保存测试结果到文件
        results_file = os.path.join(os.path.dirname(__file__), "reports", "test_results.json")
        
        # 读取现有结果
        existing_results = {}
        if os.path.exists(results_file):
            with open(results_file, 'r', encoding='utf-8') as f:
                existing_results = json.load(f)
        
        # 添加当前测试结果
        test_name = request.node.nodeid
        existing_results[test_name] = results
        
        # 保存更新后的结果
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(existing_results, f, ensure_ascii=False, indent=2)
    
    request.addfinalizer(fin)
    return results
