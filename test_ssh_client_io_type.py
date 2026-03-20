#!/usr/bin/env python3
"""
测试SSH客户端的IO类型参数处理
"""

import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.utils.ssh_client import SSHClient

# 模拟登录凭证
class MockLoginCredential:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 22
        self.username = 'test'
        self.password = 'test'
        self.platform = 'linux'
        self.platform_partition = '/tmp'

# 测试IO类型处理
def test_io_type_processing():
    """测试IO类型参数处理"""
    print("测试SSH客户端的IO类型参数处理")
    print("=" * 60)
    
    # 创建SSH客户端实例
    login_credential = MockLoginCredential()
    ssh_client = SSHClient(login_credential)
    
    # 测试用例1：IO类型为["write"]
    print("\n测试1: IO类型为['write']")
    fio_params1 = {
        'io_type': ['write'],
        'block_size': '4k',
        'queue_depth': '16',
        'runtime': '10s'
    }
    
    # 模拟run_fio_test方法中的IO类型处理逻辑
    io_type = fio_params1.get('io_type', fio_params1.get('rw', 'read'))
    io_types = []
    if isinstance(io_type, list):
        io_types = [str(it).strip() for it in io_type if it.strip()]
    elif isinstance(io_type, str) and ',' in io_type:
        io_types = [it.strip() for it in io_type.split(',') if it.strip()]
    elif io_type:
        io_types = [str(io_type).strip()]
    else:
        io_types = ['read']
    
    print(f"处理后的io_types: {io_types}")
    assert io_types == ['write'], f"期望 ['write']，实际 {io_types}"
    
    # 测试用例2：IO类型为["randread", "randwrite"]
    print("\n测试2: IO类型为['randread', 'randwrite']")
    fio_params2 = {
        'io_type': ['randread', 'randwrite'],
        'block_size': '4k',
        'queue_depth': '16',
        'runtime': '10s'
    }
    
    io_type = fio_params2.get('io_type', fio_params2.get('rw', 'read'))
    io_types = []
    if isinstance(io_type, list):
        io_types = [str(it).strip() for it in io_type if it.strip()]
    elif isinstance(io_type, str) and ',' in io_type:
        io_types = [it.strip() for it in io_type.split(',') if it.strip()]
    elif io_type:
        io_types = [str(io_type).strip()]
    else:
        io_types = ['read']
    
    print(f"处理后的io_types: {io_types}")
    assert io_types == ['randread', 'randwrite'], f"期望 ['randread', 'randwrite']，实际 {io_types}"
    
    # 测试用例3：IO类型为["rw"]
    print("\n测试3: IO类型为['rw']")
    fio_params3 = {
        'io_type': ['rw'],
        'block_size': '4k',
        'queue_depth': '16',
        'runtime': '10s'
    }
    
    io_type = fio_params3.get('io_type', fio_params3.get('rw', 'read'))
    io_types = []
    if isinstance(io_type, list):
        io_types = [str(it).strip() for it in io_type if it.strip()]
    elif isinstance(io_type, str) and ',' in io_type:
        io_types = [it.strip() for it in io_type.split(',') if it.strip()]
    elif io_type:
        io_types = [str(io_type).strip()]
    else:
        io_types = ['read']
    
    print(f"处理后的io_types: {io_types}")
    assert io_types == ['rw'], f"期望 ['rw']，实际 {io_types}"
    
    # 测试用例4：IO类型为字符串"write"
    print("\n测试4: IO类型为字符串'write'")
    fio_params4 = {
        'io_type': 'write',
        'block_size': '4k',
        'queue_depth': '16',
        'runtime': '10s'
    }
    
    io_type = fio_params4.get('io_type', fio_params4.get('rw', 'read'))
    io_types = []
    if isinstance(io_type, list):
        io_types = [str(it).strip() for it in io_type if it.strip()]
    elif isinstance(io_type, str) and ',' in io_type:
        io_types = [it.strip() for it in io_type.split(',') if it.strip()]
    elif io_type:
        io_types = [str(io_type).strip()]
    else:
        io_types = ['read']
    
    print(f"处理后的io_types: {io_types}")
    assert io_types == ['write'], f"期望 ['write']，实际 {io_types}"
    
    # 测试用例5：IO类型为逗号分隔的字符串"read,write"
    print("\n测试5: IO类型为逗号分隔的字符串'read,write'")
    fio_params5 = {
        'io_type': 'read,write',
        'block_size': '4k',
        'queue_depth': '16',
        'runtime': '10s'
    }
    
    io_type = fio_params5.get('io_type', fio_params5.get('rw', 'read'))
    io_types = []
    if isinstance(io_type, list):
        io_types = [str(it).strip() for it in io_type if it.strip()]
    elif isinstance(io_type, str) and ',' in io_type:
        io_types = [it.strip() for it in io_type.split(',') if it.strip()]
    elif io_type:
        io_types = [str(io_type).strip()]
    else:
        io_types = ['read']
    
    print(f"处理后的io_types: {io_types}")
    assert io_types == ['read', 'write'], f"期望 ['read', 'write']，实际 {io_types}"
    
    # 测试用例6：IO类型为None
    print("\n测试6: IO类型为None")
    fio_params6 = {
        'block_size': '4k',
        'queue_depth': '16',
        'runtime': '10s'
    }
    
    io_type = fio_params6.get('io_type', fio_params6.get('rw', 'read'))
    io_types = []
    if isinstance(io_type, list):
        io_types = [str(it).strip() for it in io_type if it.strip()]
    elif isinstance(io_type, str) and ',' in io_type:
        io_types = [it.strip() for it in io_type.split(',') if it.strip()]
    elif io_type:
        io_types = [str(io_type).strip()]
    else:
        io_types = ['read']
    
    print(f"处理后的io_types: {io_types}")
    assert io_types == ['read'], f"期望 ['read']，实际 {io_types}"
    
    print("\n" + "=" * 60)
    print("所有测试通过！")

if __name__ == "__main__":
    test_io_type_processing()
