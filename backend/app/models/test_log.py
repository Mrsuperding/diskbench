from datetime import datetime
from app.models import db

class TestLog(db.Model):
    """测试日志模型 - 存储日志文件元数据"""
    
    __tablename__ = 'test_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='日志ID')
    test_task_id = db.Column(db.Integer, db.ForeignKey('test_tasks.id'), nullable=False, comment='任务ID')
    node_id = db.Column(db.Integer, db.ForeignKey('nodes.id'), nullable=False, comment='节点ID')
    task_execution_id = db.Column(db.Integer, db.ForeignKey('task_executions.id'), nullable=False, comment='执行ID')
    log_type = db.Column(db.String(50), nullable=False, comment='日志类型(iostat/fio/system)')
    log_filename = db.Column(db.String(255), nullable=False, comment='日志文件名')
    log_path = db.Column(db.String(500), nullable=False, comment='日志文件路径')
    file_size = db.Column(db.Integer, comment='文件大小(字节)')
    collection_time = db.Column(db.DateTime, default=datetime.utcnow, comment='采集时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    iostat_metrics = db.relationship('IOStatMetric', backref='test_log', lazy='dynamic', cascade='all, delete-orphan')
    
    # 索引
    __table_args__ = (
        db.Index('idx_test_task_id', 'test_task_id'),
        db.Index('idx_node_id', 'node_id'),
        db.Index('idx_task_execution_id', 'task_execution_id'),
        db.Index('idx_log_type', 'log_type'),
        db.Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f'<TestLog {self.log_type} - {self.log_filename}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'test_task_id': self.test_task_id,
            'node_id': self.node_id,
            'task_execution_id': self.task_execution_id,
            'log_type': self.log_type,
            'log_filename': self.log_filename,
            'log_path': self.log_path,
            'file_size': self.file_size,
            'collection_time': self.collection_time.isoformat(),
            'timestamp': self.collection_time.isoformat(),
            'created_at': self.created_at.isoformat(),
        }
    
    @classmethod
    def get_by_test_task(cls, test_task_id):
        """根据任务ID获取日志"""
        return cls.query.filter_by(test_task_id=test_task_id).all()
    
    @classmethod
    def get_by_node(cls, node_id):
        """根据节点ID获取日志"""
        return cls.query.filter_by(node_id=node_id).all()
    
    @classmethod
    def get_by_execution(cls, task_execution_id):
        """根据执行ID获取日志"""
        return cls.query.filter_by(task_execution_id=task_execution_id).all()


class IOStatMetric(db.Model):
    """IOStat性能指标模型 - 存储解析后的iostat指标"""
    
    __tablename__ = 'iostat_metrics'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='指标ID')
    test_log_id = db.Column(db.Integer, db.ForeignKey('test_logs.id'), nullable=False, comment='日志ID')
    collection_time = db.Column(db.DateTime, nullable=False, comment='采集时间')
    device = db.Column(db.String(100), nullable=False, comment='设备名称')
    read_kbps = db.Column(db.Float, comment='读取速度(KB/s)')
    write_kbps = db.Column(db.Float, comment='写入速度(KB/s)')
    read_iops = db.Column(db.Float, comment='读取IOPS')
    write_iops = db.Column(db.Float, comment='写入IOPS')
    await_time = db.Column(db.Float, comment='平均等待时间(ms)')
    svctm = db.Column(db.Float, comment='服务时间(ms)')
    util = db.Column(db.Float, comment='利用率(%)')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 索引
    __table_args__ = (
        db.Index('idx_test_log_id', 'test_log_id'),
        db.Index('idx_collection_time', 'collection_time'),
        db.Index('idx_device', 'device'),
    )
    
    def __repr__(self):
        return f'<IOStatMetric {self.device} - {self.collection_time}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'test_log_id': self.test_log_id,
            'collection_time': self.collection_time.isoformat(),
            'device': self.device,
            'read_kbps': self.read_kbps,
            'write_kbps': self.write_kbps,
            'read_iops': self.read_iops,
            'write_iops': self.write_iops,
            'await_time': self.await_time,
            'svctm': self.svctm,
            'util': self.util,
            'created_at': self.created_at.isoformat(),
        }
    
    @classmethod
    def get_by_log(cls, test_log_id):
        """根据日志ID获取指标"""
        return cls.query.filter_by(test_log_id=test_log_id).order_by(cls.collection_time).all()
    
    @classmethod
    def get_by_time_range(cls, test_log_id, start_time, end_time):
        """根据时间范围获取指标"""
        return cls.query.filter(
            cls.test_log_id == test_log_id,
            cls.collection_time >= start_time,
            cls.collection_time <= end_time
        ).order_by(cls.collection_time).all()


