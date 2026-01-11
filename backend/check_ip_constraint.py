# 检查并移除nodes表ip_address字段的唯一约束
import pymysql
from config import config

# 从配置中获取数据库连接信息
db_config = config['default'].SQLALCHEMY_DATABASE_URI

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
    print("检查nodes表ip_address字段的约束...")
    
    # 查询表结构信息
    cursor.execute("DESCRIBE nodes")
    columns = cursor.fetchall()
    print("nodes表结构:")
    for column in columns:
        name, type_, nullable, key, default, extra = column
        print(f"  {name}: {type_}, nullable: {nullable}, key: {key}, default: {default}, extra: {extra}")
    
    print("\n查询nodes表的索引信息...")
    cursor.execute("SHOW INDEX FROM nodes")
    indexes = cursor.fetchall()
    print("nodes表索引:")
    for index in indexes:
        print(f"  Index: {index[2]}, Column: {index[4]}, Unique: {index[1]}")
    
    # 查找IP地址相关的唯一约束
    cursor.execute("SHOW CREATE TABLE nodes")
    create_table_sql = cursor.fetchone()[1]
    print(f"\nCREATE TABLE SQL: {create_table_sql[:500]}...")
    
    # 如果有唯一约束，尝试移除
    if 'ip_address' in create_table_sql and ('UNIQUE' in create_table_sql or 'unique' in create_table_sql):
        print("\n检测到ip_address字段存在唯一约束，尝试移除...")
        
        # 查找约束名称
        cursor.execute("SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_NAME = 'nodes' AND COLUMN_NAME = 'ip_address' AND CONSTRAINT_TYPE = 'UNIQUE'")
        constraint = cursor.fetchone()
        
        if constraint:
            constraint_name = constraint[0]
            print(f"找到唯一约束: {constraint_name}")
            
            # 移除约束
            cursor.execute(f"ALTER TABLE nodes DROP CONSTRAINT {constraint_name}")
            conn.commit()
            print("✓ 已成功移除ip_address字段的唯一约束!")
        else:
            # 对于MySQL，可能需要使用不同的方式移除约束
            print("尝试使用DROP INDEX移除唯一约束...")
            try:
                cursor.execute("ALTER TABLE nodes DROP INDEX ip_address")
                conn.commit()
                print("✓ 已成功移除ip_address字段的唯一约束!")
            except Exception as e:
                print(f"移除约束失败: {e}")
    else:
        print("\n✓ ip_address字段不存在唯一约束!")
        
finally:
    # 关闭游标和连接
    cursor.close()
    conn.close()