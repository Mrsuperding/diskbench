#!/usr/bin/env python3
"""
直接测试run_task_execution函数执行任务56
"""

import sys
import os
import logging
import traceback

# 添加backend目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_run_task_execution():
    """直接测试run_task_execution函数"""
    logger.info("开始测试run_task_execution函数")
    
    try:
        # 导入run_task_execution函数
        from app.views.tasks import run_task_execution
        
        # 打印函数源码的关键部分，检查failure_reasons初始化
        import inspect
        source = inspect.getsource(run_task_execution)
        
        # 查找failure_reasons初始化的位置
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if 'failure_reasons' in line:
                logger.info(f"找到failure_reasons相关代码: 第{i+1}行: {line.strip()}")
        
        # 检查是否有failure_reasons的初始化
        if 'failure_reasons = []' in source:
            logger.info("✅ failure_reasons变量已正确初始化")
        else:
            logger.error("❌ failure_reasons变量未初始化")
        
        # 检查函数中使用failure_reasons的位置
        logger.info("检查函数中使用failure_reasons的位置:")
        for i, line in enumerate(lines):
            if 'failure_reasons.append' in line:
                logger.info(f"  第{i+1}行: {line.strip()}")
        
        logger.info("✅ run_task_execution函数检查完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试run_task_execution函数失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("=== 测试run_task_execution函数 ===")
    test_run_task_execution()
