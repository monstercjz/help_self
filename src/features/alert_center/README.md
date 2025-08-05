# 告警中心 (Alert Center) 插件

## 1. 概述

告警中心插件是 HelpSelf & Monitoring Center 的核心功能之一。它提供了一个后台HTTP服务，用于接收来自外部系统、脚本或应用程序的实时告警信息。所有接收到的告警都会被持久化存储，并在UI界面上实时展示，同时根据配置触发桌面通知。

该插件旨在成为一个集中的信息聚合点，帮助用户监控和响应各种外部事件。

## 2. 功能特性

- **后台HTTP监听**：内置一个轻量级的Flask Web服务，在指定端口监听HTTP POST请求。
- **实时信息展示**：在主界面的“告警中心”选项卡中，以表格形式实时展示接收到的每一条告警。
- **可配置的通知**：
    - 支持按严重等级（`INFO`, `WARNING`, `CRITICAL`）过滤通知。
    - 支持独立配置是否启用桌面弹窗及弹窗显示时长。
- **历史记录**：所有告警信息都会被存储在插件专属的SQLite数据库中，支持历史追溯。
- **数据统计与分析**：提供历史数据统计功能，帮助分析告警趋势（此功能由 `StatisticsDialog` 提供）。
- **独立的插件化设置**：所有配置项均可通过UI（操作 -> 插件设置）进行管理，与全局设置解耦。

## 3. 配置说明

本插件的所有配置项都位于 `config.ini` 文件的 `[alert_center]` 配置节下。

| 配置项                    | 类型    | 默认值          | 说明                                                                 |
| ------------------------- | ------- | --------------- | -------------------------------------------------------------------- |
| `host`                    | string  | `0.0.0.0`       | 后台HTTP服务监听的IP地址。`0.0.0.0` 表示监听所有网络接口。         |
| `port`                    | integer | `9527`          | 后台HTTP服务监听的端口号。请确保此端口未被其他程序占用。             |
| `enable_desktop_popup`    | boolean | `true`          | 是否为该插件的告警启用桌面弹窗通知。会覆盖全局通知设置。             |
| `popup_timeout`           | integer | `10`            | 桌面弹窗的显示时长（秒）。会覆盖全局通知设置。                       |
| `notification_level`      | string  | `WARNING`       | 触发桌面通知的最低严重等级。可选值：`INFO`, `WARNING`, `CRITICAL`。 |
| `load_history_on_startup` | integer | `100`           | 程序启动时，在UI上自动加载的最近历史记录条数。设置为 `0` 则不加载。 |
| `db_path`                 | string  | (自动生成)      | 插件专属数据库文件的路径。通常不需要手动修改。                       |

## 4. API 接口说明

插件通过一个HTTP端点接收告警。

- **URL**: `http://<host>:<port>/alert`
- **请求方法**: `POST`
- **Content-Type**: `application/json`

### JSON Body 格式

请求体必须是一个包含以下键的JSON对象。所有键都是可选的，如果缺失，系统将使用默认值。

| 键名       | 类型   | 是否必须 | 默认值                | 说明                                                               |
| ---------- | ------ | -------- | --------------------- | ------------------------------------------------------------------ |
| `severity` | string | 否       | `"INFO"`              | 严重等级。有效值：`"INFO"`, `"WARNING"`, `"CRITICAL"` (不区分大小写)。 |
| `type`     | string | 否       | `"Generic Alert"`     | 告警的类型或分类，用于UI展示。                                     |
| `message`  | string | 否       | `"No message provided."` | 告警的详细内容。                                                   |

**注意**：任何不属于以上三个键的自定义字段都将被忽略。

## 5. 使用示例

您可以使用任何能发送HTTP POST请求的工具来发送告警，例如 `curl`。

### 示例：发送一条“严重”等级的数据库备份失败告警

假设程序运行在本机，监听端口为默认的 `9527`。

```bash
curl -X POST http://127.0.0.1:9527/alert \
-H "Content-Type: application/json" \
-d '{
    "severity": "CRITICAL",
    "type": "Database Backup",
    "message": "Failed to backup database [prod_db] to remote storage. Connection timed out."
}'
```

### 示例：发送一条“信息”等级的常规任务完成通知

```bash
curl -X POST http://127.0.0.1:9527/alert \
-H "Content-Type: application/json" \
-d '{
    "severity": "INFO",
    "type": "Scheduled Task",
    "message": "Daily log cleanup task completed successfully."
}'
```

---

## 6. 架构与关键代码分析

本插件遵循了清晰的分层设计模式，以确保代码的高内聚、低耦合和可维护性。

### 6.1. 外部依赖

作为插件，`alert_center` 并不完全独立工作，它依赖于平台提供的核心服务和基类。

#### 6.1.1. 共享核心服务 (通过 `context` 注入)

