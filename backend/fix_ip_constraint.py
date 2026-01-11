# 移除nodes表ip_address字段的唯一约束
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
    print("移除nodes表ip_address字段的唯一约束...")
    
    # 直接移除ip_address索引（从DESCRIBE输出看到key为UNI）
    cursor.execute("ALTER TABLE nodes DROP INDEX ip_address")
    conn.commit()
    print("✓ 已成功移除ip_address字段的唯一约束!")
    
    # 检查是否还有其他IP相关的唯一索引
    cursor.execute("SHOW INDEX FROM nodes")
    indexes = cursor.fetchall()
    ip_indexes = [index for index in indexes if index[4] == 'ip_address']
    
    if ip_indexes:
        print("\n还存在其他IP相关的索引:")
        for index in ip_indexes:
            print(f"  Index: {index[2]}, Column: {index[4]}, Unique: {index[1]}")
    else:
        print("\n✓ 已没有IP地址相关的索引!")
    
    # 再次检查表结构
    cursor.execute("DESCRIBE nodes")
    columns = cursor.fetchall()
    print("\n更新后的nodes表结构:")
    for column in columns:
        name, type_, nullable, key, default, extra = column
        if name == 'ip_address':
            print(f"  {name}: {type_}, nullable: {nullable}, key: {key}")
            
finally:
    # 关闭游标和连接
    cursor.close()
    conn.close()