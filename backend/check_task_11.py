#!/usr/bin/env python3
"""
检查任务ID=11的详细信息
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 从app.py导入create_app函数
import importlib.util

# 加载app.py模块
spec = importlib.util.spec_from_file_location("app_module", os.path.join(os.path.dirname(__file__), "app.py"))
app_module = importlib.util.module_from_spec(spec)
sys.modules["app_module"] = app_module
spec.loader.exec_module(app_module)

# 创建应用实例
app = app_module.create_app()

from app.models import TestTask, Node, IOTestCase, db

TASK_ID = 11

with app.app_context():
    try:
        # 获取任务
        task = TestTask.query.get(TASK_ID)
        if not task:
            print(f"任务ID={TASK_ID}不存在")
            sys.exit(1)
        
        print(f"任务ID={TASK_ID}信息:")
        task_dict = task.to_dict()
        print(f"  名称: {task_dict['name']}")
        print(f"  状态: {task_dict['status']}")
        print(f"  节点ID: {task_dict['node_ids']}")
        print(f"  测试用例ID: {task_dict['io_test_case_ids']}")
        
        # 检查节点是否存在
        print("\n检查节点是否存在:")
        node_ids = task_dict['node_ids']
        if node_ids:
            nodes = Node.query.filter(Node.id.in_(node_ids)).all()
            print(f"  找到 {len(nodes)} 个节点")
            for node in nodes:
                print(f"    节点 {node.id}: {node.name} - {node.ip_address}")
            
            if len(nodes) != len(node_ids):
                missing_ids = set(node_ids) - {node.id for node in nodes}
                print(f"  缺失节点ID: {missing_ids}")
        else:
            print("  没有关联节点")
        
        # 检查测试用例是否存在
        print("\n检查测试用例是否存在:")
        case_ids = task_dict['io_test_case_ids']
        if case_ids:
            cases = IOTestCase.query.filter(IOTestCase.id.in_(case_ids)).all()
            print(f"  找到 {len(cases)} 个测试用例")
            for case in cases:
                print(f"    测试用例 {case.id}: {case.name}")
            
            if len(cases) != len(case_ids):
                missing_ids = set(case_ids) - {case.id for case in cases}
                print(f"  缺失测试用例ID: {missing_ids}")
        else:
            print("  没有关联测试用例")
            
        # 尝试更新任务
        print("\n尝试更新任务:")
        new_node_ids = [1]
        new_case_ids = [2]
        
        # 检查新节点
        new_nodes = Node.query.filter(Node.id.in_(new_node_ids)).all()
        print(f"  新节点: {[node.id for node in new_nodes]}")
        
        # 检查新测试用例
        new_cases = IOTestCase.query.filter(IOTestCase.id.in_(new_case_ids)).all()
        print(f"  新测试用例: {[case.id for case in new_cases]}")
        
        # 更新节点关联
        task.nodes = new_nodes
        
        # 更新测试用例关联
        from sqlalchemy import text
        db.session.execute(text('DELETE FROM task_case_association WHERE test_task_id = :task_id'), {'task_id': task.id})
        for case in new_cases:
            db.session.execute(text('INSERT INTO task_case_association (test_task_id, io_test_case_id) VALUES (:task_id, :case_id)'), 
                             {'task_id': task.id, 'case_id': case.id})
        
        db.session.commit()
        print("  任务更新成功！")
        
        # 验证更新结果
        updated_task = TestTask.query.get(TASK_ID)
        updated_dict = updated_task.to_dict()
        print(f"  更新后节点ID: {updated_dict['node_ids']}")
        print(f"  更新后测试用例ID: {updated_dict['io_test_case_ids']}")
        
    except Exception as e:
        db.session.rollback()
        print(f"  更新失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()