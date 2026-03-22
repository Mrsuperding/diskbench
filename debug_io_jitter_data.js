"""
诊断IO抖动图表数据问题的脚本
检查：
1. 数据库中IOSTAT指标是否有数据
2. 字段值是否为0
3. 前端聚合逻辑是否正确
"""

# 在浏览器console中运行此代码来诊断问题
console.log("=== IO抖动图表数据诊断 ===");

// 1. 检查原始metrics数据
console.log("1. 检查processIOJitterMetrics接收到的原始数据:");
console.log("在processIOJitterMetrics函数第一行添加:");
console.log("console.log('原始metrics:', JSON.stringify(metrics, null, 2));");

// 2. 检查设备数据
console.log("\n2. 检查deviceData结构:");
console.log("在processIOJitterMetrics函数结束前添加:");
console.log("console.log('deviceData:', JSON.stringify(deviceData, null, 2));");

// 3. 检查聚合后的数据
console.log("\n3. 检查updateAggregatedMetrics的输出:");
console.log("在updateAggregatedMetrics函数结束前添加:");
console.log("console.log('聚合后的iostatMetrics:', JSON.stringify({");
console.log("  readLatency: iostatMetrics.readLatency,");
console.log("  diskUtilization: iostatMetrics.diskUtilization,");
console.log("  queueLength: iostatMetrics.queueLength,");
console.log("  serviceTime: iostatMetrics.serviceTime");
console.log("}, null, 2));");

// 4. 检查后端API返回
console.log("\n4. 在Network标签中检查API响应:");
console.log("查找 /api/logs/{logId}/iostat-metrics");
console.log("检查返回的数据中 await_time, svctm, util 字段是否有值");

// 5. 常见问题检查清单
console.log("\n5. 问题检查清单:");
console.log("□ 后端数据库中iostat_metrics表是否有数据？");
console.log("□ await_time, svctm, util字段是否为NULL或0？");
console.log("□ 前端接收到的metrics数组是否有这些字段？");
console.log("□ Math.max()操作是否返回0？（可能所有值都是0）");
console.log("□ 时间戳对齐是否正确？");
