import pymysql
import config

# 从配置中获取数据库连接信息
db_config = config.config['default'].SQLALCHEMY_DATABASE_URI

# 解析连接字符串
# 格式: mysql+pymysql://username:password@host:port/database
import re
match = re.match(r'mysql\+pymysql://(.*?):(.*?)@(.*?):(\d+)/(.*?)$', db_config)
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

# 创建游标
cursor = conn.cursor()

try:
    # 查询test_tasks表结构
    cursor.execute("DESCRIBE test_tasks")
    columns = cursor.fetchall()
    
    print("\ntest_tasks表结构:")
    for column in columns:
        name, type_, nullable, key, default, extra = column
        print(f"  {name}: {type_} (nullable: {nullable}, key: {key}, default: {default}, extra: {extra})")
    
    # 查询是否有node_id列
    cursor.execute("SHOW COLUMNS FROM test_tasks LIKE 'node_id'")
    has_node_id = cursor.fetchone() is not None
    print(f"\n表中是否有node_id列: {has_node_id}")
    
    # 查询关联表是否存在
    cursor.execute("SHOW TABLES LIKE 'task_node_association'")
    has_task_node_association = cursor.fetchone() is not None
    print(f"task_node_association表是否存在: {has_task_node_association}")
    
    if has_task_node_association:
        cursor.execute("DESCRIBE task_node_association")
        association_columns = cursor.fetchall()
        print("\ntask_node_association表结构:")
        for column in association_columns:
            name, type_, nullable, key, default, extra = column
            print(f"  {name}: {type_} (key: {key})")
    
    # 查询task_case_association表是否存在
    cursor.execute("SHOW TABLES LIKE 'task_case_association'")
    has_task_case_association = cursor.fetchone() is not None
    print(f"\ntask_case_association表是否存在: {has_task_case_association}")
    
    if has_task_case_association:
        cursor.execute("DESCRIBE task_case_association")
        association_columns = cursor.fetchall()
        print("\ntask_case_association表结构:")
        for column in association_columns:
            name, type_, nullable, key, default, extra = column
            print(f"  {name}: {type_} (key: {key})")
            
finally:
    # 关闭游标和连接
    cursor.close()
    conn.close()