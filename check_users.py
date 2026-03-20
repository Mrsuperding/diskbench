import pymysql

# 连接数据库
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='123456',
    database='io_platform',
    charset='utf8mb4'
)

try:
    with conn.cursor() as cursor:
        # 查询用户表
        cursor.execute("SELECT id, username, email FROM users")
        users = cursor.fetchall()
        
        print("数据库中的用户:")
        for user in users:
            print(f"ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}")
finally:
    conn.close()
