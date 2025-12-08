# IO性能测试平台

一个功能完整的IO性能测试平台，采用现代化的前后端分离架构，支持fio和vdbench两种主流IO测试工具，为企业提供专业、高效、可靠的存储性能测试解决方案。

## 🚀 项目特色

### 核心功能
- ✅ **双测试引擎**: 支持fio和vdbench两种主流IO测试工具
- ✅ **分布式测试**: 多节点、多分区并发性能测试
- ✅ **实时监控**: 实时性能数据监控和可视化展示
- ✅ **智能分析**: 多维度性能数据分析和报告生成
- ✅ **权限管理**: 完善的用户权限管理体系
- ✅ **任务空间**: 项目化任务管理和分类

### 技术优势
- 🏗️ **前后端分离**: Vue.js 3 + Flask现代化架构
- 🔒 **安全可靠**: JWT认证、数据加密、权限控制
- 📊 **数据可视化**: ECharts图表库，丰富的数据展示
- 🐳 **易于部署**: Docker容器化部署支持
- 📈 **高性能**: 优化的数据库设计和查询性能
- 🔧 **可扩展**: 模块化设计，支持功能扩展

## 📁 项目结构

```
IO性能测试平台/
├── 📋 技术文档/
│   ├── IO性能测试平台技术方案.md      # 完整技术方案
│   ├── 数据库设计方案.md              # 数据库详细设计
│   ├── 部署指南.md                    # 部署和配置指南
│   ├── 用户使用手册.md                # 用户使用指南
│   └── 项目总结.md                    # 项目总结报告
│
├── 🎨 前端原型/
│   └── frontend/                      # Vue.js前端项目
│       ├── src/
│       │   ├── components/            # Vue组件
│       │   ├── views/                 # 页面视图
│       │   ├── router/                # 路由配置
│       │   ├── store/                 # 状态管理
│       │   ├── api/                   # API接口
│       │   ├── utils/                 # 工具函数
│       │   └── assets/                # 静态资源
│       ├── package.json               # 项目依赖
│       └── vue.config.js              # Vue配置
│
├── ⚙️ 后端框架/
│   └── backend/                       # Flask后端项目
│       ├── app/
│       │   ├── models/                # 数据库模型
│       │   ├── views/                 # 视图函数
│       │   ├── utils/                 # 工具类
│       │   └── services/              # 业务服务
│       ├── config.py                  # 配置文件
│       ├── app.py                     # 主应用文件
│       └── requirements.txt           # Python依赖
│
├── 🏗️ 架构图表/
│   ├── system_architecture.png        # 系统架构图
│   ├── data_flow_diagram.png          # 数据流图
│   └── database_schema.png            # 数据库ER图
│
└── 📚 文档资料/
    └── README.md                      # 项目说明
```

## 🛠️ 技术栈

### 前端技术
- **Vue.js 3**: 渐进式JavaScript框架
- **Element Plus**: 基于Vue 3的组件库
- **ECharts**: 功能强大的图表库
- **Pinia**: Vue状态管理库
- **Vue Router**: Vue.js官方路由管理器

### 后端技术
- **Flask**: 轻量级Python Web框架
- **SQLAlchemy**: Python SQL工具包和ORM
- **Flask-JWT-Extended**: JWT认证扩展
- **Celery**: 分布式任务队列
- **Redis**: 内存数据结构存储

### 数据库技术
- **MySQL 8.0**: 关系型数据库管理系统
- **Redis**: 缓存和消息队列

### 部署技术
- **Docker**: 容器化平台
- **Docker Compose**: 多容器编排工具
- **Nginx**: 高性能Web服务器

## 📊 功能模块

### 1. 用户管理系统
- 用户注册、登录、认证
- 基于角色的权限控制（RBAC）
- 个人设置和密码管理
- 管理员用户管理功能

### 2. 登录信息管理
- SSH连接配置和管理
- 密码和密钥认证支持
- 连接测试和状态监控
- 安全的信息存储和加密

### 3. 节点分区管理
- 测试节点信息配置
- 分区列表管理
- 节点状态监控
- 系统资源使用情况监控

### 4. IO用例管理
- fio测试用例配置
- vdbench测试用例配置
- 用例模板和预设
- 参数验证和提示

### 5. 任务管理系统
- 测试任务创建和管理
- 任务执行和监控
- 实时进度跟踪
- 任务结果收集

### 6. 结果分析系统
- 多维度性能指标展示
- 实时数据可视化
- 历史数据对比分析
- 图表和报告生成

### 7. 任务空间管理
- 任务分类和项目管理
- 空间成员管理
- 资源配额控制
- 权限隔离

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 14+
- MySQL 8.0+
- Redis 6.0+

### 开发环境部署

1. **克隆项目**
```bash
git clone https://github.com/your-org/io-performance-platform.git
cd io-performance-platform
```

2. **部署后端**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

pip install -r requirements.txt
flask run --debug
```

3. **部署前端**
```bash
cd frontend
npm install
npm run serve
```

### 生产环境部署

推荐使用Docker部署：

```bash
# 使用Docker Compose一键部署
docker-compose up -d

# 访问应用
# 前端: http://localhost
# 后端API: http://localhost:5000/api
```

详细部署说明请参考 [部署指南.md](部署指南.md)。

## 📈 性能指标

### 支持的测试类型
- **顺序读/写测试**: 评估顺序IO性能
- **随机读/写测试**: 评估随机IO性能
- **混合读写测试**: 模拟真实应用场景
- **压力测试**: 系统极限性能测试
- **延迟测试**: IO延迟性能评估

### 监控指标
- **IOPS**: 每秒IO操作数
- **带宽**: 数据传输速率（MB/s）
- **延迟**: IO操作响应时间（ms）
- **CPU使用率**: 系统CPU负载
- **内存使用率**: 系统内存使用
- **磁盘使用率**: 存储空间使用

## 🔐 安全特性

- **身份认证**: JWT令牌认证
- **权限控制**: 基于角色的访问控制（RBAC）
- **数据加密**: 敏感信息加密存储
- **输入验证**: 严格的参数验证和过滤
- **SQL注入防护**: 参数化查询
- **XSS防护**: 内容安全策略

## 📊 系统监控

- **服务状态监控**: 实时服务健康检查
- **性能指标监控**: 系统性能数据收集
- **日志管理**: 集中式日志收集和分析
- **告警机制**: 异常情况自动告警

## 📚 文档资料

- **[技术方案](IO性能测试平台技术方案.md)**: 详细的技术架构和设计方案
- **[数据库设计](数据库设计方案.md)**: 数据库表结构和关系设计
- **[部署指南](部署指南.md)**: 完整的部署和配置说明
- **[用户手册](用户使用手册.md)**: 详细的使用指南和最佳实践
- **[项目总结](项目总结.md)**: 项目成果和技术总结

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

### 开发规范
- 遵循PEP 8 Python编码规范
- 使用TypeScript进行前端开发
- 编写单元测试和集成测试
- 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和用户！

## 📞 联系我们

- **技术支持**: support@io-platform.com
- **项目主页**: https://io-platform.com
- **问题反馈**: https://github.com/your-org/io-performance-platform/issues

---

**IO性能测试平台** - 专业的存储性能测试解决方案 🚀