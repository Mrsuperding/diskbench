create table monitor
(
    id   int auto_increment
        primary key,
    ts   datetime null,
    cpu  float    null,
    mem  float    null,
    disk float    null
);

create index ix_monitor_id
    on monitor (id);

create index ix_monitor_ts
    on monitor (ts);

create table users
(
    id         int auto_increment
        primary key,
    username   varchar(50)                        not null,
    email      varchar(100)                       not null,
    password   varchar(255)                       not null,
    role       enum ('admin', 'user')             not null,
    is_active  tinyint(1)                         not null,
    avatar     varchar(255)                       null,
    created_at datetime default CURRENT_TIMESTAMP null,
    updated_at datetime default CURRENT_TIMESTAMP null,
    constraint ix_users_email
        unique (email),
    constraint ix_users_username
        unique (username)
);

create table nodes
(
    id          int auto_increment
        primary key,
    node_name   varchar(100)                          not null,
    host        varchar(255)                          not null,
    port        int                                   not null,
    login_type  enum ('password', 'key')              not null,
    username    varchar(100)                          not null,
    password    varchar(255)                          null,
    private_key text                                  null,
    status      enum ('online', 'offline', 'testing') not null,
    os_type     varchar(50)                           null,
    cpu_info    varchar(255)                          null,
    memory_info varchar(255)                          null,
    disk_info   text                                  null,
    created_by  int                                   null,
    is_public   tinyint(1)                            not null,
    created_at  datetime default CURRENT_TIMESTAMP    null,
    updated_at  datetime default CURRENT_TIMESTAMP    null,
    constraint nodes_ibfk_1
        foreign key (created_by) references users (id)
);

create table node_partitions
(
    id             int auto_increment
        primary key,
    node_id        int                                not null,
    partition_name varchar(100)                       not null,
    mount_point    varchar(255)                       not null,
    filesystem     varchar(50)                        null,
    total_size     int                                null,
    available_size int                                null,
    is_active      tinyint(1)                         not null,
    created_at     datetime default CURRENT_TIMESTAMP null,
    constraint node_partitions_ibfk_1
        foreign key (node_id) references nodes (id)
);

create index ix_node_partitions_id
    on node_partitions (id);

create index node_id
    on node_partitions (node_id);

create index created_by
    on nodes (created_by);

create index ix_nodes_id
    on nodes (id);

create index ix_nodes_node_name
    on nodes (node_name);

create table test_cases
(
    id                int auto_increment
        primary key,
    case_name         varchar(200)                                                    not null,
    description       text                                                            null,
    io_engine         varchar(50)                                                     not null,
    block_size        varchar(20)                                                     not null,
    queue_depth       int                                                             not null,
    io_size           varchar(20)                                                     not null,
    runtime           int                                                             not null,
    rw_mode           enum ('read', 'write', 'randread', 'randwrite', 'rw', 'randrw') not null,
    rw_ratio          varchar(10)                                                     not null,
    compression_ratio decimal(3, 2)                                                   not null,
    direct_io         tinyint(1)                                                      not null,
    numjobs           int                                                             not null,
    time_based        tinyint(1)                                                      not null,
    verify            varchar(20)                                                     null,
    verify_fatal      tinyint(1)                                                      not null,
    group_reporting   tinyint(1)                                                      not null,
    created_by        int                                                             null,
    is_public         tinyint(1)                                                      not null,
    is_template       tinyint(1)                                                      not null,
    created_at        datetime default CURRENT_TIMESTAMP                              null,
    updated_at        datetime default CURRENT_TIMESTAMP                              null,
    constraint test_cases_ibfk_1
        foreign key (created_by) references users (id)
);

create table tasks
(
    id           int auto_increment
        primary key,
    task_name    varchar(200)                                                    not null,
    description  text                                                            null,
    status       enum ('pending', 'running', 'completed', 'failed', 'cancelled') not null,
    created_by   int                                                             not null,
    test_case_id int                                                             not null,
    is_public    tinyint(1)                                                      not null,
    start_time   datetime                                                        null,
    end_time     datetime                                                        null,
    duration     int                                                             null,
    total_io_ops bigint                                                          null,
    avg_iops     decimal(10, 2)                                                  null,
    avg_latency  decimal(10, 2)                                                  null,
    avg_bw       decimal(10, 2)                                                  null,
    created_at   datetime default CURRENT_TIMESTAMP                              null,
    updated_at   datetime default CURRENT_TIMESTAMP                              null,
    constraint tasks_ibfk_1
        foreign key (created_by) references users (id),
    constraint tasks_ibfk_2
        foreign key (test_case_id) references test_cases (id)
);

