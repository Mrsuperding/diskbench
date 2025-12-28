import sys
import os
from sqlalchemy import create_engine
from app.models import db
from config import Config

# 创建数据库引擎
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

# 绑定db对象到引擎
db.engine = engine

# 创建所有表
print("开始创建数据库表...")
db.create_all()
print("数据库表创建完成！")
