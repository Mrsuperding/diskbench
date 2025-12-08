import pymysql
import config

# 从配置中获取数据库连接信息
db_config = config.config['default'].SQLALCHEMY_DATABASE_URI

# 解析连接字符串
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
    # 将node_id列改为可空
    print("修改test_tasks表，将node_id列改为可空...")
    cursor.execute("ALTER TABLE test_tasks MODIFY COLUMN node_id INT NULL")
    conn.commit()
    print("修改成功！")
    
    # 同样修改io_test_case_id列，因为我们将使用多对多关系
    print("\n修改test_tasks表，将io_test_case_id列改为可空...")
    cursor.execute("ALTER TABLE test_tasks MODIFY COLUMN io_test_case_id INT NULL")
    conn.commit()
    print("修改成功！")
    
    # 验证修改结果
    cursor.execute("DESCRIBE test_tasks")
    columns = cursor.fetchall()
    
    print("\n修改后的test_tasks表结构:")
    for column in columns:
        name, type_, nullable, key, default, extra = column
        if name in ['node_id', 'io_test_case_id']:
            print(f"  {name}: {type_} (nullable: {nullable})")
            
finally:
    # 关闭游标和连接
    cursor.close()
    conn.close()