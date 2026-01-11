# 检查登录凭证信息
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
    print("检查登录凭证表结构...")
    cursor.execute("DESCRIBE login_credentials")
    columns = cursor.fetchall()
    print("login_credentials表结构:")
    for column in columns:
        name, type_, nullable, key, default, extra = column
        print(f"  {name}: {type_}, nullable: {nullable}, key: {key}")
    
    print("\n检查可用的登录凭证...")
    
    # 查询登录凭证表，只查询存在的字段
    cursor.execute("SELECT id, username, created_at FROM login_credentials")
    credentials = cursor.fetchall()
    
    print(f"找到 {len(credentials)} 个登录凭证:")
    for credential in credentials:
        id_, username, created_at = credential
        print(f"  ID: {id_}, 用户名: {username}, 创建时间: {created_at}")
        
    # 如果有凭证，返回第一个的ID
    if credentials:
        print(f"\n建议使用第一个凭证ID: {credentials[0][0]}")
    else:
        print("\n没有找到任何登录凭证，请先创建登录凭证!")
        
finally:
    # 关闭游标和连接
    cursor.close()
    conn.close()