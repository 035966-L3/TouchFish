> [!WARNING]
> **这是 TouchFish v4 版本，自 v4 开始不再向前兼容 v1 - v3。**

# TouchFish - 局域网聊天解决方案

## 演示

请观看[此视频](https://www.bilibili.com/video/BV1qqSqB4E6x)以查看 v4 版本的用法。

该视频演示的程序为 beta 版本，与正式发行版有若干出入，敬请谅解。

## 相比于 v3 的变化

- 合并 Client 和 Server 为一个程序（`LTS.py`）
- 目前仅提供命令行（GUI 版本即将跟进）
- 更换协议（见 `protocol.txt` 或 [`协议文档`](README-protocol-document.md)）

## 快速开始

### 作为服务端

1. **获取内网 IP 地址**：
   - **Windows**: 命令提示符执行 `ipconfig`，查找 "无线局域网适配器 WLAN" 下的 "IPv4 地址"
   - **Linux**: 终端执行 `ip a`

2. **检查端口可用性**：
   - **Windows**: `netstat -an | findstr <portid>`（无输出表示端口空闲）

3. **第一次启动服务器**：
   - 运行程序
   - 在 5 秒内按下 `Ctrl + C`
   - 指定启动方式（`Server`）
   - 输入内网 IP 地址
   - 指定可用端口
   - 设置服务端昵称（将在聊天室中显示）
   - 设置最大用户数（不超过 128）
   - 将 IP 地址和端口信息分享给客户端用户

4. **后续启动服务器**：
   - 运行程序
   - 等待 5 秒
   - 程序将自动以上次的配置启动

### 作为客户端

1. **第一次启动程序**：
   - 运行程序
   - 在 5 秒内按下 `Ctrl + C`
   - 指定启动方式（`Client`）
   - 输入服务器 IP 地址
   - 输入服务器端口
   - 设置个人昵称（将在聊天室中显示）

2. **后续启动程序**：
   - 运行程序
   - 等待 5 秒
   - 程序将自动以上次的配置启动

## 系统要求

### Windows
- **Windows 7 及以下系统用户**：可能需要安装额外的 DLL 文件
- 部分 Windows 版本可能不支持 ASCII 转义显示文字，建议使用 Windows 10 及以上系统

### macOS
> [!WARNING]
> 需要启用 "任何来源" 应用运行权限：  
> 系统设置 → 安全性与隐私 → 安全性 → 允许以下来源的应用程序 → 选择 "任何来源"

### Linux
无特殊限制

---

以上是软件使用方法，以下是与软件生态等相关内容

---

## 发行版本生态

TouchFish 拥有丰富的衍生版本生态系统，满足不同用户需求：

**这里的大部分发行版都暂不支持 v4 版本，如需使用请前往 [Release](https://github.com/2044-space-elevator/TouchFish/releases) 页面下载旧版本**

| 版本名称 | 简称 | 主要作者 | 对v1-3支持 | 语言 | 平台支持 | 特色 | 对v4支持
|---------|------|----------|--|------|----------|------|--|
| LTS | TF | @2044-space-elevator, @035966-L3 | ✅ | Python | Win, macOS, Linux | 根版本，长期支持 | ✅ |
| UI Remake | TFUR | @pztsdy | ✅ | Node.JS | Win, macOS*, Linux* | 现代化 UI，Markdown，代码高亮（可能会停更） | ❌ |
| Plus | Plus | @ayf2192538031 | ❌ | Python | Win*, macOS*, Linux* | 增强功能集 | ❌ |
| Pro | Pro | @BoXueDuoCai | ✅ | Python | Win*, macOS*, Linux* | Markdown，LaTeX，用户高亮 | ❌ |
| Android | (已废除) | @pztsdy | ✅ | Kotlin | Android | 移动端（有使用限制）（已停更） | ❌ |
| Astra | TFA | @ILoveScratch2 | ✅ | Dart | 全平台(UI) | 最佳发行版之一，现代化 UI | ✅ |
| More | More | @xx2860 | ✅ | Python | Win*, macOS*, Linux(UI) | 性能优化，镜像站 | ❌^ |

> *注：*  
> 标 * 的版本可能需要自行编译、直接运行代码或缺少预编译包  
> 标 ^ 的内容因为不在 Github 内，所以数据可能会有差异现象
