# 检查登录凭证数据表结构
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入app和数据库相关模块
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app_from_pkg
from app.py import create_app
from app.models import db, LoginCredential
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    # 打印数据库连接信息
    print(f"数据库URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # 使用inspect检查数据库结构
    inspector = inspect(db.engine)
    
    # 检查login_credentials表是否存在
    tables = inspector.get_table_names()
    print(f"数据库中的表: {tables}")
    
    if 'login_credentials' in tables:
        print("\n登录凭证数据表(login_credentials)存在!")
        
        # 获取表的结构信息
        columns = inspector.get_columns('login_credentials')
        print("表结构:")
        for column in columns:
            print(f"- {column['name']} ({column['type']}) - {column.get('comment', '无注释')}")
        
        # 检查是否有数据
        credential_count = db.session.query(LoginCredential).count()
        print(f"\n当前登录凭证数量: {credential_count}")
        
        # 如果有数据，显示部分信息
        if credential_count > 0:
            print("\n部分登录凭证信息:")
            credentials = LoginCredential.query.limit(3).all()
            for cred in credentials:
                print(f"- ID: {cred.id}, 别名: {cred.alias}, 主机: {cred.host}, 用户名: {cred.username}")
    else:
        print("\n登录凭证数据表(login_credentials)不存在!")