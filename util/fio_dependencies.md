# FIO依赖包整理

## 1. 核心依赖说明

FIO (Flexible I/O Tester) 是一个强大的IO测试工具，用于评估存储系统的性能。以下是不同架构和Linux发行版下安装FIO所需的依赖包。

## 2. x86架构依赖包

### 2.1 Debian/Ubuntu系统

**安装命令**：
```bash
# 更新软件包列表
sudo apt-get update

# 安装编译依赖
sudo apt-get install -y build-essential libaio-dev libc6-dev libgcc1 libnuma-dev libssl-dev libz-dev pkg-config

# 安装fio（如果直接使用预编译版本）
sudo apt-get install -y fio
```

**核心依赖包说明**：
- `build-essential`: 包含gcc、g++、make等编译工具
- `libaio-dev`: 异步IO支持
- `libc6-dev`: C语言标准库
- `libgcc1`: GCC运行时库
- `libnuma-dev`: NUMA（非统一内存访问）支持
- `libssl-dev`: SSL/TLS加密支持
- `libz-dev`: Zlib压缩库支持
- `pkg-config`: 管理编译选项的工具

### 2.2 RHEL/CentOS系统

**安装命令**：
```bash
# 安装编译依赖
sudo yum install -y gcc gcc-c++ make libaio-devel numactl-devel openssl-devel zlib-devel

# 安装fio（如果直接使用预编译版本）
sudo yum install -y fio
```

**核心依赖包说明**：
- `gcc`: C编译器
- `gcc-c++`: C++编译器
- `make`: 构建工具
- `libaio-devel`: 异步IO支持
- `numactl-devel`: NUMA支持
- `openssl-devel`: SSL/TLS加密支持
- `zlib-devel`: Zlib压缩库支持

## 3. ARM架构依赖包

### 3.1 Debian/Ubuntu系统（ARM64/AArch64）

**安装命令**：
```bash
# 更新软件包列表
sudo apt-get update

# 安装编译依赖
sudo apt-get install -y build-essential libaio-dev libc6-dev libgcc1 libnuma-dev libssl-dev libz-dev pkg-config

# 安装fio（如果直接使用预编译版本）
sudo apt-get install -y fio
```

### 3.2 RHEL/CentOS系统（ARM64/AArch64）

**安装命令**：
```bash
# 安装编译依赖
sudo yum install -y gcc gcc-c++ make libaio-devel numactl-devel openssl-devel zlib-devel

# 安装fio（如果直接使用预编译版本）
sudo yum install -y fio
```

### 3.3 交叉编译ARM版本（在x86机器上编译ARM版本）

**安装命令**：
```bash
# Debian/Ubuntu系统
sudo apt-get install -y gcc-arm-linux-gnueabi g++-arm-linux-gnueabi libc6-armel-cross libaio-dev:armel libssl-dev:armel libz-dev:armel

# RHEL/CentOS系统
sudo yum install -y gcc-arm-linux-gnu g++-arm-linux-gnu
```

## 4. 编译安装FIO

如果需要从源码编译FIO，可以使用以下命令：

```bash
# 下载FIO源码
wget https://github.com/axboe/fio/archive/refs/tags/fio-3.36.tar.gz

# 解压源码
tar -xf fio-3.36.tar.gz
cd fio-fio-3.36

# 编译（针对当前架构）
make

# 安装
sudo make install
```

## 5. 验证FIO安装

安装完成后，可以使用以下命令验证FIO是否正常工作：

```bash
# 查看FIO版本
fio --version

# 运行简单的测试
fio --name=test --ioengine=libaio --rw=read --bs=4k --size=1G --numjobs=1 --runtime=60 --group_reporting
```

## 6. 架构特定注意事项

### 6.1 x86架构
- 支持所有FIO功能
- 性能优化较好
- 兼容几乎所有Linux发行版

### 6.2 ARM架构
- ARM64/AArch64支持完整的FIO功能
- 旧版ARM32架构可能存在一些限制
- 某些高级功能可能需要特定的硬件支持

## 7. 依赖包版本兼容性

| 依赖包 | 最低版本要求 | 推荐版本 |
|--------|--------------|----------|
| gcc | 4.8 | 7.0+ |
| libaio | 0.3.110 | 0.3.112+ |
| libssl | 1.0.0 | 1.1.1+ |
| libz | 1.2.0 | 1.2.11+ |

## 8. 常见问题与解决方案

1. **编译失败：找不到libaio.h**
   - 解决方案：安装libaio-dev或libaio-devel

2. **运行时错误：libaio.so.1: cannot open shared object file**
   - 解决方案：安装libaio1或libaio

3. **NUMA支持缺失**
   - 解决方案：安装libnuma-dev或numactl-devel，或使用`--disable-numa`编译选项

4. **交叉编译失败**
   - 解决方案：确保安装了正确的交叉编译工具链，设置正确的CC环境变量

## 9. 自动化安装脚本

以下是一个自动化安装FIO的脚本，支持x86和ARM架构：

```bash
#!/bin/bash

# 检测系统架构
ARCH=$(uname -m)
echo "检测到系统架构: $ARCH"

# 检测Linux发行版
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu
    echo "检测到Debian/Ubuntu系统"
    sudo apt-get update
    sudo apt-get install -y build-essential libaio-dev libnuma-dev libssl-dev libz-dev pkg-config fio
elif [ -f /etc/redhat-release ]; then
    # RHEL/CentOS
    echo "检测到RHEL/CentOS系统"
    sudo yum install -y gcc gcc-c++ make libaio-devel numactl-devel openssl-devel zlib-devel fio
else
    echo "不支持的Linux发行版"
    exit 1
fi

# 验证安装
echo "验证FIO安装..."
fio --version

echo "FIO安装完成！"
```

将上述脚本保存为`install_fio.sh`，然后执行：
```bash
chmod +x install_fio.sh
./install_fio.sh
```

## 10. 参考链接

- [FIO官方网站](https://fio.readthedocs.io/)
- [FIO GitHub仓库](https://github.com/axboe/fio)
- [Linux内核异步IO文档](https://www.kernel.org/doc/html/latest/block/asynchronous-io.html)
- [NUMA架构介绍](https://www.kernel.org/doc/html/latest/admin-guide/mm/numa.html)