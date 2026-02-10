# 测试延迟数据提取修复
import sys
import os
import json

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 直接导入LogCollector类
from app.utils.log_collector import LogCollector

# 创建LogCollector实例
log_collector = LogCollector()

print("测试延迟数据提取修复")
print("=" * 50)

# 测试1: 测试convert_lat函数（需要从LogCollector类中提取）
print("\n1. 测试延迟转换逻辑:")

# 定义convert_lat函数（复制自LogCollector类）
def convert_lat(lat_str):
    try:
        lat_val = float(lat_str.strip())
        if lat_val < 0.1:
            # 如果值小于0.1，很可能是秒级，转换为毫秒
            return lat_val * 1000
        elif lat_val < 1000:
            # 如果值在0.1-1000之间，直接返回（已经是毫秒）
            return lat_val
        elif lat_val < 1000000:
            # 如果值在1000-1000000之间，可能是微秒，转换为毫秒
            return lat_val / 1000
        else:
            # 否则是纳秒，转换为毫秒
            return lat_val / 1000000
    except:
        return 0.0

# 测试convert_lat函数
test_values = [
    "0.001688",  # 秒
    "1.688",     # 毫秒
    "1688",      # 微秒
    "1688000",   # 纳秒
    "0",         # 零值
    ""           # 空值
]

for val in test_values:
    result = convert_lat(val)
    print(f"  {val} -> {result} ms")

# 测试2: 测试_parse_fio_log方法（模拟FIO日志内容）
print("\n2. 测试_parse_fio_log方法:")

# 创建一个模拟的FIO日志内容（完全匹配正则表达式格式）
mock_fio_log = """
diskbench_test: (groupid=0, jobs=1): err= 0: pid=1234:
  read: IOPS=1000, BW=4000KB/s (4.0MB/s)
  write: IOPS=500, BW=2000KB/s (2.0MB/s)
clat (nsec):
  avg=1688, max=10000,
clat percentiles (nsec):
  99.00th=[1688]
rw=randread
Run status group 0 (all jobs):
   READ: bw=4000KB/s (4.0MB/s)
   WRITE: bw=2000KB/s (2.0MB/s)
"""

# 写入临时文件
temp_log_path = "temp_fio_test.log"
with open(temp_log_path, 'w') as f:
    f.write(mock_fio_log)

try:
    # 解析日志
    result = log_collector._parse_fio_log(temp_log_path)
    print(f"  解析结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 检查是否提取了lat_p99和lat_max
    if result and 'jobs' in result:
        for job in result['jobs']:
            print(f"  作业延迟: 平均={job.get('lat', 0)}ms, p99={job.get('lat_p99', 0)}ms, 最大={job.get('lat_max', 0)}ms")
            
finally:
    # 清理临时文件
    if os.path.exists(temp_log_path):
        os.remove(temp_log_path)

print("\n测试完成！")
print("=" * 50)
