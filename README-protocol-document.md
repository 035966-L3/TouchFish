# TouchFish v4 协议文档

**注：本文档内容大部分由AI生成，可能会有漏洞或错误，具体请阅读[protocol.txt](protocol.txt)**

本协议分为三个部分，`Gate`，`Chat` 和 `Server`，协议均使用 json 格式进行发送。英文版和 json 代码块见 [protocol.txt](protocol.txt)。

---

# 1. Gate

这个部分是关于进入聊天室的请求、审核等操作的协议内容。

## 1.1 Request  

客户端首次连接时向服务器发送此消息，用于申请加入。  

- `type`: 固定为 `"GATE.REQUEST"`，标识消息类型。  
- `username`: 字符串，表示用户希望使用的用户名，必须非空。

## 1.2 Response  

服务器对 `Request` 的直接响应，告知客户端其请求的处理结果。  

- `type`: 固定为 `"GATE.RESPONSE"`。  
- `result`: 字符串，可能取值包括：  
  - `"Accepted"`：立即允许加入；  
  - `"Pending review"`：需人工审核；  
  - `"IP is banned"`：当前 IP 被封禁；  
  - `"Room is full"`：服务器用户数已达上限；  
  - `"Duplicate usernames"`：用户名已被使用；  
  - `"Username consists of banned words"`：用户名包含违禁词。

## 1.3 Review Result  

当请求状态为 `"Pending review"` 时，管理员审核完成后，服务器向该客户端发送此消息。  

- `type`: 固定为 `"GATE.REVIEW_RESULT"`。  
- `accepted`: 布尔值，`true` 表示审核通过，`false` 表示拒绝。  
- `operator`: 审核操作者信息对象：  
  - `username`: 操作者用户名；  
  - `uid`: 操作者的唯一用户 ID（非负整数）。

## 1.4 Incorrect Protocol  

当客户端发送的消息格式不符合协议规范时，服务器可返回此错误通知。  

- `type`: 固定为 `"GATE.INCORRECT_PROTOCOL"`。  
- `time`: 时间戳，精确到微秒，表示错误发生的时间。  
- `ip`: 字符串，格式为 `IPv4地址:端口号`，表示违规客户端的网络地址。

## 1.5 Client Request  

客户端主动发起的与 Gate 相关的请求。

### 1.5.1 Announce  

客户端在收到 `GATE.RESPONSE` 后，可向服务器广播自己的接入状态（主要用于同步或确认）。  

- `type`: 固定为 `"GATE.CLIENT_REQUEST.ANNOUNCE"`。  
- `username`: 用户名。  
- `uid`: 服务器分配给该用户的唯一 ID（非负整数）。  
- `result`: 与 `1.2 Response` 中的 `result` 含义相同，用于声明当前状态。

### 1.5.2 Log  

客户端可主动上报自身的连接日志，用于调试或审计。  

- `type`: 固定为 `"GATE.CLIENT_REQUEST.LOG"`。  
- `time`: 时间戳（微秒）。  
- `ip`: 客户端 IP 地址与端口（`IPv4:port`）。  
- `username`: 用户名。  
- `uid`: 用户唯一 ID。

## 1.6 Status Change  

用于修改用户在线状态或权限等级。

### 1.6.1 Request  

由管理员或系统发起的状态变更指令。  

- `type`: 固定为 `"GATE.STATUS_CHANGE.REQUEST"`。  
- `status`: 字符串，表示目标状态，取值包括：  
  - `"Rejected"`：拒绝接入；  
  - `"Kicked"`：被踢出；  
  - `"Offline"`：离线；  
  - `"Pending"`：等待审核；  
  - `"Online"`：在线；  
  - `"Admin"`：管理员；  
  - `"Root"`：超级管理员。  
- `uid`: 被操作用户的唯一 ID。

### 1.6.2 Announce  

服务器广播用户状态变更，通知所有相关客户端。  

- `type`: 固定为 `"GATE.STATUS_CHANGE.ANNOUNCE"`。  
- `status`: 新状态（同上）。  
- `uid`: 被变更状态的用户 ID。

### 1.6.3 Log  

记录状态变更事件的日志。  

- `type`: 固定为 `"GATE.STATUS_CHANGE.LOG"`。  
- `time`: 时间戳（微秒）。  
- `status`: 新状态。  
- `uid`: 被操作用户 ID。  
- `operator`: 操作者的用户 ID（非负整数）。

---

# 2. Chat

这个部分是关于在聊天室内收发消息、私聊等操作的协议内容。

