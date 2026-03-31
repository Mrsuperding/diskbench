-- 添加partition_mode字段到io_test_cases表
ALTER TABLE io_test_cases
ADD COLUMN partition_mode ENUM('concurrent', 'sequential') DEFAULT 'concurrent'
COMMENT '分区执行模式：concurrent并发，sequential串行'
AFTER parameters;
