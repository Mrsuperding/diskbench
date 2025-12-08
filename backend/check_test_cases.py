# 导入必要的模块
import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# 导入create_app函数和数据库模型
from app.py import create_app
from app.models import db, IOTestCase

# 创建应用实例
app = create_app()

with app.app_context():
    # Check if there are any test cases in the database
    print("Checking for existing test cases...")
    test_cases = IOTestCase.query.all()
    print(f"Found {len(test_cases)} test cases")
    
    for case in test_cases:
        print(f"  ID: {case.id}, Name: {case.name}, Description: {case.description}")
    
    if not test_cases:
        print("\nNo test cases found. Let's create one...")
        # Create a simple test case
        new_case = IOTestCase(
            name="Test Case 1",
            description="A simple test case for multi-node testing",
            tool="fio",
            parameters={"rw": "read", "size": "1G", "bs": "4k"},
            is_public=True,
            created_by=1
        )
        db.session.add(new_case)
        db.session.commit()
        print(f"Test case created successfully: ID={new_case.id}")