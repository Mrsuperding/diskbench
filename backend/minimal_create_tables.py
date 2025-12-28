import sys
import os
from flask import Flask
from app.models import db
from config import Config

# 创建最小的Flask应用实例
app = Flask(__name__)

# 配置数据库
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

# 导入所有模型
from app.models import *

# 创建数据库表
with app.app_context():
    print("开始创建数据库表...")
    db.create_all()
    print("数据库表创建完成！")
