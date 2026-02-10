# 直接查询数据库检查task 33
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
    print("检查task 33...")
    
    # 查询test_tasks表
    cursor.execute("SELECT id, name, status, created_at, completed_at FROM test_tasks WHERE id = 33")
    task = cursor.fetchone()
    
    if task:
        id_, name, status, created_at, completed_at = task
        print(f"找到task 33: {name}")
        print(f"状态: {status}")
        print(f"创建时间: {created_at}")
        print(f"完成时间: {completed_at}")
        
        # 查询执行实例
        cursor.execute("SELECT id, status, log_file_path FROM task_executions WHERE task_id = 33")
        executions = cursor.fetchall()
        print(f"\n执行实例: {len(executions)} 个")
        for execution in executions:
            exec_id, exec_status, log_file_path = execution
            print(f"  ID: {exec_id}, 状态: {exec_status}")
            print(f"  日志文件路径: {log_file_path}")
    else:
        print("未找到task 33")
    
    # 查询所有测试任务
    print("\n最近的测试任务:")
    cursor.execute("SELECT id, name, status FROM test_tasks ORDER BY id DESC LIMIT 10")
    tasks = cursor.fetchall()
    for t in tasks:
        id_, name, status = t
        print(f"  ID: {id_}, 名称: {name}, 状态: {status}")
    
    # 查询test_logs表
    print("\n检查test_logs表...")
    cursor.execute("SELECT COUNT(*) FROM test_logs WHERE test_task_id = 33")
    log_count = cursor.fetchone()[0]
    print(f"task 33的日志记录数: {log_count}")
    
finally:
    # 关闭游标和连接
    cursor.close()
    conn.close()
