create table environment_spaces
(
	id int auto_increment comment '环境空间ID'
		primary key,
	name varchar(100) not null comment '环境空间名称',
	description text null comment '环境空间描述',
	owner_id int not null comment '所有者ID',
	created_at datetime null comment '创建时间',
	updated_at datetime null comment '更新时间',
	is_active tinyint(1) null comment '是否激活'
);

create index idx_is_active
	on environment_spaces (is_active);

create index idx_name
	on environment_spaces (name);

create index idx_owner_id
	on environment_spaces (owner_id);

alter table environment_spaces
	add constraint name
		unique (name);

create table io_performance_data
(
	id int auto_increment comment '数据ID'
		primary key,
	test_task_id int not null comment '任务ID',
	node_id int not null comment '节点ID',
	io_test_case_id int not null comment 'IO测试用例ID',
	task_execution_id int not null comment '执行ID',
	read_iops float null comment '读取IOPS',
	write_iops float null comment '写入IOPS',
	read_kbps float null comment '读取速度(KB/s)',
	write_kbps float null comment '写入速度(KB/s)',
	await_time float null comment '平均等待时间(ms)',
	svctm float null comment '服务时间(ms)',
	util float null comment '利用率(%)',
	lat_p99 float null comment 'P99延迟(ms)',
	lat_max float null comment '最大延迟(ms)',
	io_model_name varchar(255) null comment 'IO模型名称',
	device varchar(100) null comment '设备名称',
	io_start_time datetime null comment 'IO开始时间',
	io_end_time datetime null comment 'IO结束时间',
	collection_time datetime null comment '采集时间',
	created_at datetime null comment '创建时间',
	lat_p9999 float null comment 'P9999延迟(ms)'
);

create index idx_collection_time
	on io_performance_data (collection_time);

create index idx_device
	on io_performance_data (device);

create index idx_io_model_name
	on io_performance_data (io_model_name);

create index idx_io_test_case_id
	on io_performance_data (io_test_case_id);

create index idx_node_id
	on io_performance_data (node_id);

create index idx_task_execution_id
	on io_performance_data (task_execution_id);

create index idx_test_task_id
	on io_performance_data (test_task_id);

create table io_test_cases
(
	id int auto_increment comment '测试用例ID'
		primary key,
	name varchar(100) not null comment '用例名称',
	description text null comment '用例描述',
	tool enum('fio', 'iozone') null comment '测试工具',
	parameters json not null comment '测试参数',
	partition_mode enum('concurrent', 'sequential') default 'concurrent' null comment '鍒嗗尯鎵ц?妯″紡锛歝oncurrent骞跺彂锛宻equential涓茶?',
	is_public tinyint(1) null comment '是否公开',
	created_by int not null comment '创建人',
	created_at datetime null comment '创建时间',
	updated_at datetime null comment '更新时间'
);

alter table io_performance_data
	add constraint io_performance_data_ibfk_3
		foreign key (io_test_case_id) references io_test_cases (id);

create index idx_created_by
	on io_test_cases (created_by);

create index idx_name
	on io_test_cases (name);

create index idx_public
	on io_test_cases (is_public);

alter table io_test_cases
	add constraint name
		unique (name);

create table iostat_metrics
(
	id int auto_increment comment '指标ID'
		primary key,
	test_log_id int not null comment '日志ID',
	collection_time datetime not null comment '采集时间',
	device varchar(100) not null comment '设备名称',
	read_kbps float null comment '读取速度(KB/s)',
	write_kbps float null comment '写入速度(KB/s)',
	read_iops float null comment '读取IOPS',
	write_iops float null comment '写入IOPS',
	await_time float null comment '平均等待时间(ms)',
	svctm float null comment '服务时间(ms)',
	util float null comment '利用率(%)',
	created_at datetime null comment '创建时间'
);

create index idx_collection_time
	on iostat_metrics (collection_time);

create index idx_device
	on iostat_metrics (device);

create index idx_test_log_id
	on iostat_metrics (test_log_id);

