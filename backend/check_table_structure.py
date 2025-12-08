from app.py import create_app
from app.models import db
from sqlalchemy import inspect

# 创建应用实例
app = create_app()

with app.app_context():
    # 获取表结构信息
    inspector = inspect(db.engine)
    
    # 查看test_tasks表的所有列
    columns = inspector.get_columns('test_tasks')
    print("\ntest_tasks表结构:")
    for column in columns:
        print(f"  {column['name']}: {column['type']} (nullable: {column['nullable']}, default: {column['default']})")
    
    # 查看是否有node_id列
    has_node_id = any(col['name'] == 'node_id' for col in columns)
    print(f"\n表中是否有node_id列: {has_node_id}")
    
    # 查看关联表是否存在
    has_task_node_association = inspector.has_table('task_node_association')
    print(f"task_node_association表是否存在: {has_task_node_association}")
    
    if has_task_node_association:
        association_columns = inspector.get_columns('task_node_association')
        print("\ntask_node_association表结构:")
        for column in association_columns:
            print(f"  {column['name']}: {column['type']}")