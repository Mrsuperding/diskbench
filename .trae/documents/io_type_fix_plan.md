# IO类型参数处理修复计划

## 问题分析
- **问题**：IO测试用例的读写模式总是默认为'read'，即使前端设置了其他模式
- **原因**：后端代码没有正确处理前端发送的io_type数组格式
- **影响**：所有IO测试都以读模式执行，无法执行写或混合读写测试

## 修复内容
- **已修复**：在`backend/app/utils/ssh_client.py`中添加了对io_type数组格式的处理
- **修改点**：第329-342行，添加了对list类型io_type参数的支持

## 验证步骤

### [x] 步骤1：启动前后端服务
- **Priority**：P0
- **Description**：启动后端和前端服务，确保服务正常运行
- **Success Criteria**：前后端服务都成功启动，无错误
- **Test Requirements**：
  - `programmatic` TR-1.1：后端服务在端口5000正常运行
  - `programmatic` TR-1.2：前端服务在端口8080正常运行

### [x] 步骤2：创建包含不同IO类型的测试用例
- **Priority**：P0
- **Description**：在前端创建测试用例，设置不同的IO类型（读、写、随机读、随机写等）
- **Success Criteria**：测试用例创建成功，IO类型设置正确
- **Test Requirements**：
  - `human-judgement` TR-2.1：前端表单能正确选择并保存不同的IO类型
  - `programmatic` TR-2.2：后端数据库中保存的io_type参数与前端设置一致

### [x] 步骤3：执行测试任务
- **Priority**：P0
- **Description**：创建并执行包含不同IO类型测试用例的任务
- **Success Criteria**：任务执行成功，日志显示正确的IO类型
- **Test Requirements**：
  - `programmatic` TR-3.1：任务执行日志中显示正确的IO类型参数
  - `programmatic` TR-3.2：fio命令中包含正确的--rw参数

### [x] 步骤4：验证测试结果
- **Priority**：P1
- **Description**：查看测试结果，确认不同IO类型的测试都执行成功
- **Success Criteria**：测试结果中显示正确的IO类型执行情况
- **Test Requirements**：
  - `human-judgement` TR-4.1：测试结果页面显示正确的IO类型
  - `programmatic` TR-4.2：数据库中存储的测试结果包含正确的IO类型信息

## 预期结果
- 前端设置的IO类型（如write、randwrite等）能够正确传递到后端
- 后端能够正确处理io_type数组格式
- fio命令能够使用正确的--rw参数执行测试
- 测试结果能够正确显示执行的IO类型

## 风险评估
- **低风险**：修改仅影响IO类型参数的处理逻辑，不会影响其他功能
- **兼容性**：修改后仍然支持字符串格式的io_type参数，保持向后兼容

## 测试数据
- 测试用例1：IO类型为["write"]
- 测试用例2：IO类型为["randread", "randwrite"]
- 测试用例3：IO类型为["rw"]

## 完成标准
- 所有验证步骤都通过
- 不同IO类型的测试用例都能正确执行
- 测试结果显示正确的IO类型信息