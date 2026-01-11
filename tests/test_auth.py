import pytest
from selenium import webdriver
#指定元素定位方式，css选择器、XPath等
from selenium.webdriver.common.by import By
#显示等待类
from selenium.webdriver.support.ui import WebDriverWait
#预期条件，用于判断页面元素是否满足特定条件
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
#chrome浏览器配置选项类
from selenium.webdriver.chrome.options import Options
import time
import random
import string

# 生成随机字符串用于测试数据
def generate_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

# 表示这个fixture在整个测试模块中只执行一次，类似定义一个用例执行前需要环境准备以及执行完后环境资源的释放
@pytest.fixture(scope="module")
def driver():
    """初始化WebDriver并在测试结束后清理"""
    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式运行，不显示浏览器窗口
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    # 初始化Chrome WebDriver
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    driver.implicitly_wait(10)  # 设置隐式等待时间
    
    yield driver
    
    print("测试结束，关闭浏览器")
    # 测试结束后关闭浏览器
    driver.quit()
    print("浏览器已关闭")

@pytest.fixture(scope="module")
def test_data():
    """生成测试数据"""
    random_str = generate_random_string()
    return {
        "username": f"testuser_{random_str}",
        "email": f"test_{random_str}@example.com",
        "password": "test123456"
    }

def test_register(driver, test_data):
    """测试注册功能"""
    # 打开注册页面
    driver.get("http://localhost:8081/register")
    
    # 等待页面加载完成
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".register-title"))
    )
    
    # 输入用户名
    username_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入用户名']")
    username_input.send_keys(test_data["username"])
    
    # 输入邮箱
    email_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入邮箱']")
    email_input.send_keys(test_data["email"])
    
    # 输入密码
    password_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入密码']")
    password_input.send_keys(test_data["password"])
    
    # 输入确认密码
    confirm_password_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='请再次输入密码']")
    confirm_password_input.send_keys(test_data["password"])
    
    # 点击注册按钮
    # 使用更通用的方式定位按钮，通过其父元素
    form = driver.find_element(By.CSS_SELECTOR, ".register-form")
    register_button = form.find_element(By.TAG_NAME, "button")
    register_button.click()
    
    # 等待注册成功跳转至登录页面
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".login-title"))
    )
    
    # 验证当前页面是登录页面
    # 检查URL是否包含login
    assert "login" in driver.current_url.lower(), f"注册后未跳转至登录页面，当前URL: {driver.current_url}"
    
    # 或者检查页面是否包含登录相关元素
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".login-form"))
    )
    
    print(f"注册测试通过，用户名: {test_data['username']}")

def test_login(driver, test_data):
    """测试登录功能"""
    # 打开登录页面
    driver.get("http://localhost:8081/login")
    
    # 等待页面加载完成
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".login-title"))
    )
    
    # 输入用户名
    username_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入用户名']")
    username_input.send_keys(test_data["username"])
    
    # 输入密码
    password_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入密码']")
    password_input.send_keys(test_data["password"])
    
    # 点击登录按钮
    # 使用更通用的方式定位按钮，通过其父元素
    form = driver.find_element(By.CSS_SELECTOR, ".login-form")
    login_button = form.find_element(By.TAG_NAME, "button")
    login_button.click()
    
    # 等待登录成功跳转至仪表盘页面
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".el-menu-item"))
    )
    
    # 验证当前页面是仪表盘页面
    assert driver.current_url == "http://localhost:8081/dashboard", f"登录后未跳转至仪表盘页面，当前URL: {driver.current_url}"
    
    print(f"登录测试通过，用户名: {test_data['username']}")
