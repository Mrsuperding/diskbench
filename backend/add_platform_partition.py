import pymysql
import re
from config import Config

# 获取数据库连接信息
db_uri = Config.SQLALCHEMY_DATABASE_URI
match = re.match(r'mysql\+pymysql://(.*?):(.*?)@(.*?):(\d+)/(.*?)$', db_uri)
if not match:
    raise ValueError("Invalid database URI format")

user, password, host, port, database = match.groups()
port = int(port)

# 连接数据库
conn = pymysql.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    database=database,
    charset='utf8mb4'
)

cursor = conn.cursor()

try:
    # 检查login_credentials表结构
    print("当前login_credentials表结构:")
    cursor.execute("DESCRIBE login_credentials")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
    
    # 检查是否已存在platform_partition字段
    has_platform_partition = any(col[0] == 'platform_partition' for col in columns)
    
    if not has_platform_partition:
        # 添加platform_partition字段
        print("\n添加platform_partition字段...")
        cursor.execute("ALTER TABLE login_credentials ADD COLUMN platform_partition VARCHAR(255) DEFAULT '/opt/io_platform' COMMENT '平台在节点的运行日志和IO日志以及fio需要的各种依赖文件的存放分区'")
        conn.commit()
        print("platform_partition字段添加成功!")
        
        # 再次检查表结构
        print("\n更新后的login_credentials表结构:")
        cursor.execute("DESCRIBE login_credentials")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
    else:
        print("\nplatform_partition字段已存在，无需添加!")
        
finally:
    # 关闭游标和连接
    cursor.close()
    conn.close()