#!/usr/bin/env python3
"""
测试IO模型命名生成和P99时延统计提取
"""

import re
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.log_collector import LogCollector


def test_io_model_naming():
    """测试IO模型命名生成是否按照指定格式"""
    print("=== 测试IO模型命名生成 ===")
    
    collector = LogCollector()
    
    # 测试用例
    test_cases = [
        # (node_count, vol_count, block_size, rw_type, queue_depth, thread_count, expected_pattern)
        (1, 1, '4k', 'randread', 16, 1, r'^1VM_1VOL_4k_randread_16d_1j$'),
        (2, 4, '8k', 'randwrite', 32, 2, r'^2VM_4VOL_8k_randwrite_32d_2j$'),
        (4, 8, '16k', 'read', 64, 4, r'^4VM_8VOL_16k_read_64d_4j$'),
        (8, 16, '32k', 'write', 128, 8, r'^8VM_16VOL_32k_write_128d_8j$'),
        (16, 32, '64k', 'randrw', 256, 16, r'^16VM_32VOL_64k_randrw_256d_16j$'),
    ]
    
    passed = 0
    failed = 0
    
    for i, (node_count, vol_count, block_size, rw_type, queue_depth, thread_count, expected_pattern) in enumerate(test_cases):
        result = collector.generate_io_model_name(node_count, vol_count, block_size, rw_type, queue_depth, thread_count)
        
        # 验证格式
        match = re.match(expected_pattern, result)
        
        if match:
            print(f"测试 {i+1}: 通过")
            print(f"  输入: {node_count}VM, {vol_count}VOL, {block_size}, {rw_type}, {queue_depth}d, {thread_count}j")
            print(f"  输出: {result}")
            print(f"  格式: 正确")
            passed += 1
        else:
            print(f"测试 {i+1}: 失败")
            print(f"  输入: {node_count}VM, {vol_count}VOL, {block_size}, {rw_type}, {queue_depth}d, {thread_count}j")
            print(f"  输出: {result}")
            print(f"  期望格式: {expected_pattern}")
            failed += 1
        print()
    
    print(f"=== 测试结果: 通过 {passed}, 失败 {failed} ===")
    return passed == len(test_cases)


def test_p99_latency_extraction():
    """测试P99时延统计是否正确提取"""
    print("=== 测试P99时延统计提取 ===")
    
    collector = LogCollector()
    
    # 模拟FIO日志内容
    test_log_content = """
diskbench_test: (g=0): rw=read, bs=(R) 4096B-4096B, (W) 4096B-4096B, (T) 4096B-4096B, ioengine=psync, iodepth=9
fio-3.36
Starting 1 process
note: both iodepth >= 1 and synchronous I/O engine are selected, queue depth will be capped at 1

diskbench_test: (groupid=0, jobs=1): err= 0: pid=878669: Tue Jan 27 21:42:00 2026
  read: IOPS=27.3k, BW=107MiB/s (112MB/s)(1024MiB/9613msec)
    clat (nsec): min=482, max=896090k, avg=36233.05, stdev=5280314.93
     lat (nsec): min=514, max=896090k, avg=36277.64, stdev=5280314.91
    clat percentiles (nsec):
     |  1.00th=[     604],  5.00th=[     620], 10.00th=[     636],
     | 20.00th=[     668], 30.00th=[     732], 40.00th=[     780],
     | 50.00th=[     836], 60.00th=[     900], 70.00th=[     972],
     | 80.00th=[    1064], 90.00th=[    1192], 95.00th=[    1336],
     | 99.00th=[    1720], 99.50th=[    2416], 99.90th=[   38144],
     | 99.95th=[ 2146304], 99.99th=[10158080]
   bw (  KiB/s): min=113336, max=221456, per=100.00%, avg=199749.60, stdev=31524.11, samples=10
   iops        : min=28334, max=55364, avg=49937.40, stdev=7881.03, samples=10
  lat (nsec)   : 500=0.01%, 750=33.63%, 1000=40.02%
  lat (usec)   : 2=25.72%, 4=0.21%, 10=0.16%, 20=0.12%, 50=0.05%
  lat (usec)   : 100=0.02%, 250=0.01%, 500=0.01%, 750=0.01%, 1000=0.01%
  lat (msec)   : 2=0.01%, 4=0.01%, 10=0.03%, 20=0.01%, 500=0.01%
  lat (msec)   : 1000=0.01%
  cpu          : usr=1.04%, sys=4.17%, ctx=322, majf=0, minf=14
  IO depths    : 1=100.0%, 2=0.0%, 4=0.0%, 8=0.0%, 16=0.0%, 32=0.0%, >=64=0.0%
     submit    : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
     complete  : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
     issued rwts: total=262144,0,0,0 short=0,0,0,0 dropped=0,0,0,0
     latency   : target=0, window=0, percentile=100.00%, depth=9

Run status group 0 (all jobs):
   READ: bw=107MiB/s (112MB/s), 107MiB/s-107MiB/s (112MB/s-112MB/s), io=1024MiB (1074MB), run=9613-9613msec

Disk stats (read/write):
  vdb: ios=3385/1, sectors=2049096/0, merge=1/0, ticks=487054/0, in_queue=487054, util=96.49%
"""
    
    # 临时写入测试日志文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(test_log_content)
        temp_log_path = f.name
    
    try:
        # 解析FIO日志
        metrics = collector._parse_fio_log(temp_log_path)
        
        print(f"解析结果: {metrics}")
        print()
        
        # 验证是否提取了P99延迟
        if metrics and metrics['jobs']:
            first_job = metrics['jobs'][0]
            lat_p99 = first_job.get('lat_p99', 0)
            
            print(f"提取的P99延迟: {lat_p99} ms")
            
            # 验证P99延迟值是否合理（应该大于0）
            if lat_p99 > 0:
                print("测试: 通过")
                print(f"  P99延迟值: {lat_p99} ms")
                return True
            else:
                print("测试: 失败")
                print(f"  P99延迟值不合理: {lat_p99} ms")
                return False
        else:
            print("测试: 失败")
            print("  解析结果为空")
            return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_log_path):
            os.unlink(temp_log_path)


def main():
    """运行所有测试"""
    print("开始测试IO模型命名和P99时延统计...")
    print()
    
    # 运行测试
    test1_passed = test_io_model_naming()
    print()
    test2_passed = test_p99_latency_extraction()
    print()
    
    # 汇总结果
    all_passed = test1_passed and test2_passed
    
    if all_passed:
        print("=== 所有测试通过! ===")
        return 0
    else:
        print("=== 部分测试失败! ===")
        return 1


if __name__ == '__main__':
    sys.exit(main())
