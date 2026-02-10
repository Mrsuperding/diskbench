import re

# 模拟FIO日志内容
content = """
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

# 测试正则表达式
job_sections = re.findall(r'diskbench_test: \(groupid=0, jobs=1\):.*?Run status group 0 \(all jobs\):', content, re.DOTALL)
print(f"找到 {len(job_sections)} 个作业部分")

for i, job_section in enumerate(job_sections):
    print(f"\n作业 {i+1}:")
    
    # 提取读写类型
    rw_type_match = re.search(r'rw=(read|write|randread|randwrite|randrw|rw)', job_section)
    rw_type = rw_type_match.group(1) if rw_type_match else 'unknown'
    print(f"  读写类型: {rw_type}")
    
    # 提取读性能指标
    read_match = re.search(r'  read: IOPS=(.*?), BW=(.*?)\(.*?\)', job_section)
    if read_match:
        print(f"  读IOPS: {read_match.group(1).strip()}")
        print(f"  读带宽: {read_match.group(2).strip()}")
    
    # 提取写性能指标
    write_match = re.search(r'  write: IOPS=(.*?), BW=(.*?)\(.*?\)', job_section)
    if write_match:
        print(f"  写IOPS: {write_match.group(1).strip()}")
        print(f"  写带宽: {write_match.group(2).strip()}")
    
    # 提取延迟指标
    lat_match = re.search(r'clat \(nsec\):.*?avg=(.*?),', job_section)
    if lat_match:
        print(f"  平均延迟: {lat_match.group(1).strip()}")

# 测试设备名称提取
device_match = re.search(r'Disk stats \(read/write\):\s*\n\s*(\w+):', content)
if device_match:
    print(f"\n提取到的设备名称: {device_match.group(1)}")
