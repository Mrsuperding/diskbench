# 并发作业数量支持多个值 - 实现计划

## [ ] 任务1：修改generateModelList方法，使numjobs支持多个值
- **优先级**：P0
- **依赖**：无
- **描述**：
  - 修改generateModelList方法，将numjobs处理逻辑改为支持多个值
  - 与块大小和队列深度的处理逻辑保持一致
  - 当numjobs输入多个值时，生成对应的多个测试模型
- **验收标准**：AC-1, AC-2, AC-3
- **测试要求**：
  - `human-judgment` TR-1.1：验证输入"1,2"时生成两个模型
  - `human-judgment` TR-1.2：验证模型名称包含正确的numjobs值
  - `human-judgment` TR-1.3：验证与其他参数的组合逻辑正确
- **备注**：需要确保numjobs的默认值为"1"