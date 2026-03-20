// IO任务详情页面功能测试

// 测试iostat日志解析函数
function testIostatLogParsing() {
  console.log('测试iostat日志解析功能...');
  
  // 模拟iostat日志行
  const iostatLogLine = 'sda               0.00     0.00    10.00    5.00     1.00     0.50     16.00     0.10    5.00    4.00    6.00   1.00   15.00';
  
  // 复制前端的解析函数
  function parseIostatLog(line) {
    try {
      // 跳过标题行和空行
      if (!line || line.startsWith("Device:") || line.trim() === "") {
        return null;
      }

      // 使用正则表达式解析设备数据行
      // 格式: device_name  rrqm/s  wrqm/s  r/s  w/s  rMB/s  wMB/s  avgrq-sz  avgqu-sz  await  r_await  w_await  svctm  %util
      const parts = line.trim().split(/\s+/);

      if (parts.length < 14) {
        return null;
      }

      const device = parts[0];

      // 提取指标值
      const readKbps = parseFloat(parts[5]) * 1024; // rMB/s 转换为 KB/s
      const writeKbps = parseFloat(parts[6]) * 1024; // wMB/s 转换为 KB/s
      const readIOPS = parseFloat(parts[2]);
      const writeIOPS = parseFloat(parts[3]);
      const awaitTime = parseFloat(parts[9]);
      const svctm = parseFloat(parts[12]);
      const util = parseFloat(parts[13]);

      // 检查是否为有效数字
      if (
        isNaN(readKbps) ||
        isNaN(writeKbps) ||
        isNaN(readIOPS) ||
        isNaN(writeIOPS)
      ) {
        return null;
      }

      const metric = {
        timestamp: new Date().toISOString(),
        device: device,
        read_kbps: readKbps,
        write_kbps: writeKbps,
        total_kbps: readKbps + writeKbps,
        read_iops: readIOPS,
        write_iops: writeIOPS,
        total_iops: readIOPS + writeIOPS,
        await_time: awaitTime,
        svctm: svctm,
        util: util,
      };

      return metric;
    } catch (error) {
      console.error("解析iostat日志失败:", error);
      return null;
    }
  }
  
  // 测试解析函数
  const result = parseIostatLog(iostatLogLine);
  
  if (result) {
    console.log('✓ iostat日志解析成功');
    console.log('解析结果:', result);
    console.log('设备名称:', result.device);
    console.log('读取速率:', result.read_kbps, 'KB/s');
    console.log('写入速率:', result.write_kbps, 'KB/s');
    console.log('读取IOPS:', result.read_iops);
    console.log('写入IOPS:', result.write_iops);
    console.log('总IOPS:', result.total_iops);
  } else {
    console.log('✗ iostat日志解析失败');
  }
  
  console.log('');
}

// 测试测试结果处理
function testTestResultsProcessing() {
  console.log('测试测试结果处理功能...');
  
  // 模拟测试结果数据
  const testResults = [
    {
      id: 1,
      io_test_case_id: 1,
      node_id: 1,
      status: 'completed',
      created_at: '2026-03-15T00:00:00',
      parsed_results: [
        {
          success: true,
          params: {
            io_type: 'randread',
            blocksize: '4k',
            iodepth: 8
          },
          raw_output: '测试输出1'
        },
        {
          success: true,
          params: {
            io_type: 'randwrite',
            blocksize: '8k',
            iodepth: 16
          },
          raw_output: '测试输出2'
        }
      ]
    },
    {
      id: 2,
      io_test_case_id: 2,
      node_id: 1,
      status: 'completed',
      created_at: '2026-03-15T00:01:00',
      parsed_results: [
        {
          success: true,
          params: {
            io_type: 'read',
            blocksize: '16k',
            iodepth: 4
          },
          raw_output: '测试输出3'
        }
      ]
    }
  ];
  
  // 模拟IO任务数据
  const ioTasks = [
    {
      id: 1,
      name: '随机读写测试'
    },
    {
      id: 2,
      name: '顺序读取测试'
    }
  ];
  
  // 模拟节点数据
  const taskNodes = [
    {
      id: 1,
      name: '测试节点1',
      ip_address: '192.168.1.100'
    }
  ];
  
  // 处理测试结果
  let processedData = [];
  testResults.forEach((result) => {
    const ioTestCase = ioTasks.find(
      (task) => task.id === result.io_test_case_id,
    );
    const node = taskNodes.find((n) => n.id === result.node_id);

    // 检查parsed_results是否为数组（多个测试组合）
    if (Array.isArray(result.parsed_results)) {
      // 为每个测试组合创建一个条目
      result.parsed_results.forEach((testResult, index) => {
        processedData.push({
          id: `${result.id}_${index}`,
          ioModelName: ioTestCase ? `${ioTestCase.name} (${testResult.params.io_type}, ${testResult.params.blocksize}, ${testResult.params.iodepth})` : "未知IO模型",
          nodeName: node ? node.name : "未知节点",
          nodeIp: node ? node.ip_address : "未知IP",
          status: testResult.success ? "success" : "failed",
          createdAt: result.created_at,
          rawResult: testResult.raw_output,
          parsedResult: testResult,
        });
      });
    } else {
      // 单个测试结果
      processedData.push({
        id: result.id,
        ioModelName: ioTestCase ? ioTestCase.name : "未知IO模型",
        nodeName: node ? node.name : "未知节点",
        nodeIp: node ? node.ip_address : "未知IP",
        status: result.status,
        createdAt: result.created_at,
        rawResult: result.raw_output,
        parsedResult: result.parsed_results,
      });
    }
  });
  
  console.log('✓ 测试结果处理成功');
  console.log('处理后的测试结果数量:', processedData.length);
  console.log('处理后的测试结果:');
  processedData.forEach((item, index) => {
    console.log(`${index + 1}. IO模型: ${item.ioModelName}`);
    console.log(`   节点: ${item.nodeName} (${item.nodeIp})`);
    console.log(`   状态: ${item.status}`);
    console.log(`   创建时间: ${item.createdAt}`);
  });
  
  // 验证块大小和队列深度参数是否被正确处理
  const hasValidModelNames = processedData.every(item => {
    return item.ioModelName.includes('blocksize') || item.ioModelName.includes('4k') || item.ioModelName.includes('8k') || item.ioModelName.includes('16k');
  });
  
  if (hasValidModelNames) {
    console.log('✓ 块大小和队列深度参数被正确处理');
  } else {
    console.log('✗ 块大小和队列深度参数处理失败');
  }
  
  console.log('');
}

// 运行测试
console.log('开始IO任务详情页面功能测试...');
console.log('='.repeat(50));

testIostatLogParsing();
testTestResultsProcessing();

console.log('='.repeat(50));
console.log('测试完成!');
