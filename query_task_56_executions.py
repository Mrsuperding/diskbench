#!/usr/bin/env python3
"""
查询任务56的执行记录，获取错误信息
"""

import sys
import os
import logging

# 添加backend目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def query_task_56_executions():
    """查询任务56的执行记录"""
    logger.info("开始查询任务56的执行记录")
    
    try:
        # 导入必要的模块
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        from config import config
        
        # 获取数据库配置
        app_config = config['default']
        db_url = app_config.SQLALCHEMY_DATABASE_URI
        
        # 创建数据库引擎和会话
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 直接执行SQL查询获取任务56的执行记录
        logger.info("查询任务56的执行记录")
        executions = session.execute(
            text("SELECT id, test_task_id, status, start_time, end_time, error_message, duration "
                 "FROM task_executions "
                 "WHERE test_task_id = 56 "
                 "ORDER BY start_time DESC")
        ).fetchall()
        
        logger.info(f"找到 {len(executions)} 条执行记录")
        
        for i, execution in enumerate(executions):
            execution_id, task_id, status, start_time, end_time, error_message, duration = execution
            logger.info(f"执行记录 {i+1}:")
            logger.info(f"  执行ID: {execution_id}")
            logger.info(f"  任务ID: {task_id}")
            logger.info(f"  状态: {status}")
            logger.info(f"  开始时间: {start_time}")
            logger.info(f"  结束时间: {end_time}")
            logger.info(f"  持续时间: {duration}秒")
            logger.info(f"  错误信息: {error_message}")
            logger.info("")
        
        # 查询任务56的基本信息
        task_info = session.execute(
            text("SELECT id, name, status, created_at, started_at, completed_at "
                 "FROM test_task "
                 "WHERE id = 56")
        ).fetchone()
        
        if task_info:
            task_id, task_name, task_status, created_at, started_at, completed_at = task_info
            logger.info("任务56基本信息:")
            logger.info(f"  任务ID: {task_id}")
            logger.info(f"  任务名称: {task_name}")
            logger.info(f"  任务状态: {task_status}")
            logger.info(f"  创建时间: {created_at}")
            logger.info(f"  开始时间: {started_at}")
            logger.info(f"  完成时间: {completed_at}")
        
        # 查询任务56关联的节点
        nodes = session.execute(
            text("SELECT n.id, n.name, n.ip_address, n.type "
                 "FROM node n "
                 "JOIN task_node_association tna ON n.id = tna.node_id "
                 "WHERE tna.test_task_id = 56")
        ).fetchall()
        
        logger.info(f"任务56关联的节点数量: {len(nodes)}")
        for i, node in enumerate(nodes):
            node_id, node_name, ip_address, node_type = node
            logger.info(f"节点 {i+1}:")
            logger.info(f"  节点ID: {node_id}")
            logger.info(f"  节点名称: {node_name}")
            logger.info(f"  主机地址: {ip_address}")
            logger.info(f"  节点类型: {node_type}")
        
        # 查询任务56关联的IO测试用例
        io_cases = session.execute(
            text("SELECT i.id, i.name, i.tool, i.parameters "
                 "FROM io_test_case i "
                 "JOIN task_case_association tca ON i.id = tca.io_test_case_id "
                 "WHERE tca.test_task_id = 56")
        ).fetchall()
        
        logger.info(f"任务56关联的IO测试用例数量: {len(io_cases)}")
        for i, io_case in enumerate(io_cases):
            case_id, case_name, tool, parameters = io_case
            logger.info(f"IO测试用例 {i+1}:")
            logger.info(f"  用例ID: {case_id}")
            logger.info(f"  用例名称: {case_name}")
            logger.info(f"  工具: {tool}")
            logger.info(f"  参数: {parameters}")
        
        session.close()
        logger.info("✅ 任务56执行记录查询完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 查询任务56执行记录失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("=== 查询任务56执行记录 ===")
    query_task_56_executions()