create table task_logs
(
    id         int auto_increment
        primary key,
    task_id    int                                        not null,
    log_level  enum ('debug', 'info', 'warning', 'error') not null,
    message    text                                       not null,
    source     varchar(50)                                null,
    created_at datetime default CURRENT_TIMESTAMP         null,
    constraint task_logs_ibfk_1
        foreign key (task_id) references tasks (id)
);

create index ix_task_logs_id
    on task_logs (id);

create index task_id
    on task_logs (task_id);

create table task_nodes
(
    id            int auto_increment
        primary key,
    task_id       int                                                             not null,
    node_id       int                                                             not null,
    partition_id  int                                                             not null,
    status        enum ('pending', 'running', 'completed', 'failed', 'cancelled') not null,
    start_time    datetime                                                        null,
    end_time      datetime                                                        null,
    duration      int                                                             null,
    io_ops        bigint                                                          null,
    iops          decimal(10, 2)                                                  null,
    latency       decimal(10, 2)                                                  null,
    bandwidth     decimal(10, 2)                                                  null,
    error_message text                                                            null,
    created_at    datetime default CURRENT_TIMESTAMP                              null,
    constraint task_nodes_ibfk_1
        foreign key (task_id) references tasks (id),
    constraint task_nodes_ibfk_2
        foreign key (node_id) references nodes (id),
    constraint task_nodes_ibfk_3
        foreign key (partition_id) references node_partitions (id)
);

create table io_performance_data
(
    id           int auto_increment
        primary key,
    task_node_id int                                not null,
    timestamp    datetime default CURRENT_TIMESTAMP null,
    iops         decimal(10, 2)                     not null,
    bandwidth    decimal(10, 2)                     not null,
    latency      decimal(10, 2)                     not null,
    read_iops    decimal(10, 2)                     null,
    write_iops   decimal(10, 2)                     null,
    read_bw      decimal(10, 2)                     null,
    write_bw     decimal(10, 2)                     null,
    read_lat     decimal(10, 2)                     null,
    write_lat    decimal(10, 2)                     null,
    cpu_usage    decimal(5, 2)                      null,
    memory_usage decimal(5, 2)                      null,
    constraint io_performance_data_ibfk_1
        foreign key (task_node_id) references task_nodes (id)
);

create index ix_io_performance_data_id
    on io_performance_data (id);

create index task_node_id
    on io_performance_data (task_node_id);

create table iostat_data
(
    id           int auto_increment
        primary key,
    task_node_id int                                not null,
    timestamp    datetime default CURRENT_TIMESTAMP null,
    device       varchar(50)                        not null,
    tps          decimal(10, 2)                     not null,
    kB_read_s    decimal(10, 2)                     not null,
    kB_wrtn_s    decimal(10, 2)                     not null,
    kB_dscd_s    decimal(10, 2)                     null,
    kB_read      bigint                             null,
    kB_wrtn      bigint                             null,
    kB_dscd      bigint                             null,
    rqmps        decimal(10, 2)                     null,
    await_time   decimal(10, 2)                     null,
    aqu_sz       decimal(10, 2)                     null,
    util         decimal(5, 2)                      null,
    constraint iostat_data_ibfk_1
        foreign key (task_node_id) references task_nodes (id)
);

create index ix_iostat_data_id
    on iostat_data (id);

create index task_node_id
    on iostat_data (task_node_id);

create index ix_task_nodes_id
    on task_nodes (id);

create index node_id
    on task_nodes (node_id);

create index partition_id
    on task_nodes (partition_id);

create index task_id
    on task_nodes (task_id);

create index created_by
    on tasks (created_by);

create index ix_tasks_id
    on tasks (id);

create index ix_tasks_task_name
    on tasks (task_name);

create index test_case_id
    on tasks (test_case_id);

create index created_by
    on test_cases (created_by);

create index ix_test_cases_case_name
    on test_cases (case_name);

create index ix_test_cases_id
    on test_cases (id);

create index ix_users_id
    on users (id);

大苏打