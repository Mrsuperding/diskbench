import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import random
import string
import os
import json
from loguru import logger
import datetime
# 配置基础日志
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
print(f"日志目录: {log_dir}")
print(f"日志目录存在: {os.path.exists(log_dir)}")

@pytest.fixture(autouse=True,scope="class")
def setup_logger(request):
    """为每个测试类设置独立的日志文件"""
    # 打印调试信息
    print(f"\n=== 日志配置调试 ===")
    print(f"request.node: {request.node}")
    print(f"request.node.fspath: {request.node.fspath}")
    print(f"request.node.fspath.basename: {request.node.fspath.basename}")
    
    # 获取测试文件的名称
    test_file = request.node.fspath.basename.replace(".py", "")
    
    # 为整个测试类生成一个时间戳
    if not hasattr(request.cls, "_log_timestamp"):
        request.cls._log_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp = request.cls._log_timestamp
    
    log_file = os.path.join(log_dir, f"{test_file}_{timestamp}.log")
    
    print(f"测试文件名称: {test_file}")
    print(f"时间戳: {timestamp}")
    print(f"日志文件路径: {log_file}")
    print(f"日志目录存在: {os.path.exists(log_dir)}")
    
    # 添加文件处理器，配置轮换和压缩
    handler_id = logger.add(
        log_file,
        rotation="100 MB",  # 减小轮换阈值，便于测试
        compression="zip",  # 压缩旧日志
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    print(f"处理器ID: {handler_id}")
    print(f"=== 日志配置调试结束 ===\n")
    
    yield
    
    # 测试完成后移除处理器
    logger.remove(handler_id)

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