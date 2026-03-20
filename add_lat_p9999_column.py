#!/usr/bin/env python3
"""
向io_performance_data表添加lat_p9999列
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

def add_lat_p9999_column():
    """向io_performance_data表添加lat_p9999列"""
    try:
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        print("连接数据库成功！")
        
        # 执行ALTER TABLE语句，添加lat_p9999列
        alter_sql = "ALTER TABLE io_performance_data ADD COLUMN lat_p9999 FLOAT COMMENT 'P9999延迟(ms)';"
        cursor.execute(alter_sql)
        conn.commit()
        
        print("\n✓ 成功向io_performance_data表添加lat_p9999列")
        
        # 验证列是否添加成功
        cursor.execute("DESCRIBE io_performance_data;")
        columns = cursor.fetchall()
        
        print("\n更新后的io_performance_data表结构:")
        print("-" * 80)
        print(f"{'Field':<20} {'Type':<20} {'Null':<10} {'Key':<10} {'Default':<15} {'Extra':<10}")
        print("-" * 80)
        
        lat_p9999_exists = False
        for column in columns:
            field, type_, null, key, default, extra = column
            print(f"{field:<20} {type_:<20} {null:<10} {key:<10} {str(default):<15} {extra:<10}")
            if field == 'lat_p9999':
                lat_p9999_exists = True
        
        print("-" * 80)
        
        if lat_p9999_exists:
            print("\n✓ lat_p9999列已成功添加到io_performance_data表中")
        else:
            print("\n✗ lat_p9999列添加失败")
        
        return lat_p9999_exists
        
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
    add_lat_p9999_column()