## 2.1 Send  

客户端发送消息或文件。  

- `type`: 固定为 `"CHAT.SEND"`。  
- `filename`: 文件名。若发送的是普通文本消息，则为空字符串 `""`；若发送文件，则为原始文件名（如 `"report.pdf"`）。  
- `content`: 若为消息，为原始文本内容；若为文件，则为文件内容的 Base64 编码字符串。  
- `to`: 目标接收者：  
  - `-2`：广播给所有在线用户；  
  - `-1`：发送到公共聊天频道；  
  - 具体 `UID`：私聊指定用户。

## 2.2 Receive  

服务器将消息转发给接收方时使用。  

- `type`: 固定为 `"CHAT.RECEIVE"`。  
- `from`: 发送者的用户 ID。  
- `order`: 区分消息类型：  
  - `0` 表示普通文本消息；  
  - 非零（如 `1`）表示文件（通常用于前端区分渲染方式）。  
- `filename`: 同 `Send`，文件名（消息则为空）。  
- `content`: 消息内容（文件则为空字符串，因文件内容已在日志或传输中处理）。  
- `to`: 接收目标（规则同 `Send`）。

> 注：出于安全或性能考虑，`content` 在文件类型消息中通常留空，文件内容通过其他机制传输或在日志中记录。

## 2.3 Log  

服务器记录每条聊天活动的审计日志。  

- `type`: 固定为 `"CHAT.LOG"`。  
- `time`: 时间戳（微秒）。  
- `from`: 发送者 UID。  
- `order`: 同 `Receive`，用于区分消息/文件。  
- `filename`: 文件名（若为消息则为空）。  
- `content`: 若为文本消息，保存原始内容；若为文件，则为空字符串（不保存文件内容，仅记录元数据）。  
- `to`: 接收目标（`-2`, `-1` 或 UID）。

---

# 3. Server

这个部分是关于服务器管理和管理员控制的协议内容。

## 3.1 Start  

服务器启动时广播，包含初始状态。  

- `type`: 固定为 `"SERVER.START"`。  
- `time`: 启动时间戳（微秒）。  
- `server_version`: 字符串，表示服务器程序版本（如 `"v1.2.0"`）。  
- `config`: JSON 对象，包含当前运行时配置（如最大用户数、审核开关等）。

## 3.2 Stop  

服务器正常关闭时广播。  

- `type`: 固定为 `"SERVER.STOP"`。  
- `time`: 关闭时间戳（微秒）。

## 3.3 Data  

用于向新连接的客户端或需要同步状态的客户端提供完整上下文。  

- `type`: 固定为 `"SERVER.DATA"`。  
- `server_version`: 服务器版本。  
- `uid`: 请求此数据的客户端自身的用户 ID。  
- `config`: 当前服务器配置（JSON 对象）。  
- `users`: 用户列表，每个元素为：  
  - `username`: 用户名；  
  - `status`: 当前状态（同 Gate 中定义的状态值）。  
- `chat_history`: 公共聊天记录数组，每条记录包含：  
  - `time`: 发送时间；  
  - `from`: 发送者 UID；  
  - `content`: 消息文本；  
  - `to`: 仅包含 `to = -1`（公共）或 `to = -2`（广播）的消息，私聊消息不在此同步。

## 3.4 Config  

### 3.4.1 Post  

客户端（通常为管理员）请求修改某项配置。  

- `type`: 固定为 `"SERVER.CONFIG.POST"`。  
- `key`: 配置项名称（字符串，如 `"max_users"`）。  
- `value`: 配置值，类型任意（数字、字符串、布尔值、对象等）。

### 3.4.2 Change  

服务器确认配置已成功修改，并通知所有监听者。  

- `type`: 固定为 `"SERVER.CONFIG.CHANGE"`。  
- `key`: 被修改的配置项名称。  
- `value`: 新的配置值。  
- `operator`: 执行修改操作的用户 UID。

### 3.4.3 Save  

服务器将当前配置持久化保存到磁盘或数据库时触发。  

- `type`: 固定为 `"SERVER.CONFIG.SAVE"`。  
- `time`: 保存时间戳（微秒）。

### 3.4.4 Log  

记录每次配置变更的详细日志，用于审计。  

- `type`: 固定为 `"SERVER.CONFIG.LOG"`。  
- `time`: 变更时间戳（微秒）。  
- `key`: 配置项名称。  
- `value`: 修改后的值。  
- `operator`: 操作者 UID。
