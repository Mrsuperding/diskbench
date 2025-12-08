import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 从app.py导入app实例和db
from app import app, db
from app.models.test_task import TestTask
from app.models.io_test_case import IOTestCase
from app.models.node import Node

with app.app_context():
    # 查询任务ID=1的信息
    task = TestTask.query.get(1)
    if task:
        print(f"任务ID: {task.id}")
        print(f"任务名称: {task.name}")
        print(f"任务状态: {task.status}")
        print(f"创建者: {task.created_by}")
        
        # 查询任务关联的测试用例
        from app.models.test_task import task_case_association
        test_case_ids = db.session.query(task_case_association.c.io_test_case_id).filter_by(test_task_id=1).all()
        test_case_ids = [case_id[0] for case_id in test_case_ids]
        print(f"关联的测试用例ID: {test_case_ids}")
        
        # 查询任务关联的节点
        from app.models.test_task import task_node_association
        node_ids = db.session.query(task_node_association.c.node_id).filter_by(test_task_id=1).all()
        node_ids = [node_id[0] for node_id in node_ids]
        print(f"关联的节点ID: {node_ids}")
        
        # 查询所有可用的测试用例
        all_test_cases = IOTestCase.query.all()
        print(f"所有可用的测试用例: {[case.id for case in all_test_cases]}")
        
        # 查询所有可用的节点
        all_nodes = Node.query.all()
        print(f"所有可用的节点: {[node.id for node in all_nodes]}")
    else:
        print("任务ID=1不存在")