这些服务通过 `ApplicationContext` 对象在插件初始化时注入，供插件在运行时访问：

- **`ApplicationContext` (`context`)**: 这是最重要的依赖，作为所有其他核心服务的容器，插件通过它来访问整个应用程序的共享资源。

- **`ConfigService` (`context.config_service`)**: 用于安全地读取和写入 `config.ini` 配置文件。插件的所有配置（如监听端口、通知级别）都通过此服务进行持久化。

- **`NotificationService` (`context.notification_service`)**: 用于发送桌面弹窗通知。插件将所有通知请求委托给此服务，以保持应用程序范围内UI行为的一致性。

- **`DatabaseInitializerService` (`context.db_initializer`)**: 用于获取插件专属的数据库连接实例。插件通过此服务来保证数据库的隔离性、正确的初始化流程以及未来的数据迁移能力。

#### 6.1.2. 核心基类 (通过 `import` 继承/使用)

插件的某些组件会继承或直接使用平台提供的核心基类，以实现特定的功能或遵循统一的接口：

- **`SqlDataService` (`src.services.sqlite_base_service.SqlDataService`)**: 插件的数据库服务 [`alert_database_service.py`](services/alert_database_service.py) 继承自此基类，以提供统一的数据库操作接口和生命周期管理。

### 6.2. 分层架构 (MVC/MVP)

插件的核心代码被组织为三个主要层次：

- **视图 (View)**: 位于 `views/` 目录下。这些是纯UI组件（继承自 `QWidget` 或 `QDialog`），负责界面的展示。它们不包含任何业务逻辑，通过Qt的**信号（Signal）**与控制器通信。
  - *关键文件*: [`alerts_page_view.py`](views/alerts_page_view.py), [`settings_dialog_view.py`](views/settings_dialog_view.py)

- **控制器 (Controller)**: 位于 `controllers/` 目录下。控制器是视图和模型/服务之间的桥梁。它响应来自视图的信号（通过**槽/Slot**），执行业务逻辑，并调用服务来处理数据或执行后台任务。
  - *关键文件*: [`alerts_page_controller.py`](controllers/alerts_page_controller.py), [`settings_dialog_controller.py`](controllers/settings_dialog_controller.py)

- **服务 (Service)**: 位于 `services/` 目录下。服务层封装了具体的后台任务和数据持久化逻辑。
  - *关键文件*: [`alert_receiver.py`](services/alert_receiver.py) (后台HTTP服务), [`alert_database_service.py`](services/alert_database_service.py) (数据库操作)

### 6.3. 插件生命周期与初始化

插件的入口是 [`plugin.py`](plugin.py)。平台核心通过 `IFeaturePlugin` 接口管理插件。

- **`initialize(self, context)`**: 这是插件的“构造函数”。当应用程序启动时，平台会调用此方法。它负责创建所有必要的组件（控制器、服务），并将它们连接起来。
- **`shutdown(self)`**: 当应用程序关闭时，此方法被调用，用于安全地停止后台服务和释放资源。

### 6.4. 后台HTTP服务

为了在不阻塞UI的情况下接收网络请求，插件使用了 `QThread`。

- **[`AlertReceiverThread`](services/alert_receiver.py)**: 这个类继承自 `QThread`，在其 `run` 方法中启动一个独立的Flask Web服务。这种设计是Qt应用程序中处理长时间运行或阻塞任务（如网络监听）的标准模式。

### 6.5. 信号与槽 (Signal & Slot) 机制

这是Qt的核心机制，也是本插件中视图和控制器解耦的关键。

- **工作流程**:
  1. 在 **View** (`AlertsPageView`) 中定义一个信号，如 `settings_requested = Signal()`。
  2. 当用户在UI上执行某个操作时（如点击“设置”按钮），View会发射(`emit`)这个信号。
  3. 在 **Controller** (`AlertsPageController`) 中，将这个信号连接到一个方法（槽），如 `self.view.settings_requested.connect(self.show_settings_dialog)`。
  4. 当信号被发射时，连接的槽函数会自动被调用，从而执行相应的业务逻辑。

这种机制使得视图完全不需要知道“点击按钮后应该发生什么”，它只负责“通知”控制器发生了某件事。

### 6.6. 配置管理

- **`ConfigService`**: 插件不直接读写 `.ini` 文件，而是通过平台提供的共享 `context.config_service` 来进行。
- **插件专属设置**: 插件的所有配置都保存在 `[alert_center]` 节下。通过在创建控制器时传入 `plugin_name`，确保了所有组件都正确地读写自己的配置，避免了硬编码。
- **专属设置对话框**: [`SettingsDialogController`](controllers/settings_dialog_controller.py) 负责加载和保存 `[alert_center]` 的配置，实现了插件设置的完全内聚。