from datetime import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置数据库连接
from config import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 获取配置
config_name = os.getenv('FLASK_CONFIG') or 'default'
cfg = config[config_name]

# 创建数据库引擎和会话
engine = create_engine(cfg.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

# 导入模型
from app.models import TestLog, IOStatMetric

print("查询测试日志数据...")
test_logs = session.query(TestLog).limit(10).all()
print(f"找到 {len(test_logs)} 条测试日志记录")
for log in test_logs:
    print(f"ID: {log.id}, 任务ID: {log.test_task_id}, 节点ID: {log.node_id}, 日志类型: {log.log_type}, 创建时间: {log.created_at}")

print("\n查询IOSTAT指标数据...")
iostat_metrics = session.query(IOStatMetric).limit(10).all()
print(f"找到 {len(iostat_metrics)} 条IOSTAT指标记录")
for metric in iostat_metrics:
    print(f"ID: {metric.id}, 测试日志ID: {metric.test_log_id}, 设备: {metric.device}, 时间: {metric.collection_time}, 读IOPS: {metric.read_iops}")

# 关闭会话
session.close()
