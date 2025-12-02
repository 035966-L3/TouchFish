# TouchFish - 局域网聊天解决方案

> [!WARNING]
> **TouchFish 正在更新到 V4 版本，自 V4 后不再向后兼容**
> [前往 v4](https://github.com/035966-L3/TouchFish) 


[官网 - BOPID](http://bopid.cn/chat)\
[官方帮助 - 2044-space-elevator & pztsdy](https://github.com/2044-space-elevator/TouchFish/wiki)\
[官方帮助服务端镜像](https://www.piaoztsdy.cn/2025/10/05/TouchFish-%E5%B8%AE%E5%8A%A9/) ||
[官方帮助管理员端镜像](https://www.piaoztsdy.cn/2025/10/05/TouchFish-Admin-%E5%B8%AE%E5%8A%A9/) - pztsdy\
[网站和文档 - ILoveScratch](http://tf.ilovescratch.dpdns.org)\
[TouchFish 101 文档 - Notion](http://touchfish-dev.notion.site/touchfish-101)

> **重要通知：贡献者须知**
> 
> 感谢您对 TouchFish 项目的关注和贡献！为避免您的努力付诸东流，请在提交 PR 前务必仔细阅读
> **[贡献者指南](https://github.com/2044-space-elevator/TouchFish/blob/main/CONTRIBUTING.md)**，
> 确保您的贡献符合项目规范。感谢您的配合！

**汪氏军工制作 | 作者 Luogu UID: 824363**

## 项目简介

TouchFish 是一款专为局域网环境设计的聊天软件，支持文字和文件传输。即使在没有公网连接的情况下，也能提供稳定的通信服务，是机房、实验室等封闭网络环境的理想选择。

> **项目官网**: [bopid.cn](https://www.bopid.cn/chat)

## 下载方式

### 推荐镜像站点
**镜像站**: [https://mirror.ilovescratch.dpdns.org/](https://mirror.ilovescratch.dpdns.org/)

> **优势**: 下载速度快，网络连接稳定
> 
> **限制**: 仅提供稳定版本，无法下载 PR 分支和开发中版本

### 官方源
**GitHub**: [https://github.com/2044-space-elevator/TouchFish](https://github.com/2044-space-elevator/TouchFish)

> **优势**: 包含所有分支、PR 和最新开发版本
> 
> **限制**: 国内访问可能较慢

## 系统要求

### Windows
- **Windows 7 及以下系统用户**: 可能需要安装额外的 DLL 文件

### macOS
> [!WARNING]
> 需要启用"任何来源"应用运行权限：
> 系统设置 → 安全性与隐私 → 安全性 → 允许以下来源的应用程序 → 选择"任何来源"

### Linux
> [!WARNING]
> **这是 TouchFish v4 版本，自 v4 开始不再向前兼容 v1 - v3。**
>
> [返回 v3](https://github.com/2044-space-elevator/TouchFish) 

## 软件架构

TouchFish 采用客户端-服务器架构，包含三个核心组件：

- **Server（服务器端）**: 聊天网络的核心，同一网络内只需运行一个实例
- **Client（客户端）**: 普通用户聊天界面
  - *ClientCLI （命令行版客户端）*: 专为**无UI界面的Linux**设计的客户端
- **Admin（管理员端）**: 授予信任用户的管理权限

## 发行版本生态

TouchFish 拥有丰富的衍生版本生态系统，满足不同用户需求：

## 演示

> *注：标注星号的版本可能需要自行编译、直接运行代码或缺少预编译包*

## 相比于 v3 的变化

- 合并 Client 和 Server 为一个程序
- 仅提供命令行（GUI 等发行版）
- 更换协议

## 快速开始

### 作为服务端

1. **获取内网 IP 地址**：
   - **Windows**: 命令提示符执行 `ipconfig`，查找 "无线局域网适配器 WLAN" 下的 "IPv4 地址"
   - **Linux**: 终端执行 `ip a`

2. **检查端口可用性**：
   - **Windows**: `netstat -an | findstr <portid>`（无输出表示端口空闲）

3. **第一次启动服务器**：
   - 运行程序
   - 在 15 秒内按下 `Ctrl + C`
   - 指定启动方式
   - 输入内网 IP 地址
   - 指定可用端口
   - 设置服务端昵称（将在聊天室中显示）
   - 设置最大用户数（不超过正整数）
   - 将 IP 地址和端口信息分享给客户端用户

4. **后续启动服务器**：
   - 运行程序
   - 等待 15 秒
   - 程序将自动以上次的配置启动

### 作为客户端

1. **第一次启动程序**：
   - 运行程序
   - 在 15 秒内按下 `Ctrl + C`
   - 指定启动方式
   - 输入服务器 IP 地址
   - 输入服务器端口
   - 设置个人昵称（将在聊天室中显示）

2. **后续启动程序**：
   - 运行程序
   - 等待 15 秒
   - 程序将自动以上次的配置启动


