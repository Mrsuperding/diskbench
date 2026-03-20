# 应用上下文错误修复计划

## [x] 任务1: 修复返回响应时的应用上下文错误
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 修改 tasks.py 文件中的 run_task 函数，确保在返回响应时使用已经获取的 execution_id，而不是再次访问 execution.id
  - 这样可以避免在应用上下文之外访问数据库对象
- **Success Criteria**:
  - 执行任务时不再出现 "Working outside of application context" 错误
  - 任务能够正常启动并在后台执行
- **Test Requirements**:
  - `programmatic` TR-1.1: 执行任务时返回 200 状态码，包含正确的 task_id 和 execution_id
  - `programmatic` TR-1.2: 任务能够在后台正常执行，不会因为应用上下文错误而失败
- **Notes**:
  - 确保在主线程中获取 execution_id 后，所有后续使用都使用这个变量，而不是再次访问 execution 对象

## [x] 任务2: 验证修复效果
- **Priority**: P1
- **Depends On**: 任务1
- **Description**:
  - 测试执行任务功能，确保不再出现应用上下文错误
  - 验证任务能够正常启动和执行
- **Success Criteria**:
  - 执行任务时不再出现 "Working outside of application context" 错误
  - 任务状态能够正确更新
  - 能够在后台线程中执行任务逻辑
- **Test Requirements**:
  - `programmatic` TR-2.1: 执行任务 API 调用返回 200 状态码
  - `programmatic` TR-2.2: 任务状态从 "pending" 变为 "running"
  - `human-judgement` TR-2.3: 日志中没有应用上下文错误
- **Notes**:
  - 测试时需要确保有可用的测试任务和节点

## [x] 任务3: 优化代码结构
- **Priority**: P2
- **Depends On**: 任务1
- **Description**:
  - 检查代码中是否还有其他可能导致应用上下文错误的地方
  - 确保所有数据库操作都在应用上下文中执行
- **Success Criteria**:
  - 代码结构清晰，避免在应用上下文之外访问数据库对象
  - 所有数据库操作都有适当的应用上下文保护
- **Test Requirements**:
  - `human-judgement` TR-3.1: 代码结构清晰，易于理解
  - `human-judgement` TR-3.2: 没有明显的应用上下文错误风险
- **Notes**:
  - 重点检查其他可能在后台线程中执行的函数
