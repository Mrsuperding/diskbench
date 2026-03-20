#!/usr/bin/env python3
"""
查询任务56的详细信息（简化版）
"""

import sys
import os
import logging

# 添加backend目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_task_56_info():
    """获取任务56的详细信息"""
    logger.info("开始查询任务56的详细信息")
    
    try:
        # 导入配置和数据库
        from config import config
        from app.models import db, TestTask, Node, IOTestCase, TaskExecution
        from sqlalchemy import text
        
        # 创建数据库连接
        app_config = config['default']
        db_url = app_config.SQLALCHEMY_DATABASE_URI
        
        # 初始化数据库
        db.engine.dispose()
        
        # 查询任务56
        task = TestTask.query.get(56)
        if not task:
            logger.error("任务56不存在")
            return False
        
        # 打印任务基本信息
        logger.info(f"任务ID: {task.id}")
        logger.info(f"任务名称: {task.name}")
        logger.info(f"任务状态: {task.status}")
        logger.info(f"任务描述: {task.description}")
        logger.info(f"创建时间: {task.created_at}")
        logger.info(f"开始时间: {task.started_at}")
        logger.info(f"完成时间: {task.completed_at}")
        logger.info(f"创建者: {task.created_by}")
        
        # 查询关联的节点
        nodes = task.nodes
        logger.info(f"关联的节点数量: {len(nodes)}")
        for i, node in enumerate(nodes):
            logger.info(f"节点 {i+1}:")
            logger.info(f"  节点ID: {node.id}")
            logger.info(f"  节点名称: {node.name}")
            logger.info(f"  主机地址: {node.ip_address}")
            logger.info(f"  节点类型: {node.type}")
            logger.info(f"  登录凭证: {node.login_credential.alias if node.login_credential else '无'}")
        
        # 查询关联的IO测试用例
        case_ids = db.session.execute(
            text('SELECT io_test_case_id FROM task_case_association WHERE test_task_id = :task_id'),
            {'task_id': 56}
        ).fetchall()
        io_test_case_ids = [case_id[0] for case_id in case_ids]
        io_test_cases = IOTestCase.query.filter(IOTestCase.id.in_(io_test_case_ids)).all()
        
        logger.info(f"关联的IO测试用例数量: {len(io_test_cases)}")
        for i, io_test_case in enumerate(io_test_cases):
            logger.info(f"IO测试用例 {i+1}:")
            logger.info(f"  用例ID: {io_test_case.id}")
            logger.info(f"  用例名称: {io_test_case.name}")
            logger.info(f"  工具: {io_test_case.tool}")
            logger.info(f"  参数: {io_test_case.parameters}")
        
        # 查询任务执行记录
        executions = TaskExecution.query.filter_by(test_task_id=56).all()
        logger.info(f"任务执行记录数量: {len(executions)}")
        for i, execution in enumerate(executions):
            logger.info(f"执行记录 {i+1}:")
            logger.info(f"  执行ID: {execution.id}")
            logger.info(f"  状态: {execution.status}")
            logger.info(f"  开始时间: {execution.start_time}")
            logger.info(f"  结束时间: {execution.end_time}")
            logger.info(f"  错误信息: {execution.error_message}")
        
        logger.info("✅ 任务56信息查询完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 查询任务56信息失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("=== 查询任务56详细信息 ===")
    get_task_56_info()
