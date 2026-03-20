#!/usr/bin/env python3
import logging
import time
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_task_execution():
    """测试任务执行功能"""
    logger.info("开始测试任务执行功能...")
    
    try:
        # 导入必要的模块
        from app import create_app
        from app.models.test_task import TestTask, TaskExecution
        from app.models import db
        
        # 创建应用实例
        app = create_app()
        logger.info("创建应用实例成功")
        
        # 在应用上下文中测试
        with app.app_context():
            logger.info("进入应用上下文成功")
            
            # 测试数据库连接
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            logger.info("数据库连接测试成功")
            
            # 获取一个测试任务
            test_task = TestTask.query.first()
            if not test_task:
                logger.warning("没有找到测试任务，创建一个测试任务")
                # 创建一个测试任务
                test_task = TestTask(
                    name="测试任务",
                    description="用于测试任务执行功能",
                    status="pending",
                    created_at=datetime.utcnow()
                )
                db.session.add(test_task)
                db.session.commit()
                logger.info(f"创建测试任务成功，ID: {test_task.id}")
            else:
                logger.info(f"找到测试任务，ID: {test_task.id}, 名称: {test_task.name}")
            
            # 测试创建执行记录
            execution = TaskExecution(
                test_task_id=test_task.id,
                status='running',
                start_time=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db.session.add(execution)
            db.session.flush()  # 获取execution.id
            
            # 提交事务
            db.session.commit()
            logger.info(f"创建执行记录成功，ID: {execution.id}")
            
            # 在主线程中获取 execution_id
            execution_id = execution.id
            logger.info(f"在主线程中获取 execution_id: {execution_id}")
            
            # 测试 run_task_execution 函数
            logger.info("测试 run_task_execution 函数")
            from app.views.tasks import run_task_execution
            
            # 执行任务
            run_task_execution(test_task.id, execution_id, app)
            logger.info("run_task_execution 函数执行成功")
            
            # 等待一段时间，让任务执行完成
            logger.info("等待任务执行完成...")
            time.sleep(5)
            
            # 检查任务状态
            updated_task = TestTask.query.get(test_task.id)
            updated_execution = TaskExecution.query.get(execution_id)
            logger.info(f"任务状态: {updated_task.status}")
            logger.info(f"执行记录状态: {updated_execution.status}")
            
            # 清理测试数据
            db.session.delete(updated_execution)
            db.session.commit()
            logger.info("清理测试数据成功")
        
        logger.info("任务执行功能测试完成")
        return True
    
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_task_execution()
    if success:
        logger.info("✅ 任务执行功能测试通过！")
    else:
        logger.error("❌ 任务执行功能测试失败！")
