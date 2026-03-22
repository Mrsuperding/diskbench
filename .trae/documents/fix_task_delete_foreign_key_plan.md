# Diskbench Pro2 - 任务删除外键约束修复计划

## [x] 任务1：分析外键约束错误
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 分析删除任务时的外键约束错误
  - 查看iostat_metrics表与test_logs表的外键关系
  - 理解当前删除逻辑的问题
- **Success Criteria**:
  - 明确外键约束错误的原因
  - 了解表之间的关联关系
- **Test Requirements**:
  - `programmatic` TR-1.1: 确认外键约束错误的具体原因
- **Notes**: 外键约束错误显示iostat_metrics表引用了test_logs表的记录

## [x] 任务2：修复删除逻辑，添加级联删除
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 修改delete_task函数，添加对iostat_metrics表的级联删除
  - 确保删除顺序正确，先删除子表记录，再删除父表记录
  - 测试修改后的删除功能
- **Success Criteria**:
  - 任务删除时不再出现外键约束错误
  - 删除操作正常返回200状态码
- **Test Requirements**:
  - `programmatic` TR-2.1: DELETE /api/tasks/{id} 返回200状态
  - `programmatic` TR-2.2: 数据库中任务及其关联数据被正确删除
- **Notes**: 确保删除顺序：iostat_metrics → test_logs → test_results → task_executions → 任务

## [x] 任务3：完整测试删除功能
- **Priority**: P1
- **Depends On**: 任务2
- **Description**:
  - 测试删除不同状态的任务
  - 测试删除包含执行记录的任务
  - 测试删除包含日志和结果的任务
- **Success Criteria**:
  - 所有类型的任务都能成功删除
  - 数据库中无残留数据
  - 前端UI删除操作无错误
- **Test Requirements**:
  - `human-judgement` TR-3.1: 前端UI删除任务流程无错误
  - `programmatic` TR-3.2: 不同类型任务的删除操作都返回200状态
- **Notes**: 确保测试覆盖各种场景

## [x] 任务4：重新进行完整UI验收测试
- **Priority**: P1
- **Depends On**: 任务3
- **Description**:
  - 使用账号dhq/123456进行完整的UI验收测试
  - 测试所有任务操作流程，重点测试删除功能
  - 确保所有功能都正常工作
- **Success Criteria**:
  - 所有任务操作（创建、克隆、修改、执行、删除）都能正常完成
  - 前端UI无错误提示
  - 后端API返回正确状态码
- **Test Requirements**:
  - `human-judgement` TR-4.1: 完整UI测试流程无错误
  - `programmatic` TR-4.2: 所有API调用返回成功状态码
- **Notes**: 确保测试覆盖所有可能的使用场景

## 总结

已成功修复任务删除时的外键约束错误，具体修复内容：

1. **分析了外键约束错误**：确认错误是由于iostat_metrics表引用了test_logs表的记录，导致删除test_logs记录时出现外键约束错误

2. **修复了删除逻辑**：
   - 添加了对iostat_metrics表的级联删除
   - 确保删除顺序正确：iostat_metrics → test_logs → test_results → task_executions → 任务
   - 使用synchronize_session=False参数避免删除时的会话同步问题

3. **测试了删除功能**：
   - 测试删除不同状态的任务
   - 测试删除包含执行记录的任务
   - 测试删除包含日志和结果的任务

4. **重新进行了完整UI验收测试**：
   - 使用账号dhq/123456进行了完整的UI验收测试
   - 测试了所有任务操作流程，重点测试了删除功能
   - 所有功能都能正常工作，前端UI无错误提示

现在任务删除功能已正常工作，不再出现外键约束错误，所有API调用都能返回正确的状态码。