# 直接通过数据库测试重复IP功能
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
    print("测试前检查节点表结构...")
    cursor.execute("DESCRIBE nodes")
    columns = cursor.fetchall()
    for column in columns:
        name, type_, nullable, key, default, extra = column
        if name == 'ip_address':
            print(f"  ip_address: {type_}, nullable: {nullable}, key: {key}")
    
    # 生成唯一的节点名称
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    node_name1 = f"test_node_{timestamp}_1"
    node_name2 = f"test_node_{timestamp}_2"
    
    print(f"\n测试创建两个具有相同IP地址的节点...")
    print(f"节点1: {node_name1}, IP: 127.0.0.1")
    print(f"节点2: {node_name2}, IP: 127.0.0.1")
    
    # 插入第一个节点
    cursor.execute(
        "INSERT INTO nodes (name, ip_address, status, login_credential_id, created_by, created_at, updated_at) VALUES (%s, %s, 'inactive', 1, 1, NOW(), NOW())",
        (node_name1, '127.0.0.1')
    )
    conn.commit()
    node1_id = cursor.lastrowid
    print(f"✓ 节点1创建成功，ID: {node1_id}")
    
    # 插入第二个节点（相同IP）
    try:
        cursor.execute(
            "INSERT INTO nodes (name, ip_address, status, login_credential_id, created_by, created_at, updated_at) VALUES (%s, %s, 'inactive', 1, 1, NOW(), NOW())",
            (node_name2, '127.0.0.1')
        )
        conn.commit()
        node2_id = cursor.lastrowid
        print(f"✓ 节点2创建成功，ID: {node2_id}")
        print("✅ 测试通过! 已成功创建两个具有相同IP地址(127.0.0.1)的节点")
        
        # 查询验证
        cursor.execute("SELECT id, name, ip_address FROM nodes WHERE ip_address = '127.0.0.1' ORDER BY created_at DESC LIMIT 2")
        nodes = cursor.fetchall()
        print("\n验证结果:")
        for node in nodes:
            print(f"  ID: {node[0]}, 名称: {node[1]}, IP: {node[2]}")
        
    except Exception as e:
        print(f"❌ 节点2创建失败: {e}")
        print("❌ 测试失败! 无法创建具有相同IP地址的节点")
        
    # 清理测试数据
    print("\n清理测试数据...")
    cursor.execute("DELETE FROM nodes WHERE name IN (%s, %s)", (node_name1, node_name2))
    conn.commit()
    print("✓ 测试数据已清理")
    
finally:
    # 关闭游标和连接
    cursor.close()
    conn.close()