class IOPerformanceData(db.Model):
    """IO性能数据模型 - 存储实时性能数据"""
    
    __tablename__ = 'io_performance_data'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='数据ID')
    test_task_id = db.Column(db.Integer, db.ForeignKey('test_tasks.id'), nullable=False, comment='任务ID')
    node_id = db.Column(db.Integer, db.ForeignKey('nodes.id'), nullable=False, comment='节点ID')
    io_test_case_id = db.Column(db.Integer, db.ForeignKey('io_test_cases.id'), nullable=False, comment='IO测试用例ID')
    task_execution_id = db.Column(db.Integer, db.ForeignKey('task_executions.id'), nullable=False, comment='执行ID')
    read_iops = db.Column(db.Float, comment='读取IOPS')
    write_iops = db.Column(db.Float, comment='写入IOPS')
    read_kbps = db.Column(db.Float, comment='读取速度(KB/s)')
    write_kbps = db.Column(db.Float, comment='写入速度(KB/s)')
    await_time = db.Column(db.Float, comment='平均等待时间(ms)')
    svctm = db.Column(db.Float, comment='服务时间(ms)')
    util = db.Column(db.Float, comment='利用率(%)')
    lat_p99 = db.Column(db.Float, comment='P99延迟(ms)')
    lat_p9999 = db.Column(db.Float, comment='P9999延迟(ms)')
    lat_max = db.Column(db.Float, comment='最大延迟(ms)')
    io_model_name = db.Column(db.String(255), comment='IO模型名称')
    device = db.Column(db.String(100), comment='设备名称')
    io_start_time = db.Column(db.DateTime, comment='IO开始时间')
    io_end_time = db.Column(db.DateTime, comment='IO结束时间')
    collection_time = db.Column(db.DateTime, default=datetime.utcnow, comment='采集时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 索引
    __table_args__ = (
        db.Index('idx_test_task_id', 'test_task_id'),
        db.Index('idx_node_id', 'node_id'),
        db.Index('idx_io_test_case_id', 'io_test_case_id'),
        db.Index('idx_task_execution_id', 'task_execution_id'),
        db.Index('idx_collection_time', 'collection_time'),
        db.Index('idx_io_model_name', 'io_model_name'),
        db.Index('idx_device', 'device'),
    )
    
    def __repr__(self):
        return f'<IOPerformanceData {self.io_model_name} - {self.device}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'test_task_id': self.test_task_id,
            'node_id': self.node_id,
            'io_test_case_id': self.io_test_case_id,
            'task_execution_id': self.task_execution_id,
            'read_iops': self.read_iops,
            'write_iops': self.write_iops,
            'read_kbps': self.read_kbps,
            'write_kbps': self.write_kbps,
            'await_time': self.await_time,
            'svctm': self.svctm,
            'util': self.util,
            'lat_p99': self.lat_p99,
            'lat_p9999': self.lat_p9999,
            'lat_max': self.lat_max,
            'io_model_name': self.io_model_name,
            'device': self.device,
            'io_start_time': self.io_start_time.isoformat() if self.io_start_time else None,
            'io_end_time': self.io_end_time.isoformat() if self.io_end_time else None,
            'collection_time': self.collection_time.isoformat(),
            'created_at': self.created_at.isoformat(),
        }
    
    @classmethod
    def get_by_task(cls, test_task_id):
        """根据任务ID获取性能数据"""
        return cls.query.filter_by(test_task_id=test_task_id).order_by(cls.collection_time).all()
    
    @classmethod
    def get_by_node_and_task(cls, node_id, test_task_id):
        """根据节点ID和任务ID获取性能数据"""
        return cls.query.filter_by(node_id=node_id, test_task_id=test_task_id).order_by(cls.collection_time).all()
    
    @classmethod
    def get_by_device_and_task(cls, device, test_task_id):
        """根据设备和任务ID获取性能数据"""
        return cls.query.filter_by(device=device, test_task_id=test_task_id).order_by(cls.collection_time).all()
    
    @classmethod
    def get_by_task_and_node_and_device(cls, test_task_id, node_id_list=None, device_list=None):
        """根据任务ID、节点列表和设备列表获取性能数据"""
        query = cls.query.filter_by(test_task_id=test_task_id)
        
        if node_id_list:
            query = query.filter(cls.node_id.in_(node_id_list))
        
        if device_list:
            query = query.filter(cls.device.in_(device_list))
        
        return query.order_by(cls.collection_time).all()