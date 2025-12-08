#!/usr/bin/env python3
"""
调试任务更新功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 从app.py导入app实例和db
from app import db
from app.models import TestTask, Node, IOTestCase
import json
import app.py as app_module

# 获取应用实例
app_instance = app_module.app

# 任务ID
TASK_ID = 11

with app_instance.app_context():
    try:
        # 获取任务
        task = TestTask.query.get(TASK_ID)
        if not task:
            print(f"任务ID={TASK_ID}不存在")
            sys.exit(1)
        
        print(f"原任务信息: {task.to_dict()}")
        
        # 尝试更新任务
        new_node_ids = [1, 2]
        new_case_ids = [1, 2, 3]
        
        # 检查节点是否存在
        nodes = Node.query.filter(Node.id.in_(new_node_ids)).all()
        print(f"找到节点: {[node.id for node in nodes]}")
        
        # 检查测试用例是否存在
        test_cases = IOTestCase.query.filter(IOTestCase.id.in_(new_case_ids)).all()
        print(f"找到测试用例: {[tc.id for tc in test_cases]}")
        
        # 更新节点关联
        task.nodes = nodes
        
        # 更新测试用例关联
        from sqlalchemy import text
        db.session.execute(text('DELETE FROM task_case_association WHERE test_task_id = :task_id'), {'task_id': task.id})
        for tc in test_cases:
            db.session.execute(text('INSERT INTO task_case_association (test_task_id, io_test_case_id) VALUES (:task_id, :case_id)'), 
                             {'task_id': task.id, 'case_id': tc.id})
        
        db.session.flush()
        
        # 测试to_dict方法
        task_dict = task.to_dict()
        print(f"更新后的任务字典: {json.dumps(task_dict, indent=2, ensure_ascii=False)}")
        
        db.session.commit()
        print("更新成功")
        
    except Exception as e:
        db.session.rollback()
        print(f"更新失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()