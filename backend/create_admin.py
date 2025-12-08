import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import app as app_module
from app.models import db, User

app = app_module.create_app()

with app.app_context():
    db.create_all()
    
    # 检查是否已存在管理员用户
    admin = User.query.filter_by(username='admin').first()
    
    if not admin:
        # 创建管理员用户
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('adminpassword')
        
        db.session.add(admin)
        db.session.commit()
        
        print('管理员用户创建成功！')
        print(f'用户名: admin')
        print(f'邮箱: admin@example.com')
        print(f'密码: adminpassword')
    else:
        print('管理员用户已存在！')
        print(f'用户名: {admin.username}')
        print(f'邮箱: {admin.email}')