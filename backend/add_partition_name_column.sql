-- 添加 partition_name 列到 system_metrics 表
-- 如果表不存在或已存在该列，请注释掉相应行

-- 添加 partition_name 列
ALTER TABLE system_metrics ADD COLUMN partition_name VARCHAR(255) NULL COMMENT '分区名称，用于分区级别指标';

-- 添加索引
CREATE INDEX idx_partition_name ON system_metrics (partition_name);
CREATE INDEX idx_node_partition_time ON system_metrics (node_id, partition_name, collection_time);
