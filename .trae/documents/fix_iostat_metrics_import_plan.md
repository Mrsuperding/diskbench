# Diskbench Pro2 - IostatMetrics导入错误修复计划

## [x] 任务1：检查IostatMetrics模型文件
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 检查是否存在IostatMetrics模型文件
  - 确认文件路径和文件名
  - 验证模型定义是否正确
- **Success Criteria**:
  - 找到IostatMetrics模型文件
  - 确认模型定义正确
- **Test Requirements**:
  - `programmatic` TR-1.1: 确认IostatMetrics模型文件存在
- **Notes**: 检查backend/app/models目录下的文件

## [x] 任务2：检查models包的__init__.py文件
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 检查backend/app/models/__init__.py文件
  - 确认是否正确导入了IostatMetrics
  - 如果没有导入，添加相应的导入语句
- **Success Criteria**:
  - __init__.py文件中正确导入了IostatMetrics
- **Test Requirements**:
  - `programmatic` TR-2.1: 确认__init__.py文件中包含IostatMetrics的导入
- **Notes**: 确保导入语句格式正确

## [x] 任务3：修复删除任务的导入语句
- **Priority**: P0
- **Depends On**: 任务2
- **Description**:
  - 修改tasks.py文件中的IostatMetrics导入语句
  - 确保导入路径正确
  - 测试修改后的删除功能
- **Success Criteria**:
  - 删除任务时不再出现导入错误
  - 删除操作正常返回200状态码
- **Test Requirements**:
  - `programmatic` TR-3.1: DELETE /api/tasks/{id} 返回200状态
  - `programmatic` TR-3.2: 无导入错误
- **Notes**: 确保导入语句与实际文件结构匹配

## [x] 任务4：测试删除功能
- **Priority**: P1
- **Depends On**: 任务3
- **Description**:
  - 测试删除不同状态的任务
  - 测试删除包含执行记录的任务
  - 测试删除包含日志和结果的任务
- **Success Criteria**:
  - 所有类型的任务都能成功删除
  - 数据库中无残留数据
  - 前端UI删除操作无错误
- **Test Requirements**:
  - `human-judgement` TR-4.1: 前端UI删除任务流程无错误
  - `programmatic` TR-4.2: 不同类型任务的删除操作都返回200状态
- **Notes**: 确保测试覆盖各种场景

## 总结

已成功修复IostatMetrics导入错误，具体修复内容：

1. **找到并确认了模型文件**：IOStatMetric模型在test_log.py文件中定义，而不是IostatMetrics（注意大小写不同）

2. **检查了models包的__init__.py文件**：确认IOStatMetric已正确导入到models包中

3. **修复了删除任务的导入语句**：
   - 将tasks.py文件中的`from app.models import IostatMetrics`修改为`from app.models import IOStatMetric`
   - 确保导入语句与实际模型名称匹配

4. **测试了删除功能**：
   - 重新启动了后端服务
   - 测试了删除不同状态的任务
   - 确认删除操作正常返回200状态码
   - 前端UI删除操作无错误

现在任务删除功能已正常工作，不再出现导入错误，所有API调用都能返回正确的状态码。