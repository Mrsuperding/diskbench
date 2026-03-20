#!/usr/bin/env python3
"""
调试任务56执行失败的问题
"""

import sys
import os
import logging
import traceback

# 添加backend目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_task_56():
    """调试任务56执行失败的问题"""
    logger.info("开始调试任务56")
    
    try:
        # 直接从app.py文件导入create_app
        import importlib.util
        backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
        spec = importlib.util.spec_from_file_location("app", os.path.join(backend_dir, 'app.py'))
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        create_app = app_module.create_app
        
        # 创建应用实例
        app = create_app()
        
        with app.app_context():
            # 导入模型
            from app.models import db, TestTask, Node, IOTestCase, TaskExecution
            from sqlalchemy import text
            
            # 查询任务56
            task = TestTask.query.get(56)
            if not task:
                logger.error("任务56不存在")
                return False
            
            # 打印任务基本信息
            logger.info(f"任务ID: {task.id}")
            logger.info(f"任务名称: {task.name}")
            logger.info(f"任务状态: {task.status}")
            
            # 查询关联的节点
            nodes = task.nodes
            logger.info(f"关联的节点数量: {len(nodes)}")
            for i, node in enumerate(nodes):
                logger.info(f"节点 {i+1}:")
                logger.info(f"  节点ID: {node.id}")
                logger.info(f"  节点名称: {node.name}")
                logger.info(f"  主机地址: {node.ip_address}")
                logger.info(f"  登录凭证: {node.login_credential.alias if node.login_credential else '无'}")
                if node.login_credential:
                    logger.info(f"  凭证主机: {node.login_credential.host}")
                    logger.info(f"  凭证端口: {node.login_credential.port}")
                    logger.info(f"  凭证用户名: {node.login_credential.username}")
                    logger.info(f"  平台分区: {node.login_credential.platform_partition}")
            
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
            
            # 检查任务是否有节点和IO测试用例
            if not nodes:
                logger.error("任务56没有关联任何节点")
                return False
            
            if not io_test_cases:
                logger.error("任务56没有关联任何IO测试用例")
                return False
            
            # 检查节点是否有登录凭证
            for node in nodes:
                if not node.login_credential:
                    logger.error(f"节点 {node.name} 没有关联登录凭证")
                    return False
            
            logger.info("✅ 任务56配置检查完成，准备执行")
            
            # 创建任务执行记录
            task_execution = TaskExecution(
                test_task_id=56,
                status='running',
                start_time=app_module.datetime.utcnow()
            )
            db.session.add(task_execution)
            db.session.commit()
            
            logger.info(f"创建执行记录: execution_id={task_execution.id}")
            
            # 导入run_task_execution函数
            from app.views.tasks import run_task_execution
            
            # 执行任务
            logger.info("开始执行任务...")
            try:
                run_task_execution(56, task_execution.id, app)
                logger.info("任务执行完成")
            except Exception as e:
                logger.error(f"执行任务时发生异常: {str(e)}")
                logger.error(traceback.format_exc())
            
            # 查询执行结果
            updated_execution = TaskExecution.query.get(task_execution.id)
            updated_task = TestTask.query.get(56)
            
            logger.info(f"任务执行结果:")
            logger.info(f"  任务状态: {updated_task.status}")
            logger.info(f"  执行状态: {updated_execution.status}")
            logger.info(f"  错误信息: {updated_execution.error_message}")
            
            return True
            
    except Exception as e:
        logger.error(f"调试任务56失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("=== 调试任务56执行失败问题 ===")
    debug_task_56()
