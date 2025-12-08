# 创建一个临时脚本，直接在其中编写创建测试用例的代码

import sys
import os

# 将当前目录添加到Python路径
sys.path.append('.')

# 直接执行app.py文件中的代码，以便访问create_app函数
with open('app.py', 'r') as f:
    app_py_content = f.read()

exec(app_py_content)

# 现在我们可以使用app变量和db、IOTestCase等模型
from app.models import db, IOTestCase

with app.app_context():
    print('Checking for existing test cases...')
    test_cases = IOTestCase.query.all()
    print(f'Found {len(test_cases)} test cases')
    
    for case in test_cases:
        print(f'  ID: {case.id}, Name: {case.name}')
    
    if not test_cases:
        print('\nNo test cases found. Creating one...')
        new_case = IOTestCase(
            name='Test Case 1',
            description='A simple test case for multi-node testing',
            tool='fio',
            parameters={'rw': 'read', 'size': '1G', 'bs': '4k'},
            is_public=True,
            created_by=1
        )
        db.session.add(new_case)
        db.session.commit()
        print(f'Test case created successfully: ID={new_case.id}')
    else:
        print('\nUsing existing test case:', test_cases[0].id)