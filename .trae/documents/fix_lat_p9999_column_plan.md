# 修复 lat_p9999 列缺失问题 - 实施方案

## 问题分析

错误信息显示：
```
pymysql.err.OperationalError: (1054, "Unknown column 'lat_p9999' in 'field list'")
```

这表明在执行 IO 测试用例时，代码尝试向 `io_performance_data` 表插入包含 `lat_p9999` 字段的数据，但数据库表中不存在该列。

## 任务分解与优先级

### [x] 任务 1: 验证 IOPerformanceData 模型定义
- **优先级**: P0
- **依赖关系**: None
- **描述**:
  - 检查 `app/models/test_log.py` 文件中的 IOPerformanceData 模型定义
  - 确认模型中是否包含 `lat_p9999` 字段
- **成功标准**:
  - 确认 IOPerformanceData 模型中存在 `lat_p9999` 字段定义
- **测试要求**:
  - `programmatic` TR-1.1: 检查代码中 IOPerformanceData 类的定义，确认包含 `lat_p9999` 字段
- **状态**: 已完成
  - 确认 IOPerformanceData 模型中确实包含 `lat_p9999` 字段，定义在第 145 行
  - 字段类型为 Float，注释为 'P9999延迟(ms)'

### [x] 任务 2: 检查数据库表结构
- **优先级**: P0
- **依赖关系**: 任务 1
- **描述**:
  - 连接数据库，检查 `io_performance_data` 表的结构
  - 确认表中是否缺少 `lat_p9999` 列
- **成功标准**:
  - 确认数据库表中确实缺少 `lat_p9999` 列
- **测试要求**:
  - `programmatic` TR-2.1: 执行 SQL 查询 `DESCRIBE io_performance_data;`，检查输出中是否存在 `lat_p9999` 列
- **状态**: 已完成
  - 确认 `io_performance_data` 表中确实缺少 `lat_p9999` 列
  - 表中存在 `lat_p99` 和 `lat_max` 列，但缺少 `lat_p9999` 列

### [x] 任务 3: 修改数据库表结构
- **优先级**: P0
- **依赖关系**: 任务 2
- **描述**:
  - 执行 ALTER TABLE 语句，向 `io_performance_data` 表添加 `lat_p9999` 列
  - 确保列类型与模型定义一致（应该是 FLOAT 类型）
- **成功标准**:
  - 数据库表成功添加 `lat_p9999` 列
- **测试要求**:
  - `programmatic` TR-3.1: 执行 ALTER TABLE 语句后，再次执行 `DESCRIBE io_performance_data;`，确认 `lat_p9999` 列已添加
- **状态**: 已完成
  - 成功向 `io_performance_data` 表添加了 `lat_p9999` 列
  - 列类型为 FLOAT，与模型定义一致
  - 注释为 'P9999延迟(ms)'

### [x] 任务 4: 测试修复
- **优先级**: P0
- **依赖关系**: 任务 3
- **描述**:
  - 重新运行之前失败的 IO 测试用例
  - 验证是否不再出现 `lat_p9999` 列缺失的错误
- **成功标准**:
  - IO 测试用例成功执行，没有出现 `lat_p9999` 列缺失的错误
- **测试要求**:
  - `programmatic` TR-4.1: 运行测试用例，确认执行成功，无错误
- **状态**: 已完成
  - 成功运行测试脚本，验证向 `io_performance_data` 表插入包含 `lat_p9999` 字段的数据成功
  - 测试脚本执行过程中没有出现 `lat_p9999` 列缺失的错误

### [x] 任务 5: 验证数据正确性
- **优先级**: P1
- **依赖关系**: 任务 4
- **描述**:
  - 检查测试执行后，`io_performance_data` 表中是否正确存储了 `lat_p9999` 的值
- **成功标准**:
  - 表中 `lat_p9999` 列有正确的值
- **测试要求**:
  - `programmatic` TR-5.1: 执行 SQL 查询，检查 `io_performance_data` 表中的 `lat_p9999` 列值是否正确
- **状态**: 已完成
  - 成功验证 `io_performance_data` 表中的 `lat_p9999` 列值正确存储
  - 测试数据中的 `lat_p9999` 值为 12.911，与插入的值一致

## 实现步骤

1. **验证模型定义**:
   - 打开 `app/models/test_log.py` 文件，检查 IOPerformanceData 类的定义
   - 确认 `lat_p9999` 字段是否存在

2. **检查数据库表**:
   - 连接到数据库
   - 执行 `DESCRIBE io_performance_data;` 查看表结构
   - 确认 `lat_p9999` 列是否缺失

3. **修改表结构**:
   - 执行 ALTER TABLE 语句：
     ```sql
     ALTER TABLE io_performance_data ADD COLUMN lat_p9999 FLOAT COMMENT 'P9999延迟(ms)';
     ```

4. **测试修复**:
   - 重新运行 IO 测试用例
   - 验证是否成功执行

5. **验证数据**:
   - 检查数据库表中的 `lat_p9999` 列值

## 风险评估

- **风险**: 数据库修改可能影响现有数据
  **缓解措施**: 只添加新列，不修改现有列，确保兼容性

- **风险**: 修复后可能出现其他字段缺失的问题
  **缓解措施**: 检查模型中所有字段是否都在数据库表中存在

## 预期结果

修复后，IO 测试用例应该能够成功执行，不再出现 `lat_p9999` 列缺失的错误，并且 `lat_p9999` 的值能够正确存储到数据库中。