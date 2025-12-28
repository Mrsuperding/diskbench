import sys
import os
import importlib.util

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 动态导入app.py文件
app_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
spec = importlib.util.spec_from_file_location('app_module', app_py_path)
app_module = importlib.util.module_from_spec(spec)
sys.modules['app_module'] = app_module
spec.loader.exec_module(app_module)

# 导入必要的模块
from app.models import db

# 创建应用实例
app = app_module.create_app()

with app.app_context():
    print("开始创建数据库表...")
    # 创建所有表
    db.create_all()
    print("数据库表创建完成！")
