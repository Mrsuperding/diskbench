import sqlite3

# 连接到SQLite数据库
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

try:
    # 查询所有表名
    print("数据库中的所有表:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(table[0])
    
    # 如果有test_tasks表，查询其结构和内容
    if ('test_tasks',) in tables:
        print("\n任务表结构:")
        cursor.execute("PRAGMA table_info(test_tasks)")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
        
        print("\n任务表内容:")
        cursor.execute("SELECT id, name FROM test_tasks")
        tasks = cursor.fetchall()
        for task in tasks:
            print(task)
    
    # 如果有test_task表，查询其结构和内容
    if ('test_task',) in tables:
        print("\n任务表结构(test_task):")
        cursor.execute("PRAGMA table_info(test_task)")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
        
        print("\n任务表内容(test_task):")
        cursor.execute("SELECT id, name FROM test_task")
        tasks = cursor.fetchall()
        for task in tasks:
            print(task)
    
    # 查询所有关联表
    print("\n查询所有关联表:")
    for table in tables:
        if 'association' in table[0]:
            print(f"\n{table[0]}表结构:")
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            for col in columns:
                print(col)
    
    # 查询测试用例表
    if ('io_test_cases',) in tables:
        print("\n测试用例表内容:")
        cursor.execute("SELECT id, name FROM io_test_cases")
        test_cases = cursor.fetchall()
        for case in test_cases:
            print(case)
    elif ('io_test_case',) in tables:
        print("\n测试用例表内容(io_test_case):")
        cursor.execute("SELECT id, name FROM io_test_case")
        test_cases = cursor.fetchall()
        for case in test_cases:
            print(case)
    
    # 查询节点表
    if ('nodes',) in tables:
        print("\n节点表内容:")
        cursor.execute("SELECT id, name FROM nodes")
        nodes = cursor.fetchall()
        for node in nodes:
            print(node)
    elif ('node',) in tables:
        print("\n节点表内容(node):")
        cursor.execute("SELECT id, name FROM node")
        nodes = cursor.fetchall()
        for node in nodes:
            print(node)
        
except Exception as e:
    print(f"查询错误: {e}")
finally:
    conn.close()