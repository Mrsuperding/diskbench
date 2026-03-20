#!/usr/bin/env python3
"""
执行任务56并捕获错误信息
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

def execute_task_56():
    """执行任务56并捕获错误信息"""
    logger.info("开始执行任务56")
    
    try:
        # 导入必要的模块
        import importlib.util
        import sys
        
        # 直接从app.py文件导入create_app
        backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
        spec = importlib.util.spec_from_file_location("app", os.path.join(backend_dir, 'app.py'))
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        create_app = app_module.create_app
        
        # 创建应用实例
        app = create_app()
        
        with app.app_context():
            # 导入模型和函数
            from app.models import db, TestTask, TaskExecution
            from app.views.tasks import run_task_execution
            from datetime import datetime
            
            # 查询任务56
            task = TestTask.query.get(56)
            if not task:
                logger.error("任务56不存在")
                return False
            
            # 打印任务基本信息
            logger.info(f"任务ID: {task.id}")
            logger.info(f"任务名称: {task.name}")
            logger.info(f"当前状态: {task.status}")
            
            # 创建任务执行记录
            task_execution = TaskExecution(
                test_task_id=56,
                status='running',
                start_time=datetime.utcnow()
            )
            db.session.add(task_execution)
            db.session.commit()
            
            logger.info(f"创建执行记录: execution_id={task_execution.id}")
            
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
        logger.error(f"执行任务56失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("=== 执行任务56并分析错误信息 ===")
    execute_task_56()
