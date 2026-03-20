const { test, expect } = require('@playwright/test');

// 测试IO任务详情页面
test.describe('IO任务详情页面测试', () => {
  // 测试页面加载
  test('IO任务详情页面能正常加载', async ({ page }) => {
    // 导航到任务详情页面（假设任务ID为1）
    await page.goto('http://localhost:8081/#/task/1');
    
    // 验证页面标题
    await expect(page).toHaveTitle(/任务详情/);
    
    // 验证页面元素
    await expect(page.locator('.page-title')).toContainText('任务详情');
    await expect(page.locator('.task-detail-card')).toBeVisible();
  });

  // 测试iostat日志解析
  test('iostat日志解析功能正常', async ({ page }) => {
    // 导航到任务详情页面
    await page.goto('http://localhost:8081/#/task/1');
    
    // 等待页面加载完成
    await page.waitForSelector('.task-logs');
    
    // 模拟iostat日志数据（通过WebSocket）
    // 这里我们可以通过JavaScript执行来模拟日志数据
    await page.evaluate(() => {
      // 模拟iostat日志行
      const iostatLogLine = 'sda               0.00     0.00    10.00    5.00     1.00     0.50     16.00     0.10    5.00    4.00    6.00   1.00   15.00';
      
      // 调用解析函数
      if (window.parseIostatLog) {
        window.parseIostatLog(iostatLogLine);
      }
    });
    
    // 验证日志是否被正确解析（通过检查控制台输出或DOM元素）
    // 由于日志解析是在前端内存中处理的，我们可以通过执行JavaScript来验证
    const iostatMetrics = await page.evaluate(() => {
      return window.iostatMetrics || [];
    });
    
    expect(iostatMetrics.length).toBeGreaterThan(0);
    expect(iostatMetrics[0]).toHaveProperty('device', 'sda');
    expect(iostatMetrics[0]).toHaveProperty('read_kbps');
    expect(iostatMetrics[0]).toHaveProperty('write_kbps');
    expect(iostatMetrics[0]).toHaveProperty('read_iops');
    expect(iostatMetrics[0]).toHaveProperty('write_iops');
  });

  // 测试测试结果显示
  test('测试结果能显示多个IO模型的结果', async ({ page }) => {
    // 导航到任务详情页面
    await page.goto('http://localhost:8081/#/task/1');
    
    // 点击"详细数据"按钮
    await page.click('text=详细数据');
    
    // 等待结果页面加载
    await page.waitForURL('**/results*');
    
    // 验证结果列表
    const resultItems = await page.locator('.el-table__row').count();
    expect(resultItems).toBeGreaterThan(0);
    
    // 验证IO模型名称显示
    const ioModelNames = await page.locator('td:has-text("IO模型") + td').allTextContents();
    expect(ioModelNames.length).toBeGreaterThan(0);
  });

  // 测试块大小和队列深度参数处理
  test('块大小和队列深度参数被正确处理', async ({ page }) => {
    // 导航到任务详情页面
    await page.goto('http://localhost:8081/#/task/1');
    
    // 点击"详细数据"按钮
    await page.click('text=详细数据');
    
    // 等待结果页面加载
    await page.waitForURL('**/results*');
    
    // 验证IO模型名称中包含块大小和队列深度信息
    const ioModelNames = await page.locator('td:has-text("IO模型") + td').allTextContents();
    
    // 检查至少有一个IO模型名称包含块大小和队列深度信息
    const hasValidModelName = ioModelNames.some(name => {
      return name.includes('blocksize') && name.includes('iodepth');
    });
    
    expect(hasValidModelName).toBe(true);
  });
});