create table login_credentials
(
	id int auto_increment comment '登录信息ID'
		primary key,
	alias varchar(100) not null comment '登录别名',
	host varchar(255) not null comment '主机地址',
	port int null comment 'SSH端口',
	username varchar(100) not null comment '用户名',
	auth_type enum('password', 'key') null comment '认证类型',
	password_encrypted text null comment '加密后的密码',
	private_key_path varchar(500) null comment '私钥文件路径',
	root_password_encrypted text null comment 'Root密码（加密）',
	base_path varchar(500) null comment '基础文件路径',
	description text null comment '描述信息',
	is_active tinyint(1) null comment '是否激活',
	created_by int not null comment '创建人',
	created_at datetime null comment '创建时间',
	updated_at datetime null comment '更新时间',
	private_key_encrypted text null,
	passphrase_encrypted text null,
	platform_partition varchar(255) default '/opt/io_platform' null comment '平台在节点的运行日志和IO日志以及fio需要的各种依赖文件的存放分区'
);

create index idx_active
	on login_credentials (is_active);

create index idx_alias
	on login_credentials (alias);

create index idx_created_by
	on login_credentials (created_by);

create index idx_host
	on login_credentials (host);

alter table login_credentials
	add constraint alias
		unique (alias);

create table monitoring_configs
(
	id int auto_increment comment '配置ID'
		primary key,
	environment_space_id int null comment '环境空间ID，为空时表示全局配置',
	collection_interval int null comment '采集间隔(秒)，默认5分钟',
	retention_period int null comment '数据保留期(天)，默认7天',
	enabled tinyint(1) null comment '是否启用',
	created_at datetime null comment '创建时间',
	updated_at datetime null comment '更新时间'
);

create index idx_enabled
	on monitoring_configs (enabled);

create index idx_environment_space_id
	on monitoring_configs (environment_space_id);

alter table monitoring_configs
	add constraint monitoring_configs_ibfk_1
		foreign key (environment_space_id) references environment_spaces (id);

create table node_status_history
(
	id int auto_increment comment '历史记录ID'
		primary key,
	node_id int not null comment '节点ID',
	status enum('active', 'inactive', 'maintenance', 'error') not null comment '状态',
	message text null comment '状态变更消息',
	created_at datetime null comment '记录时间'
);

create index idx_created_at
	on node_status_history (created_at);

create index idx_node_id
	on node_status_history (node_id);

create table nodes
(
	id int auto_increment comment '节点ID'
		primary key,
	name varchar(100) not null comment '节点名称',
	ip_address varchar(50) not null comment 'IP地址',
	status enum('active', 'inactive', 'maintenance', 'error') null comment '节点状态',
	os_type varchar(50) null comment '操作系统类型',
	os_version varchar(100) null comment '操作系统版本',
	cpu_info varchar(255) null comment 'CPU信息',
	memory_total bigint null comment '总内存(字节)',
	disk_total bigint null comment '总磁盘空间(字节)',
	login_credential_id int not null comment '登录凭证ID',
	created_by int not null comment '创建人',
	created_at datetime null comment '创建时间',
	updated_at datetime null comment '更新时间',
	last_heartbeat datetime null comment '最后心跳时间',
	io_partitions json null comment 'IO分区列表',
	environment_space_id int null
);

alter table io_performance_data
	add constraint io_performance_data_ibfk_2
		foreign key (node_id) references nodes (id);

alter table node_status_history
	add constraint node_status_history_ibfk_1
		foreign key (node_id) references nodes (id);

create index idx_created_by
	on nodes (created_by);

create index idx_name
	on nodes (name);

create index idx_status
	on nodes (status);

create index login_credential_id
	on nodes (login_credential_id);

alter table nodes
	add constraint name
		unique (name);

alter table nodes
	add constraint fk_nodes_environment_space
		foreign key (environment_space_id) references environment_spaces (id)
			on delete set null;

alter table nodes
	add constraint nodes_ibfk_1
		foreign key (login_credential_id) references login_credentials (id);

create table operation_logs
(
	id int auto_increment comment '日志ID'
		primary key,
	user_id int not null comment '操作用户ID',
	operation_type varchar(50) not null comment '操作类型',
	operation_target varchar(100) not null comment '操作目标',
	target_id int null comment '目标ID',
	operation_details text null comment '操作详情',
	ip_address varchar(50) null comment 'IP地址',
	user_agent varchar(500) null comment '用户代理',
	result enum('success', 'failed', 'partial') null comment '操作结果',
	error_message text null comment '错误信息',
	created_at datetime null comment '操作时间'
);

