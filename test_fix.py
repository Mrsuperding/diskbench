#!/usr/bin/env python3
"""
测试任务执行修复
验证failure_reasons变量初始化的修复是否有效
"""

import sys
import os
import logging

# 添加backend目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_failure_reasons_initialization():
    """测试failure_reasons变量初始化"""
    logger.info("开始测试failure_reasons变量初始化")
    
    try:
        # 直接导入run_task_execution函数
        from app.views.tasks import run_task_execution
        logger.info("✅ 成功导入run_task_execution函数")
        
        # 检查函数代码中是否包含failure_reasons的初始化
        import inspect
        source = inspect.getsource(run_task_execution)
        
        if 'failure_reasons = []' in source:
            logger.info("✅ 测试通过: failure_reasons变量已正确初始化")
            return True
        else:
            logger.error("❌ 测试失败: failure_reasons变量未初始化")
            logger.error("函数源码片段:")
            # 打印函数源码的相关部分
            lines = source.split('\n')
            for i, line in enumerate(lines):
                if 'task_failed' in line:
                    # 打印附近的代码
                    start = max(0, i-5)
                    end = min(len(lines), i+10)
                    for j in range(start, end):
                        logger.error(f"{j+1}: {lines[j]}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== 测试failure_reasons变量初始化修复 ===")
    success = test_failure_reasons_initialization()
    if success:
        logger.info("🎉 测试成功！failure_reasons变量初始化修复有效")
        sys.exit(0)
    else:
        logger.error("💥 测试失败！failure_reasons变量初始化修复无效")
        sys.exit(1)
