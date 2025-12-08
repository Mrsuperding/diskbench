#!/usr/bin/env python3
"""
简单检查任务ID的详细信息
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入必要的模块
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import config

# 获取数据库配置
config_name = os.environ.get('FLASK_CONFIG') or 'default'
db_config = config[config_name].SQLALCHEMY_DATABASE_URI

# 创建数据库连接
engine = create_engine(db_config)
Session = sessionmaker(bind=engine)
session = Session()

TASK_ID = 11

# 直接使用SQL查询任务信息
print(f"任务ID={TASK_ID}信息:")
try:
    # 查询任务基本信息
    task_result = session.execute(
        text('SELECT id, name, status FROM test_tasks WHERE id = :task_id'),
        {'task_id': TASK_ID}
    ).fetchone()
    
    if not task_result:
        print(f"任务ID={TASK_ID}不存在")
        session.close()
        sys.exit(1)
    
    print(f"  名称: {task_result[1]}")
    print(f"  状态: {task_result[2]}")
    
    # 查询关联的节点ID
    node_results = session.execute(
        text('SELECT node_id FROM task_node_association WHERE test_task_id = :task_id'),
        {'task_id': TASK_ID}
    ).fetchall()
    node_ids = [node[0] for node in node_results]
    print(f"  节点ID: {node_ids}")
    
    # 查询关联的测试用例ID
    case_results = session.execute(
        text('SELECT io_test_case_id FROM task_case_association WHERE test_task_id = :task_id'),
        {'task_id': TASK_ID}
    ).fetchall()
    case_ids = [case[0] for case in case_results]
    print(f"  测试用例ID: {case_ids}")
    
    # 检查节点是否存在
    print("\n检查节点是否存在:")
    if node_ids:
        existing_nodes = session.execute(
            text('SELECT id, name FROM nodes WHERE id IN :node_ids'),
            {'node_ids': tuple(node_ids)}
        ).fetchall()
        print(f"  找到 {len(existing_nodes)} 个节点")
        for node in existing_nodes:
            print(f"    节点 {node[0]}: {node[1]}")
        
        if len(existing_nodes) != len(node_ids):
            existing_node_ids = {node[0] for node in existing_nodes}
            missing_ids = set(node_ids) - existing_node_ids
            print(f"  缺失节点ID: {missing_ids}")
    else:
        print("  没有关联节点")
    
    # 检查测试用例是否存在
    print("\n检查测试用例是否存在:")
    if case_ids:
        existing_cases = session.execute(
            text('SELECT id, name FROM io_test_cases WHERE id IN :case_ids'),
            {'case_ids': tuple(case_ids)}
        ).fetchall()
        print(f"  找到 {len(existing_cases)} 个测试用例")
        for case in existing_cases:
            print(f"    测试用例 {case[0]}: {case[1]}")
        
        if len(existing_cases) != len(case_ids):
            existing_case_ids = {case[0] for case in existing_cases}
            missing_ids = set(case_ids) - existing_case_ids
            print(f"  缺失测试用例ID: {missing_ids}")
    else:
        print("  没有关联测试用例")
        
    session.close()
    print("\n查询完成！")
    
except Exception as e:
    session.close()
    print(f"查询失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)