create index idx_created_at
	on operation_logs (created_at);

create index idx_operation_target
	on operation_logs (operation_target);

create index idx_operation_type
	on operation_logs (operation_type);

create index idx_result
	on operation_logs (result);

create index idx_user_id
	on operation_logs (user_id);

create table system_metrics
(
	id int auto_increment comment '指标ID'
		primary key,
	node_id int not null comment '节点ID',
	metric_type varchar(50) not null comment '指标类型',
	metric_name varchar(100) not null comment '指标名称',
	metric_value float not null comment '指标值',
	metric_unit varchar(50) null comment '指标单位',
	collection_time datetime null comment '采集时间',
	created_at datetime null comment '创建时间',
	partition_name varchar(255) null comment '分区名称，用于分区级别指标'
);

create index idx_collection_time
	on system_metrics (collection_time);

create index idx_metric_name
	on system_metrics (metric_name);

create index idx_metric_type
	on system_metrics (metric_type);

create index idx_node_id
	on system_metrics (node_id);

create index idx_node_partition_time
	on system_metrics (node_id, partition_name, collection_time);

create index idx_partition_name
	on system_metrics (partition_name);

alter table system_metrics
	add constraint system_metrics_ibfk_1
		foreign key (node_id) references nodes (id);

create table task_case_association
(
	test_task_id int not null,
	io_test_case_id int not null
);

create index io_test_case_id
	on task_case_association (io_test_case_id);

alter table task_case_association
	add primary key (test_task_id, io_test_case_id);

alter table task_case_association
	add constraint task_case_association_ibfk_2
		foreign key (io_test_case_id) references io_test_cases (id);

create table task_executions
(
	id int auto_increment comment '执行ID'
		primary key,
	test_task_id int not null comment '任务ID',
	status enum('pending', 'running', 'completed', 'failed', 'cancelled') null comment '执行状态',
	error_message text null comment '错误信息',
	start_time datetime null comment '开始时间',
	end_time datetime null comment '结束时间',
	duration int null comment '执行时长(秒)',
	created_at datetime null comment '创建时间'
);

alter table io_performance_data
	add constraint io_performance_data_ibfk_4
		foreign key (task_execution_id) references task_executions (id);

create index idx_created_at
	on task_executions (created_at);

create index idx_status
	on task_executions (status);

create index idx_test_task_id
	on task_executions (test_task_id);

create table task_node_association
(
	test_task_id int not null,
	node_id int not null
);

create index node_id
	on task_node_association (node_id);

alter table task_node_association
	add primary key (test_task_id, node_id);

alter table task_node_association
	add constraint task_node_association_ibfk_2
		foreign key (node_id) references nodes (id);

create table task_operation_logs
(
	id int auto_increment comment '日志ID'
		primary key,
	test_task_id int not null comment '任务ID',
	task_execution_id int null comment '执行ID',
	timestamp datetime not null comment '时间戳',
	level varchar(20) null comment '日志级别',
	message text not null comment '日志消息',
	context text null comment '上下文信息(JSON)',
	created_at datetime null comment '创建时间'
);

create index idx_task_operation_execution_id
	on task_operation_logs (task_execution_id);

create index idx_task_operation_level
	on task_operation_logs (level);

create index idx_task_operation_task_id
	on task_operation_logs (test_task_id);

create index idx_task_operation_timestamp
	on task_operation_logs (timestamp);

alter table task_operation_logs
	add constraint task_operation_logs_ibfk_2
		foreign key (task_execution_id) references task_executions (id);

create table task_space_members
(
	id int auto_increment comment '成员ID'
		primary key,
	task_space_id int not null comment '空间ID',
	user_id int not null comment '用户ID',
	role enum('admin', 'member') null comment '成员角色',
	joined_at datetime null comment '加入时间'
);

create index idx_task_space_id
	on task_space_members (task_space_id);

create index idx_user_id
	on task_space_members (user_id);

alter table task_space_members
	add constraint uq_task_space_user
		unique (task_space_id, user_id);

