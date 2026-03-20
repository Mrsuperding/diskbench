# IO任务修复计划

## [x] 任务1：修复iostat日志解析失败问题
- **Priority**: P1
- **Depends On**: None
- **Description**:
  - 修复log_collector.py中缺少timedelta导入的问题
  - 确保iostat日志解析能够正常工作
- **Success Criteria**:
  - iostat日志解析不再出现"type object 'datetime.datetime' has no attribute 'timedelta'"错误
  - 能够成功解析iostat日志并提取性能指标
- **Test Requirements**:
  - `programmatic` TR-1.1: 运行包含iostat日志的任务，验证解析过程无错误
  - `human-judgement` TR-1.2: 检查日志输出，确认iostat指标被正确解析
- **Notes**: 在log_collector.py文件顶部添加from datetime import timedelta导入

## [x] 任务2：修复测试结果显示问题
- **Priority**: P1
- **Depends On**: None
- **Description**:
  - 检查后端如何存储多个IO模型的测试结果
  - 检查前端如何处理和显示测试结果
  - 确保所有IO模型的测试结果都能正确显示
- **Success Criteria**:
  - 测试结果页面能够显示所有IO模型的测试结果
  - 每个IO模型的详细数据都能正确展示
- **Test Requirements**:
  - `programmatic` TR-2.1: 创建包含多个IO模型的测试任务，验证所有模型的结果都能显示
  - `human-judgement` TR-2.2: 检查测试结果页面，确认所有IO模型的结果都已显示
- **Notes**: 需要检查后端的测试结果存储逻辑和前端的结果处理逻辑

## [x] 任务3：修复块大小和队列深度参数问题
- **Priority**: P1
- **Depends On**: None
- **Description**:
  - 检查ssh_client.py中处理block_size和queue_depth参数的逻辑
  - 修复参数拼接错误，确保块大小和队列深度被正确处理
- **Success Criteria**:
  - 块大小和队列深度参数被正确处理，不再出现44k和1616这样的错误值
  - fio命令能够正确执行
- **Test Requirements**:
  - `programmatic` TR-3.1: 运行包含多个块大小和队列深度的测试任务，验证参数被正确处理
  - `human-judgement` TR-3.2: 检查命令日志，确认fio命令中的参数值正确
- **Notes**: 需要检查参数处理和命令构建逻辑，确保正确处理多个值的情况

## [x] 任务4：验证所有修复
- **Priority**: P2
- **Depends On**: 任务1, 任务2, 任务3
- **Description**:
  - 运行完整的测试任务，验证所有修复是否生效
  - 检查前端和后端是否正常工作
- **Success Criteria**:
  - 测试任务能够正常执行
  - 所有IO模型的测试结果都能正确显示
  - 日志解析正常，无错误
- **Test Requirements**:
  - `programmatic` TR-4.1: 运行完整的测试任务，验证所有功能正常
  - `human-judgement` TR-4.2: 检查前端页面和后端日志，确认所有功能正常
- **Notes**: 确保所有修复都已正确实施并测试通过