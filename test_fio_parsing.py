#!/usr/bin/env python3
import re

# 测试用的 FIO 输出
raw_output = '''diskbench_test: (g=0): rw=randread, bs=(R) 4096B-4096B, (W) 4096B-4096B, (T) 4096B-4096B, ioengine=psync, iodepth=4
fio-3.36
Starting 1 process
note: both iodepth >= 1 and synchronous I/O engine are selected, queue depth will be capped at 1

diskbench_test: (groupid=0, jobs=1): err= 0: pid=3536875: Wed Mar 18 01:01:37 2026
  read: IOPS=1959, BW=7838KiB/s (8026kB/s)(230MiB/30001msec)
    clat (usec): min=76, max=28600, avg=508.70, stdev=1548.78
     lat (usec): min=76, max=28600, avg=508.85, stdev=1548.77
    clat percentiles (usec):
     |  1.00th=[   89],  5.00th=[   91], 10.00th=[   93], 20.00th=[   95],
     | 30.00th=[  104], 40.00th=[  113], 50.00th=[  117], 60.00th=[  126],
     | 70.00th=[  139], 80.00th=[  159], 90.00th=[  277], 95.00th=[ 3818],
     | 99.00th=[ 7963], 99.50th=[ 8586], 99.90th=[ 8979], 99.95th=[ 9110],
     | 99.99th=[10421]
   bw (  KiB/s): min= 7600, max=17192, per=100.00%, avg=7847.46, stdev=1237.96, samples=59
   iops        : min= 1900, max= 4298, avg=1961.86, stdev=309.49, samples=59
  lat (usec)   : 100=26.82%, 250=62.73%, 500=3.86%, 750=0.13%, 1000=0.03%
  lat (msec)   : 2=0.04%, 4=2.20%, 10=4.17%, 20=0.01%, 50=0.01%
  cpu          : usr=0.64%, sys=1.74%, ctx=117583, majf=0, minf=10
  IO depths    : 1=100.0%, 2=0.0%, 4=0.0%, 8=0.0%, 16=0.0%, 32=0.0%, >=64=0.0%
     submit    : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
     complete  : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
     issued rwts: total=58784,0,0,0 short=0,0,0,0 dropped=0,0,0,0
     latency   : target=0, window=0, percentile=100.00%, depth=4

Run status group 0 (all jobs):
   READ: bw=7838KiB/s (8026kB/s), 7838KiB/s-7838KiB/s (8026kB/s-8026kB/s), io=230MiB (241MB), run=30001-30001msec

Disk stats (read/write):
  vdb: ios=58588/1, sectors=468704/0, merge=0/0, ticks=29147/0, in_queue=29147, util=99.72%'''

# 测试解析函数
def test_fio_parsing():
    print("开始测试 FIO 输出解析...")
    print("=" * 60)
    
    # 解析读取IOPS
    read_iops_match = re.search(r'^\s*read:\s*IOPS=([\d.]+)', raw_output, re.IGNORECASE | re.MULTILINE)
    read_iops = float(read_iops_match.group(1)) if read_iops_match else 0
    print(f"读取 IOPS: {read_iops}")
    assert read_iops == 1959, f"读取 IOPS 解析错误: {read_iops}"
    
    # 解析写入IOPS
    write_iops_match = re.search(r'^\s*write:\s*IOPS=([\d.]+)', raw_output, re.IGNORECASE | re.MULTILINE)
    write_iops = float(write_iops_match.group(1)) if write_iops_match else 0
    print(f"写入 IOPS: {write_iops}")
    assert write_iops == 0, f"写入 IOPS 解析错误: {write_iops}"
    
    # 解析读取带宽
    read_bw_match = re.search(r'^\s*read:.*BW=([\d.]+)(K|M)i?B/s', raw_output, re.IGNORECASE | re.MULTILINE)
    if read_bw_match:
        read_bw_value = float(read_bw_match.group(1))
        unit = read_bw_match.group(2)
        if unit == 'M':
            read_kbps = read_bw_value * 1024
        else:
            read_kbps = read_bw_value
    else:
        read_kbps = 0
    print(f"读取带宽 (Kbps): {read_kbps}")
    assert read_kbps == 7838, f"读取带宽解析错误: {read_kbps}"
    
    # 解析写入带宽
    write_bw_match = re.search(r'^\s*write:.*BW=([\d.]+)(K|M)i?B/s', raw_output, re.IGNORECASE | re.MULTILINE)
    if write_bw_match:
        write_bw_value = float(write_bw_match.group(1))
        unit = write_bw_match.group(2)
        if unit == 'M':
            write_kbps = write_bw_value * 1024
        else:
            write_kbps = write_bw_value
    else:
        write_kbps = 0
    print(f"写入带宽 (Kbps): {write_kbps}")
    assert write_kbps == 0, f"写入带宽解析错误: {write_kbps}"
    
    # 解析延迟
    lat_match = re.search(r'^\s*lat \(usec\):.*avg=([\d.]+)', raw_output, re.MULTILINE)
    if lat_match:
        await_time = float(lat_match.group(1)) / 1000
    else:
        await_time = 0
    print(f"平均延迟 (ms): {await_time}")
    assert abs(await_time - 0.50885) < 0.0001, f"平均延迟解析错误: {await_time}"
    
    # 解析p99延迟
    lat_p99_match = re.search(r'99\.00th=\[\s*([\d.]+)\]', raw_output, re.DOTALL)
    if lat_p99_match:
        lat_p99 = float(lat_p99_match.group(1)) / 1000
    else:
        lat_p99 = 0
    print(f"P99 延迟 (ms): {lat_p99}")
    assert abs(lat_p99 - 7.963) < 0.0001, f"P99 延迟解析错误: {lat_p99}"
    
    # 解析最大延迟
    lat_max_match = re.search(r'^\s*lat \(usec\):.*max=([\d.]+)', raw_output, re.MULTILINE)
    if lat_max_match:
        lat_max = float(lat_max_match.group(1)) / 1000
    else:
        lat_max = 0
    print(f"最大延迟 (ms): {lat_max}")
    assert abs(lat_max - 28.6) < 0.0001, f"最大延迟解析错误: {lat_max}"
    
    print("=" * 60)
    print("所有测试通过！FIO 输出解析正常。")

if __name__ == "__main__":
    test_fio_parsing()