create table task_spaces
(
	id int auto_increment comment '空间ID'
		primary key,
	name varchar(100) not null comment '空间名称',
	description text null comment '空间描述',
	owner_id int not null comment '所有者ID',
	is_public tinyint(1) null comment '是否公开',
	created_at datetime null comment '创建时间',
	updated_at datetime null comment '更新时间'
);

alter table task_space_members
	add constraint task_space_members_ibfk_1
		foreign key (task_space_id) references task_spaces (id);

create index idx_name
	on task_spaces (name);

create index idx_owner_id
	on task_spaces (owner_id);

create index idx_public
	on task_spaces (is_public);

create table test_case_templates
(
	id int auto_increment comment '模板ID'
		primary key,
	name varchar(100) not null comment '模板名称',
	description text null comment '模板描述',
	tool enum('fio', 'iozone') null comment '测试工具',
	parameters json not null comment '模板参数',
	category varchar(50) null comment '模板分类',
	created_at datetime null comment '创建时间',
	updated_at datetime null comment '更新时间'
);

create index idx_category
	on test_case_templates (category);

create index idx_name
	on test_case_templates (name);

alter table test_case_templates
	add constraint name
		unique (name);

create table test_logs
(
	id int auto_increment comment '日志ID'
		primary key,
	test_task_id int not null comment '任务ID',
	node_id int not null comment '节点ID',
	task_execution_id int not null comment '执行ID',
	log_type varchar(50) not null comment '日志类型(iostat/fio/system)',
	log_filename varchar(255) not null comment '日志文件名',
	log_path varchar(500) not null comment '日志文件路径',
	file_size int null comment '文件大小(字节)',
	collection_time datetime null comment '采集时间',
	created_at datetime null comment '创建时间'
);

alter table iostat_metrics
	add constraint iostat_metrics_ibfk_1
		foreign key (test_log_id) references test_logs (id);

create index idx_created_at
	on test_logs (created_at);

create index idx_log_type
	on test_logs (log_type);

create index idx_node_id
	on test_logs (node_id);

create index idx_task_execution_id
	on test_logs (task_execution_id);

create index idx_test_task_id
	on test_logs (test_task_id);

alter table test_logs
	add constraint test_logs_ibfk_2
		foreign key (node_id) references nodes (id);

alter table test_logs
	add constraint test_logs_ibfk_3
		foreign key (task_execution_id) references task_executions (id);

create table test_result_aggregations
(
	id int auto_increment comment '聚合ID'
		primary key,
	test_result_id int not null comment '结果ID',
	metric_name varchar(100) not null comment '指标名称',
	metric_value float not null comment '指标值',
	metric_unit varchar(50) null comment '指标单位',
	metric_type enum('average', 'min', 'max', 'sum', 'value') null comment '指标类型',
	created_at datetime null comment '创建时间'
);

create index idx_metric_name
	on test_result_aggregations (metric_name);

create index idx_test_result_id
	on test_result_aggregations (test_result_id);

create table test_results
(
	id int auto_increment comment '结果ID'
		primary key,
	test_task_id int not null comment '任务ID',
	node_id int not null comment '节点ID',
	io_test_case_id int not null comment '测试用例ID',
	task_execution_id int not null comment '执行ID',
	tool enum('fio', 'iozone') null comment '测试工具',
	command text null comment '执行命令',
	raw_output text null comment '原始输出',
	parsed_results json null comment '解析后的结果',
	status enum('success', 'failed', 'partial') null comment '结果状态',
	created_at datetime null comment '创建时间'
);

alter table test_result_aggregations
	add constraint test_result_aggregations_ibfk_1
		foreign key (test_result_id) references test_results (id);

create index idx_created_at
	on test_results (created_at);

create index idx_io_test_case_id
	on test_results (io_test_case_id);

create index idx_node_id
	on test_results (node_id);

create index idx_status
	on test_results (status);

create index idx_test_task_id
	on test_results (test_task_id);

create index task_execution_id
	on test_results (task_execution_id);

alter table test_results
	add constraint test_results_ibfk_2
		foreign key (node_id) references nodes (id);

alter table test_results
	add constraint test_results_ibfk_3
		foreign key (io_test_case_id) references io_test_cases (id);

