## 问题分析
用户指出当前获取iostat指标的接口是根据开始时间和结束时间来获取的，但实际上详细数据是根据fio的运行结果文件来的，性能抖动图是根据iostat来绘制的。

## 解决方案
1. **修改性能指标获取方式**：不再基于iostat时间范围，而是直接通过FIO运行生成的JSON日志文件获取性能指标，包括带宽、IOPS、读写时延、p99指标、最大时延指标
2. **建立FIO日志与JSON日志的关联**：确保每个FIO运行都有对应的JSON日志文件，FIO运行完成后会生成一个JSON格式的结果文件
3. **修改相关API接口**：
   - 更新`get_iostat_metrics`接口，支持通过FIO日志ID获取对应的各类性能指标
   - 修改`get_performance_jitter`方法，使其通过FIO日志ID获取各类性能指标
4. **更新前端调用逻辑**：确保前端正确传递FIO日志ID来获取FIO性能指标

## 实施步骤
1. **修改FIO日志处理逻辑**：
   - 在`log_collector.py`中添加解析FIO JSON日志的方法
   - 确保FIO运行完成后生成的JSON日志被正确收集和关联

2. **更新后端API**：
   - 修改`app/views/logs.py`中的`get_iostat_metrics`接口，支持通过FIO日志ID获取性能指标
   - 更新`log_collector.py`中的`get_performance_jitter`方法
   - 添加新的方法来解析FIO JSON日志并提取所需指标

3. **更新数据模型**：
   - 在TestLog模型中添加字段，关联对应的FIO JSON日志文件

4. **更新前端代码**：
   - 修改前端调用逻辑，确保传递正确的FIO日志ID
   - 更新详细数据表格，显示从FIO JSON日志中提取的指标

5. **测试验证**：
   - 确保详细数据能正确显示FIO JSON日志中的性能指标
   - 确保性能抖动图仍能正常绘制

## 关键修改点
1. **后端代码**：
   - `app/utils/log_collector.py`：添加解析FIO JSON日志的方法
   - `app/views/logs.py`：更新API接口，支持通过FIO日志ID获取性能指标
   - `app/models/test_log.py`：添加关联字段

2. **前端代码**：
   - 更新调用API的参数，传递FIO日志ID
   - 确保数据表格能正确显示从JSON日志中提取的指标

## 预期效果
1. 详细数据表格显示FIO运行生成的JSON日志中的性能指标
2. 性能抖动图仍基于iostat日志绘制
3. API接口统一通过FIO日志ID获取性能数据
4. 支持获取关键性能指标：带宽、IOPS、读写时延、p99指标、最大时延指标