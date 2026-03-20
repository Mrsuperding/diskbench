# 模型名称格式改进 - 实现计划

## [x] 任务1：修改generateModelList方法，添加numjobs支持
- **优先级**：P0
- **依赖**：无
- **描述**：
  - 从parameters中获取numjobs的值
  - 在生成模型名称时包含numjobs
  - 按照要求添加后缀：块大小后面加"k"，队列深度后面加"d"，并发数后面加"n"
- **成功标准**：
  - 模型名称格式为：blockSize+k_queueDepth+d_ioType_numjobs+n
  - 例如：4k_16d_randread_1n
- **测试要求**：
  - `human-judgment` TR-1.1：验证模型名称包含numjobs
  - `human-judgment` TR-1.2：验证模型名称格式正确，包含所有后缀
- **备注**：需要确保numjobs的默认值为1