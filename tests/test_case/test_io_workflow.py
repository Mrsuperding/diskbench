import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
import time

class TestIOWorkflow:
    """IO工作流测试类"""
    
    def monitor_network(self, driver):
        """启用浏览器网络监控，捕获XHR请求响应"""
        driver.execute_script("""
            window._networkLogs = [];
            
            // 监听XMLHttpRequest
            (function() {
                const originalXHR = window.XMLHttpRequest;
                window.XMLHttpRequest = function() {
                    const xhr = new originalXHR();
                    xhr.addEventListener('load', function() {
                        window._networkLogs.push({
                            url: this.responseURL,
                            status: this.status,
                            statusText: this.statusText,
                            response: this.responseText,
                            method: this._method || 'GET'
                        });
                    });
                    const originalOpen = xhr.open;
                    xhr.open = function(method, url) {
                        this._method = method;
                        return originalOpen.apply(this, arguments);
                    };
                    return xhr;
                };
            })();
            
            // 监听fetch请求
            (function() {
                const originalFetch = window.fetch;
                window.fetch = function(url, options) {
                    return originalFetch.apply(this, arguments)
                        .then(response => {
                            const clonedResponse = response.clone();
                            return clonedResponse.text()
                                .then(text => {
                                    window._networkLogs.push({
                                        url: url,
                                        status: response.status,
                                        statusText: response.statusText,
                                        response: text,
                                        method: options ? options.method || 'GET' : 'GET'
                                    });
                                    return response;
                                });
                        });
                };
            })();
        """)
    
    def get_network_logs(self, driver):
        """获取网络日志"""
        return driver.execute_script("return window._networkLogs || [];")
    
    def check_for_errors(self, driver, operation_name):
        """检查页面上是否有错误提示"""
        print(f"\n🔍 检查 {operation_name} 操作是否有错误")
        time.sleep(1)
        
        has_error = False
        
        # 检查网络请求错误
        network_logs = self.get_network_logs(driver)
        for log in network_logs:
            if log['status'] >= 400:
                has_error = True
                print(f"❌ 网络请求错误: {log['method']} {log['url']}")
                print(f"   状态码: {log['status']} {log['statusText']}")
        
        # 查找UI错误提示元素
        error_elements = driver.find_elements(By.CSS_SELECTOR, ".el-message--error")
        if error_elements:
            for error in error_elements:
                print(f"❌ UI错误提示: {error.text}")
            has_error = True
        
        # 检查表单验证错误
        form_errors = driver.find_elements(By.CSS_SELECTOR, ".el-form-item__error")
        if form_errors:
            for error in form_errors:
                print(f"❌ 表单验证错误: {error.text}")
            has_error = True
        
        if not has_error:
            print(f"✅ {operation_name} 操作未发现明显错误")
        
        return has_error
    
    def find_button_by_text(self, driver, buttons, keyword):
        """根据按钮文本查找按钮"""
        for button in buttons:
            if button.text and keyword in button.text:
                return button
        return None
    
    def find_form_item_by_text(self, container, text):
        """根据文本查找表单项"""
        form_items = container.find_elements(By.CSS_SELECTOR, ".el-form-item")
        for item in form_items:
            if text in item.text:
                return item
        return None
    
    def click_element_safely(self, driver, element):
        """安全点击元素，处理各种可能的异常"""
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
            time.sleep(0.5)
            element.click()
            return True
        except ElementClickInterceptedException:
            try:
                driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                return False
        except Exception:
            return False
    
    def set_input_value(self, input_element, value):
        """设置输入框值，确保输入成功"""
        input_element.click()
        time.sleep(0.5)
        input_element.clear()
        input_element.send_keys(value)
        time.sleep(0.5)
        
        entered_value = input_element.get_attribute('value')
        if entered_value != value:
            input_element.clear()
            input_element.send_keys(value)
            time.sleep(0.5)
        
        return input_element.get_attribute('value') == value
    
    def select_from_dropdown(self, driver, form_item, option_index=0):
        """从下拉选择器中选择选项"""
        try:
            selector = form_item.find_element(By.CSS_SELECTOR, ".el-select")
            
            if not self.click_element_safely(driver, selector):
                return False
            
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-select-dropdown__item")))
            
            options = driver.find_elements(By.CSS_SELECTOR, ".el-select-dropdown__item")
            if options and len(options) > option_index:
                return self.click_element_safely(driver, options[option_index])
            
            return False
        except Exception:
            return False
    
    def verify_item_in_table(self, driver, table_locator, item_name, item_type="节点"):
        """验证项目是否在表格中"""
        print(f"\n=== 验证{item_type}创建 ===")
        item_found = False
        
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(table_locator))
        time.sleep(2)
        
        try:
            table = driver.find_element(*table_locator)
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"   在表格中找到 {len(rows)} 行数据")
            
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    continue
                
                cell_texts = [cell.text.strip() for cell in cells]
                row_text = " | ".join(cell_texts)
                
                if item_name in cell_texts[0] or item_name in row_text:
                    item_found = True
                    print(f"✅ {item_type} {item_name} 已成功创建并显示在列表中")
                    print(f"   {item_type}行内容: {row_text}")
                    break
        except Exception as e:
            print(f"   查找表格数据时出错: {e}")
        
        if not item_found:
            print(f"   首次检查未找到{item_type}，尝试刷新页面...")
            driver.refresh()
            WebDriverWait(driver, 20).until(EC.presence_of_element_located(table_locator))
            time.sleep(3)
            
            try:
                table = driver.find_element(*table_locator)
                rows = table.find_elements(By.TAG_NAME, "tr")
                
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if not cells:
                        continue
                    
                    cell_texts = [cell.text.strip() for cell in cells]
                    row_text = " | ".join(cell_texts)
                    
                    if item_name in cell_texts[0] or item_name in row_text:
                        item_found = True
                        print(f"✅ 刷新后找到{item_type} {item_name}")
                        break
            except Exception as e:
                print(f"   刷新后查找数据时出错: {e}")
        
        if item_found:
            print(f"✅ {item_type}创建验证成功: {item_name}")
        else:
            print(f"❌ {item_type}创建验证失败: {item_name} 未出现在列表中")
        
        print("====================")
        return item_found
    
    def test_complete_io_workflow(self, driver, base_url, test_data, test_results):
        """测试完整的IO测试工作流"""
        print("开始完整的IO工作流测试")
        print(f"测试数据: {test_data}")
        
        # 启用网络监控
        self.monitor_network(driver)
        
        # 1. 注册新用户
        print("1. 注册新用户")
        driver.get(f"{base_url}/register")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "form")))
        
        username_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='用户名']")
        self.set_input_value(username_input, test_data["username"])
        
        email_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='邮箱']")
        self.set_input_value(email_input, test_data["email"])
        
        password_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='密码']")
        self.set_input_value(password_input, test_data["password"])
        
        confirm_password_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='再次输入密码']")
        self.set_input_value(confirm_password_input, test_data["password"])
        
        # 提交注册
        register_form = driver.find_element(By.TAG_NAME, "form")
        register_buttons = register_form.find_elements(By.TAG_NAME, "button")
        if register_buttons:
            self.click_element_safely(driver, register_buttons[0])
        
        # 检查注册错误
        self.check_for_errors(driver, "注册")
        
        # 等待登录页面加载
        WebDriverWait(driver, 20).until(EC.url_contains("/login"))
        print(f"注册成功，用户名: {test_data['username']}")
        
        # 2. 登录
        print("2. 登录")
        login_username = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='用户名']")
        self.set_input_value(login_username, test_data["username"])
        
        login_password = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='密码']")
        self.set_input_value(login_password, test_data["password"])
        
        login_form = driver.find_element(By.TAG_NAME, "form")
        login_buttons = login_form.find_elements(By.TAG_NAME, "button")
        if login_buttons:
            self.click_element_safely(driver, login_buttons[0])
        
        # 检查登录错误
        self.check_for_errors(driver, "登录")
        
        # 等待仪表盘页面加载
        WebDriverWait(driver, 20).until(EC.url_contains("/dashboard"))
        print("登录成功")
        
        # 3. 创建登录凭证
        print("3. 创建登录凭证")
        driver.get(f"{base_url}/login-credentials")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        
        # 点击新建按钮
        buttons = driver.find_elements(By.CSS_SELECTOR, ".el-button")
        new_button = self.find_button_by_text(driver, buttons, "新建")
        if new_button:
            self.click_element_safely(driver, new_button)
        
        # 等待对话框加载
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-dialog")))
        dialog = driver.find_element(By.CSS_SELECTOR, ".el-dialog")
        
        # 凭证别名
        alias_input = dialog.find_element(By.CSS_SELECTOR, "input[placeholder='请输入凭证别名']")
        self.set_input_value(alias_input, test_data["credential_alias"])
        
        # 主机地址
        host_input = dialog.find_element(By.CSS_SELECTOR, "input[placeholder*='主机地址']")
        self.set_input_value(host_input, test_data["credential_host"])
        
        # 端口
        port_input = dialog.find_element(By.CSS_SELECTOR, ".el-input-number input")
        self.set_input_value(port_input, test_data["credential_port"])
        
        # 用户名
        username_input = dialog.find_element(By.CSS_SELECTOR, "input[placeholder='请输入用户名']")
        self.set_input_value(username_input, test_data["credential_username"])
        
        # 密码
        password_inputs = dialog.find_elements(By.CSS_SELECTOR, "input[type='password']")
        if password_inputs:
            self.set_input_value(password_inputs[0], test_data["credential_password"])
        
        # 平台分区路径
        try:
            platform_input = dialog.find_element(By.CSS_SELECTOR, "input[placeholder*='平台分区路径']")
            self.set_input_value(platform_input, "/tmp")
        except Exception:
            pass
        
        # 提交凭证创建
        dialog_buttons = dialog.find_elements(By.CSS_SELECTOR, ".el-dialog__footer .el-button")
        confirm_button = self.find_button_by_text(driver, dialog_buttons, "确定")
        if confirm_button:
            self.click_element_safely(driver, confirm_button)
        
        # 检查创建登录凭证错误
        self.check_for_errors(driver, "创建登录凭证")
        time.sleep(2)
        print(f"登录凭证创建完成: {test_data['credential_alias']}")
        
        # 4. 创建节点
        print("4. 创建节点")
        driver.get(f"{base_url}/nodes")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        
        # 点击新建按钮
        buttons = driver.find_elements(By.CSS_SELECTOR, ".el-button")
        new_button = self.find_button_by_text(driver, buttons, "新建")
        if new_button:
            self.click_element_safely(driver, new_button)
        
        # 等待对话框加载
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-dialog")))
        dialog = driver.find_element(By.CSS_SELECTOR, ".el-dialog")
        
        # 节点名称
        name_input = dialog.find_element(By.CSS_SELECTOR, "input[placeholder='请输入节点名称']")
        self.set_input_value(name_input, test_data["node_name"])
        
        # 主机地址
        ip_input = dialog.find_element(By.CSS_SELECTOR, "input[placeholder*='主机地址']")
        self.set_input_value(ip_input, test_data["node_ip"])
        
        # 选择登录凭证
        credential_form_item = self.find_form_item_by_text(dialog, "登录凭证")
        if credential_form_item:
            self.select_from_dropdown(driver, credential_form_item, 0)
        
        # 选择节点类型
        type_form_item = self.find_form_item_by_text(dialog, "节点类型")
        if type_form_item:
            self.select_from_dropdown(driver, type_form_item, 0)
        
        # 提交节点创建
        dialog_buttons = dialog.find_elements(By.CSS_SELECTOR, ".el-dialog__footer .el-button")
        confirm_button = self.find_button_by_text(driver, dialog_buttons, "确定")
        if confirm_button:
            self.click_element_safely(driver, confirm_button)
        
        # 检查创建节点错误
        self.check_for_errors(driver, "创建节点")
        time.sleep(2)
        print(f"节点创建完成: {test_data['node_name']}")
        
        # 验证节点创建
        self.verify_item_in_table(driver, (By.TAG_NAME, "table"), test_data["node_name"], "节点")
        
        # 5. 创建IO测试用例
        print("5. 创建IO测试用例")
        driver.get(f"{base_url}/io-cases")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        
        # 点击新建按钮
        buttons = driver.find_elements(By.CSS_SELECTOR, ".el-button")
        new_button = self.find_button_by_text(driver, buttons, "新建")
        if new_button:
            self.click_element_safely(driver, new_button)
        
        # 等待对话框加载
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-dialog")))
        dialog = driver.find_element(By.CSS_SELECTOR, ".el-dialog")
        
        # 用例名称
        name_item = self.find_form_item_by_text(dialog, "用例名称")
        name_input = name_item.find_element(By.TAG_NAME, "input")
        self.set_input_value(name_input, test_data["io_case_name"])
        
        # 块大小
        block_size_item = self.find_form_item_by_text(dialog, "块大小(KB)")
        block_size_input = block_size_item.find_element(By.TAG_NAME, "input")
        self.set_input_value(block_size_input, "4")
        
        # 队列深度
        queue_depth_item = self.find_form_item_by_text(dialog, "队列深度")
        queue_depth_input = queue_depth_item.find_element(By.TAG_NAME, "input")
        self.set_input_value(queue_depth_input, "16")
        
        # IO类型
        io_type_item = self.find_form_item_by_text(dialog, "IO类型")
        io_type_input = io_type_item.find_element(By.TAG_NAME, "input")
        self.set_input_value(io_type_input, "randread")
        
        # 运行时间
        runtime_item = self.find_form_item_by_text(dialog, "运行时间")
        runtime_input = runtime_item.find_element(By.CSS_SELECTOR, ".el-input__inner")
        self.set_input_value(runtime_input, "60")
        
        # 提交IO测试用例创建
        dialog_buttons = dialog.find_elements(By.CSS_SELECTOR, ".el-dialog__footer .el-button")
        confirm_button = self.find_button_by_text(driver, dialog_buttons, "确定")
        if confirm_button:
            self.click_element_safely(driver, confirm_button)
        
        # 检查创建IO测试用例错误
        self.check_for_errors(driver, "创建IO测试用例")
        time.sleep(2)
        print(f"IO测试用例创建完成: {test_data['io_case_name']}")
        
        # 验证IO测试用例创建
        self.verify_item_in_table(driver, (By.TAG_NAME, "table"), test_data["io_case_name"], "IO测试用例")
        
        # 6. 创建IO测试任务
        print("6. 创建IO测试任务")
        driver.get(f"{base_url}/tasks/io-task-management")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        
        # 点击新建按钮
        buttons = driver.find_elements(By.CSS_SELECTOR, ".el-button")
        new_button = self.find_button_by_text(driver, buttons, "新建")
        if new_button:
            self.click_element_safely(driver, new_button)
        
        # 等待对话框加载
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-dialog")))
        dialog = driver.find_element(By.CSS_SELECTOR, ".el-dialog")
        
        # 任务名称
        name_item = self.find_form_item_by_text(dialog, "任务名称")
        name_input = name_item.find_element(By.TAG_NAME, "input")
        self.set_input_value(name_input, test_data["task_name"])
        
        # 描述
        desc_item = self.find_form_item_by_text(dialog, "描述")
        desc_input = desc_item.find_element(By.TAG_NAME, "textarea")
        self.set_input_value(desc_input, "测试任务描述")
        
        # 选择测试用例
        test_case_item = self.find_form_item_by_text(dialog, "测试用例")
        if test_case_item:
            self.select_from_dropdown(driver, test_case_item, 0)
        
        # 提交任务创建
        dialog_buttons = dialog.find_elements(By.CSS_SELECTOR, ".el-dialog__footer .el-button")
        confirm_button = self.find_button_by_text(driver, dialog_buttons, "确定")
        if confirm_button:
            self.click_element_safely(driver, confirm_button)
        
        # 检查创建IO测试任务错误
        self.check_for_errors(driver, "创建IO测试任务")
        time.sleep(2)
        print(f"IO测试任务创建完成: {test_data['task_name']}")
        
        # 验证IO测试任务创建
        self.verify_item_in_table(driver, (By.TAG_NAME, "table"), test_data["task_name"], "IO测试任务")
        
        print("\n🎉 IO工作流测试完成！")
