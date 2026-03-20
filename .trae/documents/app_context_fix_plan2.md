# 应用上下文错误修复计划（第二版）

## [x] 任务1: 修复 run_task_execution 函数中的应用上下文错误
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 修改 `run_task_execution` 函数，确保在 `except` 块中也能正确处理应用上下文
  - 将异常处理逻辑移到应用上下文内部，或者在 `except` 块中重新创建应用上下文
- **Success Criteria**:
  - 执行任务时不再出现 "Working outside of application context" 错误
  - 即使发生异常，也能正确更新任务状态
- **Test Requirements**:
  - `programmatic` TR-1.1: 执行任务时返回 200 状态码，包含正确的 task_id 和 execution_id
  - `programmatic` TR-1.2: 任务能够在后台正常执行，不会因为应用上下文错误而失败
  - `programmatic` TR-1.3: 即使发生异常，任务状态也能被正确更新为失败
- **Notes**:
  - 重点关注 `except` 块中的数据库操作，确保它们在应用上下文中执行

## [x] 任务2: 验证修复效果
- **Priority**: P1
- **Depends On**: 任务1
- **Description**:
  - 测试执行任务功能，确保不再出现应用上下文错误
  - 验证任务能够正常启动和执行
  - 测试异常情况下的错误处理
- **Success Criteria**:
  - 执行任务时不再出现 "Working outside of application context" 错误
  - 任务状态能够正确更新
  - 即使发生异常，任务状态也能被正确更新为失败
- **Test Requirements**:
  - `programmatic` TR-2.1: 执行任务 API 调用返回 200 状态码
  - `programmatic` TR-2.2: 任务状态从 "pending" 变为 "running"
  - `programmatic` TR-2.3: 即使发生异常，任务状态也能被更新为 "failed"
  - `human-judgement` TR-2.4: 日志中没有应用上下文错误
- **Notes**:
  - 测试时需要确保有可用的测试任务和节点
  - 可以通过模拟异常来测试错误处理逻辑

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
