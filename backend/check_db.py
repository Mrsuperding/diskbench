# 直接使用app.py来获取应用实例
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入app中的create_app函数
from app import create_app

app = create_app()
with app.app_context():
    # 导入模型和数据库
    from app.models import db
    
    # 打印数据库URL
    print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # 检查nodes表是否存在io_partitions字段
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    columns = [column['name'] for column in inspector.get_columns('nodes')]
    
    print(f"Nodes table columns: {columns}")
    
    # 如果没有io_partitions字段，添加它
    if 'io_partitions' not in columns:
        print("Adding io_partitions column...")
        # 使用SQLAlchemy的文本执行功能
        from sqlalchemy import text
        db.engine.execute(text("ALTER TABLE nodes ADD COLUMN io_partitions JSON DEFAULT '[]'") )
        print("io_partitions column added successfully!")
    else:
        print("io_partitions column already exists!")