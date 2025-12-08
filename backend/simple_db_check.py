import sys
import os
from sqlalchemy import create_engine, text
import json

# 从.env文件获取数据库配置
MYSQL_USER = 'root'
MYSQL_PASSWORD = '123456'
MYSQL_HOST = 'localhost'
MYSQL_PORT = '3306'
MYSQL_DATABASE = 'io_platform'

# 构建MySQL连接字符串
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

try:
    # 创建数据库引擎
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        # 检查任务表是否存在
        result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'io_platform' AND table_name = 'test_tasks';"))
        table_exists = result.fetchone() is not None
        
        if table_exists:
            print("test_tasks表存在")
            
            # 查询任务ID=3
            task_query = text("SELECT id, name, description FROM test_tasks WHERE id = 3;")
            task_result = connection.execute(task_query)
            task = task_result.fetchone()
            
            if task:
                print(f"任务ID=3存在: {task.name}")
                
                # 查询任务ID=3的测试结果
                results_query = text("SELECT id, status, created_at FROM test_results WHERE test_task_id = 3;")
                results_result = connection.execute(results_query)
                results = results_result.fetchall()
                
                print(f"任务ID=3的测试结果数量: {len(results)}")
                for result in results:
                    print(f"结果ID: {result.id}, 状态: {result.status}, 创建时间: {result.created_at}")
            else:
                print("任务ID=3不存在")
                
                # 列出所有任务
                all_tasks_query = text("SELECT id, name FROM test_tasks;")
                all_tasks_result = connection.execute(all_tasks_query)
                all_tasks = all_tasks_result.fetchall()
                print(f"所有任务: {[f'Task {t.id}: {t.name}' for t in all_tasks]}")
        else:
            print("test_tasks表不存在")
            
            # 列出所有表
            tables_query = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'io_platform';")
            tables_result = connection.execute(tables_query)
            tables = tables_result.fetchall()
            print(f"所有表: {[t.table_name for t in tables]}")
            
    print("数据库检查完成")
    
except Exception as e:
    print(f"数据库操作失败: {str(e)}")
    import traceback
    traceback.print_exc()