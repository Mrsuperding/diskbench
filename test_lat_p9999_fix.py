#!/usr/bin/env python3
"""
测试 lat_p9999 列修复是否成功
"""

import pymysql
from backend.config import Config

# 从配置中获取数据库连接信息
config = Config()
db_config = {
    'host': config.MYSQL_HOST,
    'port': int(config.MYSQL_PORT),
    'user': config.MYSQL_USER,
    'password': config.MYSQL_PASSWORD,
    'database': config.MYSQL_DATABASE
}

def test_lat_p9999_insert():
    """测试向io_performance_data表插入包含lat_p9999字段的数据"""
    try:
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        print("连接数据库成功！")
        
        # 准备测试数据
        test_data = {
            'test_task_id': 90,
            'node_id': 4,
            'io_test_case_id': 4,
            'task_execution_id': 120,
            'read_iops': 1984.0,
            'write_iops': 0,
            'read_kbps': 7936.0,
            'write_kbps': 0,
            'await_time': 0.50227,
            'svctm': 0,
            'util': 0,
            'lat_p99': 8.586,
            'lat_p9999': 12.911,  # 测试添加的字段
            'lat_max': 33.984,
            'io_model_name': '4k_1d_randread_1n',
            'device': 'vdb'
        }
        
        # 构建插入语句
        columns = ', '.join(test_data.keys())
        placeholders = ', '.join(['%s'] * len(test_data))
        insert_sql = f"INSERT INTO io_performance_data ({columns}, collection_time, created_at) VALUES ({placeholders}, NOW(), NOW());"
        
        # 执行插入操作
        cursor.execute(insert_sql, list(test_data.values()))
        conn.commit()
        
        print("\n✓ 成功向io_performance_data表插入包含lat_p9999字段的数据")
        
        # 验证数据是否正确插入
        cursor.execute("SELECT lat_p9999 FROM io_performance_data WHERE test_task_id = %s ORDER BY id DESC LIMIT 1;", (test_data['test_task_id'],))
        result = cursor.fetchone()
        
        if result and result[0] == test_data['lat_p9999']:
            print(f"\n✓ 验证成功！lat_p9999值正确存储: {result[0]}")
            return True
        else:
            print("\n✗ 验证失败！lat_p9999值未正确存储")
            return False
        
    except pymysql.MySQLError as e:
        print(f"数据库操作错误: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_lat_p9999_insert()