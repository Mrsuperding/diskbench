# 检查用户信息
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
    print("检查用户表结构...")
    cursor.execute("DESCRIBE users")
    columns = cursor.fetchall()
    print("users表结构:")
    for column in columns:
        name, type_, nullable, key, default, extra = column
        print(f"  {name}: {type_}, nullable: {nullable}, key: {key}")
    
    print("\n检查可用的用户...")
    
    # 查询用户表
    cursor.execute("SELECT id, username, role, email, status, created_at FROM users")
    users = cursor.fetchall()
    
    print(f"找到 {len(users)} 个用户:")
    for user in users:
        id_, username, role, email, status, created_at = user
        print(f"  ID: {id_}, 用户名: {username}, 角色: {role}, 邮箱: {email}, 状态: {status}, 创建时间: {created_at}")
        
    # 检查admin用户
    cursor.execute("SELECT id, username FROM users WHERE username = 'admin'")
    admin_user = cursor.fetchone()
    if admin_user:
        print(f"\n找到admin用户: ID {admin_user[0]}, 用户名: {admin_user[1]}")
    else:
        print("\n未找到admin用户!")
        
finally:
    # 关闭游标和连接
    cursor.close()
    conn.close()