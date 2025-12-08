# 检查登录凭证数据表
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入app.py中的create_app函数
import app
create_app = app.create_app
from app.models import db, LoginCredential
from sqlalchemy import inspect

# 创建应用实例
app = create_app()

with app.app_context():
    print("检查登录凭证数据表...")
    
    # 使用SQLAlchemy的inspect来检查数据库结构
    inspector = inspect(db.engine)
    
    # 检查login_credentials表是否存在
    tables = inspector.get_table_names()
    print(f"数据库中的表: {tables}")
    
    if 'login_credentials' in tables:
        print("\n✅ 登录凭证数据表(login_credentials)存在!")
        
        # 获取表结构
        columns = inspector.get_columns('login_credentials')
        print("表结构:")
        for column in columns:
            print(f"- {column['name']} ({column['type']}) - {column.get('comment', '')}")
        
        # 检查数据
        count = db.session.query(LoginCredential).count()
        print(f"\n当前凭证数量: {count}")
        
        if count > 0:
            print("\n部分凭证信息:")
            credentials = db.session.query(LoginCredential).limit(3).all()
            for cred in credentials:
                print(f"- ID: {cred.id}, 别名: {cred.alias}, 主机: {cred.host}")
    else:
        print("\n❌ 登录凭证数据表不存在!")
        
        # 如果表不存在，考虑创建
        print("尝试创建表...")
        db.create_all()
        
        # 再次检查
        if 'login_credentials' in inspector.get_table_names():
            print("✅ 表已成功创建!")
        else:
            print("❌ 表创建失败!")