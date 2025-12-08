# 直接数据库查询脚本
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 导入模型
from app.models.test_task import TestTask

# 从app.py中获取数据库配置
import importlib.util

spec = importlib.util.spec_from_file_location("app", os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"))
app_module = importlib.util.module_from_spec(spec)

try:
    # 执行模块，捕获可能的导入错误
    spec.loader.exec_module(app_module)
    
    # 获取数据库URI
    db_uri = app_module.app.config['SQLALCHEMY_DATABASE_URI']
    
    # 创建数据库引擎
    engine = create_engine(db_uri)
    
    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 查询任务ID为3的状态
        task = session.query(TestTask).get(3)
        if task:
            print(f'Task ID: {task.id}')
            print(f'Task Name: {task.name}')
            print(f'Task Status: {task.status}')
            print(f'Task Created At: {task.created_at}')
            print(f'Task Started At: {task.started_at}')
            print(f'Task Completed At: {task.completed_at}')
        else:
            print('Task with ID 3 not found')
    finally:
        # 关闭会话
        session.close()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()