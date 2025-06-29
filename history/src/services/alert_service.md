由于引入了**严重等级 (Severity)** 这个核心概念，并期望它在UI中得到高亮和在通知中进行智能过滤，我们向服务器发送的JSON数据格式确实应该更新。

---

### **当前服务器支持的消息格式**

目前，您的服务器（`alert_receiver.py` 中的 Flask 服务）可以接收以下两种格式的消息：

#### **1. 旧格式 (向后兼容)**

这是最原始的格式，它**没有包含 `severity` 字段**。
*   **服务器处理:** 如果没有 `severity` 字段，服务器会**默认**将其视为 `INFO` 级别。

```json
{
    "type": "System Alert",
    "message": "CPU usage exceeds 90% on server 'WEB-01'."
}
```

#### **2. 新格式 (推荐使用)**

这是推荐的格式，它**包含 `severity` 字段**，允许发送方明确指定告警的严重等级。

*   **`severity` 可选值:** "INFO", "WARNING", "CRITICAL"。
*   **服务器处理:** 服务器会直接使用此字段的值。如果值为我们系统不认识的（如 "UNKNOWN"），也会默认处理为 `INFO`。

```json
{
    "type": "Database Error",
    "message": "Failed to connect to primary DB instance.",
    "severity": "CRITICAL"
}
```

---

### **更新后的测试与发送消息说明**

为了充分测试我们应用程序的所有功能（UI高亮、智能通知、历史记录中的等级显示等），您应该使用包含 `severity` 字段的**新格式**。

以下是更新后的说明，包括 `curl` 示例：

---

**更新后的说明：向服务器发送告警消息**

您的“桌面控制与监控中心”应用程序现在支持接收带有**严重等级**的告警消息。请使用以下格式通过HTTP POST请求发送JSON数据。

*   **URL:** `http://127.0.0.1:5000/alert`
*   **Method:** `POST`
*   **Content-Type:** `application/json`

---

### **推荐的 Body (JSON) 格式**

请在JSON中包含 `severity` 字段，以明确告警的严重等级。

```json
{
    "type": "Your Alert Type",          // 告警类型，例如 "Disk Space", "Login Attempt"
    "message": "Detailed alert message",// 详细的告警内容
    "severity": "CRITICAL"              // 【关键】严重等级，可选值: "INFO", "WARNING", "CRITICAL"
}
```

---

### **使用 `curl` 的示例**

以下是不同 `severity` 等级的 `curl` 示例，推荐在 **Git Bash 或 PowerShell** 中执行（单引号包裹JSON字符串，避免转义问题）。如果必须在**Windows CMD**中执行，请记得对内部的双引号进行转义 (`\"`)。

#### **示例 1: 发送 `CRITICAL` 告警**

（预期：UI表格红色高亮，桌面通知弹窗，日志记录 `CRITICAL`）

**Git Bash / PowerShell:**
```bash
curl -X POST -H "Content-Type: application/json" -d '{"type": "Database Down", "message": "核心数据库集群离线，服务中断！", "severity": "CRITICAL"}' http://127.0.0.1:5000/alert
```

#### **示例 2: 发送 `WARNING` 告警**

（预期：UI表格黄色高亮，桌面通知弹窗，日志记录 `WARNING`）

**Git Bash / PowerShell:**
```bash
curl -X POST -H "Content-Type: application/json" -d '{"type": "CPU Usage", "message": "WEB服务器CPU利用率持续高于85%！", "severity": "WARNING"}' http://127.0.0.1:5000/alert
```

#### **示例 3: 发送 `INFO` 告警**

（预期：UI表格默认白色背景，**通常不会弹窗**（取决于您的设置），日志记录 `INFO`）

**Git Bash / PowerShell:**
```bash
curl -X POST -H "Content-Type: application/json" -d '{"type": "User Activity", "message": "用户'admin'从新IP登录。", "severity": "INFO"}' http://127.0.0.1:5000/alert
```

#### **示例 4: 发送不带 `severity` 的旧格式告警 (兼容性测试)**

（预期：UI表格默认白色背景，**不会弹窗**，日志记录 `INFO`）

**Git Bash / PowerShell:**
```bash
curl -X POST -H "Content-Type: application/json" -d '{"type": "System Reboot", "message": "服务器'APP-03'已完成重启。"}' http://127.0.0.1:5000/alert
```
---
# 示例 1: 发送 CRITICAL 告警 (强制UTF-8，通过echo和管道)
echo '{"type": "Database Down", "message": "核心数据库集群离线，服务中断！", "severity": "CRITICAL"}' | \
curl -X POST -H "Content-Type: application/json; charset=utf-8" --data-binary @- http://127.0.0.1:5000/alert

# 示例 2: 发送 WARNING 告警 (强制UTF-8，通过echo和管道)
echo '{"type": "CPU Usage", "message": "WEB服务器CPU利用率持续高于85%！", "severity": "WARNING"}' | \
curl -X POST -H "Content-Type: application/json; charset=utf-8" --data-binary @- http://127.0.0.1:5000/alert

# 示例 3: 发送 INFO 告警 (强制UTF-8，通过echo和管道)
echo '{"type": "User Activity", "message": "用户admin从新IP登录。", "severity": "INFO"}' | \
curl -X POST -H "Content-Type: application/json; charset=utf-8" --data-binary @- http://127.0.0.1:5000/alert

# 示例 4: 发送不带 severity 的旧格式告警 (强制UTF-8，通过echo和管道)
echo '{"type": "System Reboot", "message": "服务器APP-03已完成重启。"}' | \
curl -X POST -H "Content-Type: application/json; charset=utf-8" --data-binary @- http://127.0.0.1:5000/alert


cmd:
curl -X POST -H "Content-Type: application/json" -d "{\"type\": \"Disk Space\", \"message\": \"/var分区使用率已超过90%\", \"severity\": \"WARNING\"}" http://127.0.0.1:5000/alert
curl -X POST -H "Content-Type: application/json" -d "{\"type\": \"System Update\", \"message\": \"A new update is available.\", \"severity\": \"NOTICE\"}" http://127.0.0.1:5000/alert


使用这些新的 `curl` 命令，您可以更全面地测试我们应用程序的告警接收、存储、显示和通知功能，并验证所有UI美化和智能逻辑是否按预期工作。