alter table test_results
	add constraint test_results_ibfk_4
		foreign key (task_execution_id) references task_executions (id);

create table test_tasks
(
	id int auto_increment comment '任务ID'
		primary key,
	name varchar(100) not null comment '任务名称',
	description text null comment '任务描述',
	node_id int null,
	io_test_case_id int null,
	task_space_id int null comment '任务空间ID',
	status enum('pending', 'running', 'completed', 'failed', 'cancelled') null comment '任务状态',
	priority enum('low', 'medium', 'high') null comment '任务优先级',
	scheduled_at datetime null comment '计划执行时间',
	started_at datetime null comment '开始执行时间',
	completed_at datetime null comment '完成时间',
	created_by int not null comment '创建人',
	created_at datetime null comment '创建时间',
	updated_at datetime null comment '更新时间',
	execution_mode enum('parallel', 'serial') default 'parallel' null comment '执行模式'
);

alter table io_performance_data
	add constraint io_performance_data_ibfk_1
		foreign key (test_task_id) references test_tasks (id);

alter table task_case_association
	add constraint task_case_association_ibfk_1
		foreign key (test_task_id) references test_tasks (id);

alter table task_executions
	add constraint task_executions_ibfk_1
		foreign key (test_task_id) references test_tasks (id);

alter table task_node_association
	add constraint task_node_association_ibfk_1
		foreign key (test_task_id) references test_tasks (id);

alter table task_operation_logs
	add constraint task_operation_logs_ibfk_1
		foreign key (test_task_id) references test_tasks (id);

alter table test_logs
	add constraint test_logs_ibfk_1
		foreign key (test_task_id) references test_tasks (id);

alter table test_results
	add constraint test_results_ibfk_1
		foreign key (test_task_id) references test_tasks (id);

create index idx_created_by
	on test_tasks (created_by);

create index idx_io_test_case_id
	on test_tasks (io_test_case_id);

create index idx_name
	on test_tasks (name);

create index idx_node_id
	on test_tasks (node_id);

create index idx_priority
	on test_tasks (priority);

create index idx_status
	on test_tasks (status);

create index task_space_id
	on test_tasks (task_space_id);

alter table test_tasks
	add constraint test_tasks_ibfk_1
		foreign key (node_id) references nodes (id);

alter table test_tasks
	add constraint test_tasks_ibfk_2
		foreign key (io_test_case_id) references io_test_cases (id);

alter table test_tasks
	add constraint test_tasks_ibfk_3
		foreign key (task_space_id) references task_spaces (id);

create table users
(
	id int auto_increment comment '用户ID'
		primary key,
	username varchar(50) not null comment '用户名',
	email varchar(100) not null comment '邮箱地址',
	password_hash varchar(255) not null comment '密码哈希',
	role enum('admin', 'user') null comment '用户角色',
	status enum('active', 'inactive', 'locked') null comment '账户状态',
	avatar_url varchar(500) null comment '头像URL',
	last_login_at datetime null comment '最后登录时间',
	login_count int null comment '登录次数',
	created_at datetime null comment '创建时间',
	updated_at datetime null comment '更新时间'
);

alter table environment_spaces
	add constraint environment_spaces_ibfk_1
		foreign key (owner_id) references users (id);

alter table io_test_cases
	add constraint io_test_cases_ibfk_1
		foreign key (created_by) references users (id);

alter table login_credentials
	add constraint login_credentials_ibfk_1
		foreign key (created_by) references users (id);

alter table nodes
	add constraint nodes_ibfk_2
		foreign key (created_by) references users (id);

alter table operation_logs
	add constraint operation_logs_ibfk_1
		foreign key (user_id) references users (id);

alter table task_space_members
	add constraint task_space_members_ibfk_2
		foreign key (user_id) references users (id);

alter table task_spaces
	add constraint task_spaces_ibfk_1
		foreign key (owner_id) references users (id);

alter table test_tasks
	add constraint test_tasks_ibfk_4
		foreign key (created_by) references users (id);

create index idx_created_at
	on users (created_at);

create index idx_email
	on users (email);

create index idx_role_status
	on users (role, status);

create index idx_username
	on users (username);

alter table users
	add constraint email
		unique (email);

alter table users
	add constraint username
		unique (username);

