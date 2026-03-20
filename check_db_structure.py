#!/usr/bin/env python3
"""
检查数据库表结构，确认io_performance_data表是否包含lat_p9999列
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

def check_table_structure():
    """检查io_performance_data表的结构"""
    try:
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        print("连接数据库成功！")
        
        # 检查io_performance_data表结构
        cursor.execute("DESCRIBE io_performance_data;")
        columns = cursor.fetchall()
        
        print("\nio_performance_data表结构:")
        print("-" * 80)
        print(f"{'Field':<20} {'Type':<20} {'Null':<10} {'Key':<10} {'Default':<15} {'Extra':<10}")
        print("-" * 80)
        
        # 检查是否存在lat_p9999列
        lat_p9999_exists = False
        for column in columns:
            field, type_, null, key, default, extra = column
            print(f"{field:<20} {type_:<20} {null:<10} {key:<10} {str(default):<15} {extra:<10}")
            if field == 'lat_p9999':
                lat_p9999_exists = True
        
        print("-" * 80)
        
        if lat_p9999_exists:
            print("\n✓ lat_p9999列存在于io_performance_data表中")
        else:
            print("\n✗ lat_p9999列不存在于io_performance_data表中")
            print("需要添加该列")
        
        return lat_p9999_exists
        
    except pymysql.MySQLError as e:
        print(f"数据库连接或查询错误: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_table_structure()