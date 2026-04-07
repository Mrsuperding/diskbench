-- DiskBench Pro 数据库表结构
-- 基于 backend/app/models 中的 SQLAlchemy 模型生成

-- ============================================
-- 1. 用户表
-- ============================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) NOT NULL COMMENT '用户名',
    email VARCHAR(100) NOT NULL COMMENT '邮箱地址',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    role ENUM('admin', 'user') DEFAULT 'user' COMMENT '用户角色',
    status ENUM('active', 'inactive', 'locked') DEFAULT 'active' COMMENT '账户状态',
    avatar_url VARCHAR(500) COMMENT '头像URL',
    last_login_at DATETIME COMMENT '最后登录时间',
    login_count INT DEFAULT 0 COMMENT '登录次数',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY ix_username (username),
    UNIQUE KEY ix_email (email),
    INDEX idx_role_status (role, status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ============================================
-- 2. 登录凭证表
-- ============================================
CREATE TABLE login_credentials (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '登录信息ID',
    alias VARCHAR(100) NOT NULL COMMENT '登录别名',
    host VARCHAR(255) NOT NULL COMMENT '主机地址',
    port INT DEFAULT 22 COMMENT 'SSH端口',
    username VARCHAR(100) NOT NULL COMMENT '用户名',
    auth_type ENUM('password', 'key') DEFAULT 'password' COMMENT '认证类型',
    password_encrypted TEXT COMMENT '加密后的密码',
    private_key_path VARCHAR(500) COMMENT '私钥文件路径',
    private_key_encrypted TEXT COMMENT '加密后的私钥内容',
    passphrase_encrypted TEXT COMMENT '加密后的私钥密码',
    root_password_encrypted TEXT COMMENT 'Root密码（加密）',
    base_path VARCHAR(500) DEFAULT '/tmp' COMMENT '基础文件路径',
    platform_partition VARCHAR(500) DEFAULT '/opt/io_platform' COMMENT '平台分区路径',
    description TEXT COMMENT '描述信息',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_by INT NOT NULL COMMENT '创建人',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY ix_alias (alias),
    INDEX idx_host (host),
    INDEX idx_created_by (created_by),
    INDEX idx_active (is_active),
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='登录凭证表';

-- ============================================
-- 3. 环境空间表
-- ============================================
CREATE TABLE environment_spaces (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '环境空间ID',
    name VARCHAR(100) NOT NULL COMMENT '环境空间名称',
    description TEXT COMMENT '环境空间描述',
    owner_id INT NOT NULL COMMENT '所有者ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    UNIQUE KEY ix_name (name),
    INDEX idx_owner_id (owner_id),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (owner_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='环境空间表';

-- ============================================
-- 4. 监控配置表
-- ============================================
CREATE TABLE monitoring_configs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '配置ID',
    environment_space_id INT COMMENT '环境空间ID，为空时表示全局配置',
    collection_interval INT DEFAULT 300 COMMENT '采集间隔(秒)，默认5分钟',
    retention_period INT DEFAULT 7 COMMENT '数据保留期(天)，默认7天',
    enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_environment_space_id (environment_space_id),
    INDEX idx_enabled (enabled),
    FOREIGN KEY (environment_space_id) REFERENCES environment_spaces(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='监控配置表';

-- ============================================
-- 5. 节点表
-- ============================================
CREATE TABLE nodes (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '节点ID',
    name VARCHAR(100) NOT NULL COMMENT '节点名称',
    ip_address VARCHAR(50) NOT NULL COMMENT 'IP地址',
    status ENUM('active', 'inactive', 'maintenance', 'error') DEFAULT 'inactive' COMMENT '节点状态',
    os_type VARCHAR(50) COMMENT '操作系统类型',
    os_version VARCHAR(100) COMMENT '操作系统版本',
    cpu_info VARCHAR(255) COMMENT 'CPU信息',
    memory_total BIGINT COMMENT '总内存(字节)',
    disk_total BIGINT COMMENT '总磁盘空间(字节)',
    login_credential_id INT COMMENT '登录凭证ID',
    environment_space_id INT COMMENT '所属环境空间ID',
    created_by INT NOT NULL COMMENT '创建人',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    last_heartbeat DATETIME COMMENT '最后心跳时间',
    io_partitions JSON DEFAULT '[]' COMMENT 'IO分区列表',
    UNIQUE KEY ix_name (name),
    INDEX idx_ip_address (ip_address),
    INDEX idx_status (status),
    INDEX idx_created_by (created_by),
    FOREIGN KEY (login_credential_id) REFERENCES login_credentials(id),
    FOREIGN KEY (environment_space_id) REFERENCES environment_spaces(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='节点表';

-- ============================================
-- 6. 节点状态历史表
-- ============================================
CREATE TABLE node_status_history (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '历史记录ID',
    node_id INT NOT NULL COMMENT '节点ID',
    status ENUM('active', 'inactive', 'maintenance', 'error') NOT NULL COMMENT '状态',
    message TEXT COMMENT '状态变更消息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
    INDEX idx_node_id (node_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (node_id) REFERENCES nodes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='节点状态历史表';

-- ============================================
-- 7. IO测试用例表
-- ============================================
CREATE TABLE io_test_cases (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '测试用例ID',
    name VARCHAR(100) NOT NULL COMMENT '用例名称',
    description TEXT COMMENT '用例描述',
    tool ENUM('fio', 'iozone') DEFAULT 'fio' COMMENT '测试工具',
    parameters JSON NOT NULL COMMENT '测试参数',
    partition_mode ENUM('concurrent', 'sequential') DEFAULT 'concurrent' COMMENT '分区执行模式',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开',
    created_by INT NOT NULL COMMENT '创建人',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY ix_name (name),
    INDEX idx_created_by (created_by),
    INDEX idx_public (is_public),
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='IO测试用例表';

-- ============================================
-- 8. 测试用例模板表
-- ============================================
CREATE TABLE test_case_templates (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '模板ID',
    name VARCHAR(100) NOT NULL COMMENT '模板名称',
    description TEXT COMMENT '模板描述',
    tool ENUM('fio', 'iozone') DEFAULT 'fio' COMMENT '测试工具',
    parameters JSON NOT NULL COMMENT '模板参数',
    category VARCHAR(50) COMMENT '模板分类',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY ix_name (name),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='测试用例模板表';

-- ============================================
-- 9. 任务空间表
-- ============================================
CREATE TABLE task_spaces (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '空间ID',
    name VARCHAR(100) NOT NULL COMMENT '空间名称',
    description TEXT COMMENT '空间描述',
    owner_id INT NOT NULL COMMENT '所有者ID',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_name (name),
    INDEX idx_owner_id (owner_id),
    INDEX idx_public (is_public),
    FOREIGN KEY (owner_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务空间表';

-- ============================================
-- 10. 任务空间成员表
-- ============================================
CREATE TABLE task_space_members (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '成员ID',
    task_space_id INT NOT NULL COMMENT '空间ID',
    user_id INT NOT NULL COMMENT '用户ID',
    role ENUM('admin', 'member') DEFAULT 'member' COMMENT '成员角色',
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
    INDEX idx_task_space_id (task_space_id),
    INDEX idx_user_id (user_id),
    UNIQUE KEY uq_task_space_user (task_space_id, user_id),
    FOREIGN KEY (task_space_id) REFERENCES task_spaces(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务空间成员表';

-- ============================================
-- 11. 测试任务表
-- ============================================
CREATE TABLE test_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '任务ID',
    name VARCHAR(100) NOT NULL COMMENT '任务名称',
    description TEXT COMMENT '任务描述',
    task_space_id INT COMMENT '任务空间ID',
    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled', 'stopped', 'cancelling') DEFAULT 'pending' COMMENT '任务状态',
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium' COMMENT '任务优先级',
    execution_mode ENUM('parallel', 'serial') DEFAULT 'parallel' COMMENT '执行模式',
    scheduled_at DATETIME COMMENT '计划执行时间',
    started_at DATETIME COMMENT '开始执行时间',
    completed_at DATETIME COMMENT '完成时间',
    created_by INT NOT NULL DEFAULT 1 COMMENT '创建人',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_name (name),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_created_by (created_by),
    FOREIGN KEY (task_space_id) REFERENCES task_spaces(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='测试任务表';

-- ============================================
-- 12. 任务执行表
-- ============================================
CREATE TABLE task_executions (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '执行ID',
    test_task_id INT NOT NULL COMMENT '任务ID',
    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled', 'stopped', 'cancelling') DEFAULT 'pending' COMMENT '执行状态',
    error_message TEXT COMMENT '错误信息',
    start_time DATETIME COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    duration INT COMMENT '执行时长(秒)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_test_task_id (test_task_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (test_task_id) REFERENCES test_tasks(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务执行表';

-- ============================================
-- 13. 测试结果表
-- ============================================
CREATE TABLE test_results (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '结果ID',
    test_task_id INT NOT NULL COMMENT '任务ID',
    node_id INT NOT NULL COMMENT '节点ID',
    io_test_case_id INT NOT NULL COMMENT '测试用例ID',
    task_execution_id INT NOT NULL COMMENT '执行ID',
    tool ENUM('fio', 'iozone') DEFAULT 'fio' COMMENT '测试工具',
    command TEXT COMMENT '执行命令',
    raw_output TEXT COMMENT '原始输出',
    parsed_results JSON COMMENT '解析后的结果',
    status ENUM('success', 'failed', 'partial') DEFAULT 'success' COMMENT '结果状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_test_task_id (test_task_id),
    INDEX idx_node_id (node_id),
    INDEX idx_io_test_case_id (io_test_case_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (test_task_id) REFERENCES test_tasks(id),
    FOREIGN KEY (node_id) REFERENCES nodes(id),
    FOREIGN KEY (io_test_case_id) REFERENCES io_test_cases(id),
    FOREIGN KEY (task_execution_id) REFERENCES task_executions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='测试结果表';

-- ============================================
-- 14. 测试结果聚合表
-- ============================================
CREATE TABLE test_result_aggregations (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '聚合ID',
    test_result_id INT NOT NULL COMMENT '结果ID',
    metric_name VARCHAR(100) NOT NULL COMMENT '指标名称',
    metric_value FLOAT NOT NULL COMMENT '指标值',
    metric_unit VARCHAR(50) COMMENT '指标单位',
    metric_type ENUM('average', 'min', 'max', 'sum', 'value') DEFAULT 'value' COMMENT '指标类型',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_test_result_id (test_result_id),
    INDEX idx_metric_name (metric_name),
    FOREIGN KEY (test_result_id) REFERENCES test_results(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='测试结果聚合表';

-- ============================================
-- 15. 测试日志表
-- ============================================
CREATE TABLE test_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    test_task_id INT NOT NULL COMMENT '任务ID',
    node_id INT NOT NULL COMMENT '节点ID',
    task_execution_id INT NOT NULL COMMENT '执行ID',
    log_type VARCHAR(50) NOT NULL COMMENT '日志类型(iostat/fio/system)',
    log_filename VARCHAR(255) NOT NULL COMMENT '日志文件名',
    log_path VARCHAR(500) NOT NULL COMMENT '日志文件路径',
    file_size INT COMMENT '文件大小(字节)',
    collection_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_test_task_id (test_task_id),
    INDEX idx_node_id (node_id),
    INDEX idx_task_execution_id (task_execution_id),
    INDEX idx_log_type (log_type),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (test_task_id) REFERENCES test_tasks(id),
    FOREIGN KEY (node_id) REFERENCES nodes(id),
    FOREIGN KEY (task_execution_id) REFERENCES task_executions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='测试日志表';

-- ============================================
-- 16. IOStat指标表
-- ============================================
CREATE TABLE iostat_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '指标ID',
    test_log_id INT NOT NULL COMMENT '日志ID',
    collection_time DATETIME NOT NULL COMMENT '采集时间',
    device VARCHAR(100) NOT NULL COMMENT '设备名称',
    read_kbps FLOAT COMMENT '读取速度(KB/s)',
    write_kbps FLOAT COMMENT '写入速度(KB/s)',
    read_iops FLOAT COMMENT '读取IOPS',
    write_iops FLOAT COMMENT '写入IOPS',
    await_time FLOAT COMMENT '平均等待时间(ms)',
    svctm FLOAT COMMENT '服务时间(ms)',
    util FLOAT COMMENT '利用率(%)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_test_log_id (test_log_id),
    INDEX idx_collection_time (collection_time),
    INDEX idx_device (device),
    FOREIGN KEY (test_log_id) REFERENCES test_logs(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='IOStat性能指标表';

-- ============================================
-- 17. IO性能数据表
-- ============================================
CREATE TABLE io_performance_data (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '数据ID',
    test_task_id INT NOT NULL COMMENT '任务ID',
    node_id INT NOT NULL COMMENT '节点ID',
    io_test_case_id INT NOT NULL COMMENT 'IO测试用例ID',
    task_execution_id INT NOT NULL COMMENT '执行ID',
    read_iops FLOAT COMMENT '读取IOPS',
    write_iops FLOAT COMMENT '写入IOPS',
    read_kbps FLOAT COMMENT '读取速度(KB/s)',
    write_kbps FLOAT COMMENT '写入速度(KB/s)',
    await_time FLOAT COMMENT '平均等待时间(ms)',
    svctm FLOAT COMMENT '服务时间(ms)',
    util FLOAT COMMENT '利用率(%)',
    lat_p99 FLOAT COMMENT 'P99延迟(ms)',
    lat_p9999 FLOAT COMMENT 'P9999延迟(ms)',
    lat_max FLOAT COMMENT '最大延迟(ms)',
    io_model_name VARCHAR(255) COMMENT 'IO模型名称',
    device VARCHAR(100) COMMENT '设备名称',
    io_start_time DATETIME COMMENT 'IO开始时间',
    io_end_time DATETIME COMMENT 'IO结束时间',
    collection_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_test_task_id (test_task_id),
    INDEX idx_node_id (node_id),
    INDEX idx_io_test_case_id (io_test_case_id),
    INDEX idx_task_execution_id (task_execution_id),
    INDEX idx_collection_time (collection_time),
    INDEX idx_io_model_name (io_model_name),
    INDEX idx_device (device),
    FOREIGN KEY (test_task_id) REFERENCES test_tasks(id),
    FOREIGN KEY (node_id) REFERENCES nodes(id),
    FOREIGN KEY (io_test_case_id) REFERENCES io_test_cases(id),
    FOREIGN KEY (task_execution_id) REFERENCES task_executions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='IO性能数据表';

-- ============================================
-- 18. 系统指标表
-- ============================================
CREATE TABLE system_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '指标ID',
    node_id INT NOT NULL COMMENT '节点ID',
    metric_type VARCHAR(50) NOT NULL COMMENT '指标类型',
    metric_name VARCHAR(100) NOT NULL COMMENT '指标名称',
    metric_value FLOAT NOT NULL COMMENT '指标值',
    metric_unit VARCHAR(50) COMMENT '指标单位',
    partition_name VARCHAR(255) COMMENT '分区名称，用于分区级别指标',
    collection_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_node_id (node_id),
    INDEX idx_metric_type (metric_type),
    INDEX idx_metric_name (metric_name),
    INDEX idx_partition_name (partition_name),
    INDEX idx_collection_time (collection_time),
    INDEX idx_node_partition_time (node_id, partition_name, collection_time),
    FOREIGN KEY (node_id) REFERENCES nodes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统指标表';

-- ============================================
-- 19. 操作日志表
-- ============================================
CREATE TABLE operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    user_id INT NOT NULL COMMENT '操作用户ID',
    operation_type VARCHAR(50) NOT NULL COMMENT '操作类型',
    operation_target VARCHAR(100) NOT NULL COMMENT '操作目标',
    target_id INT COMMENT '目标ID',
    operation_details TEXT COMMENT '操作详情',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    user_agent VARCHAR(500) COMMENT '用户代理',
    result ENUM('success', 'failed', 'partial') DEFAULT 'success' COMMENT '操作结果',
    error_message TEXT COMMENT '错误信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    INDEX idx_user_id (user_id),
    INDEX idx_operation_type (operation_type),
    INDEX idx_operation_target (operation_target),
    INDEX idx_result (result),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- ============================================
-- 20. 任务操作日志表
-- ============================================
CREATE TABLE task_operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    test_task_id INT NOT NULL COMMENT '任务ID',
    task_execution_id INT COMMENT '执行ID',
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '时间戳',
    level VARCHAR(20) DEFAULT 'INFO' COMMENT '日志级别',
    message TEXT NOT NULL COMMENT '日志消息',
    context TEXT COMMENT '上下文信息(JSON)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_task_operation_task_id (test_task_id),
    INDEX idx_task_operation_execution_id (task_execution_id),
    INDEX idx_task_operation_timestamp (timestamp),
    INDEX idx_task_operation_level (level),
    FOREIGN KEY (test_task_id) REFERENCES test_tasks(id),
    FOREIGN KEY (task_execution_id) REFERENCES task_executions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务操作日志表';

-- ============================================
-- 21. 任务-测试用例关联表
-- ============================================
CREATE TABLE task_case_association (
    test_task_id INT NOT NULL COMMENT '测试任务ID',
    io_test_case_id INT NOT NULL COMMENT 'IO测试用例ID',
    PRIMARY KEY (test_task_id, io_test_case_id),
    INDEX idx_task_case_task_id (test_task_id),
    INDEX idx_task_case_case_id (io_test_case_id),
    FOREIGN KEY (test_task_id) REFERENCES test_tasks(id),
    FOREIGN KEY (io_test_case_id) REFERENCES io_test_cases(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务-测试用例关联表';

-- ============================================
-- 22. 任务-节点关联表
-- ============================================
CREATE TABLE task_node_association (
    test_task_id INT NOT NULL COMMENT '测试任务ID',
    node_id INT NOT NULL COMMENT '节点ID',
    PRIMARY KEY (test_task_id, node_id),
    INDEX idx_task_node_task_id (test_task_id),
    INDEX idx_task_node_node_id (node_id),
    FOREIGN KEY (test_task_id) REFERENCES test_tasks(id),
    FOREIGN KEY (node_id) REFERENCES nodes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务-节点关联表';

-- ============================================
-- 初始化数据
-- ============================================

-- 插入默认管理员用户 (密码: admin123)
INSERT INTO users (username, email, password_hash, role, status) VALUES
('admin', 'admin@diskbench.local', 'scrypt:32768:8:1$YxZ8vF2mK9pL4qRw$7e4d8c3b6a9f1e2d5c8b4a7d9e6f3c2b5a8d1e4f7c3b6a9d2e5f8c1b4a7d0e3f', 'admin', 'active');

-- 插入全局监控配置
INSERT INTO monitoring_configs (environment_space_id, collection_interval, retention_period, enabled) VALUES
(NULL, 300, 7, TRUE);
