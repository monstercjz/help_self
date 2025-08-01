## 依赖
pygetwindow  # 新增：用于操作桌面窗口
Pillow       # 用于pystray图标管理
pip install psutil pywin32


## 标题：桌面窗口管理插件 - 参数设置使用说明书

### 适用范围：
*   Desktop Control & Monitoring Center 应用程序
*   桌面窗口管理 (Window Arranger) 插件

### 1. 插件概述

“桌面窗口管理”插件是 Desktop Control & Monitoring Center 应用程序的核心功能之一，旨在帮助用户高效地组织和管理桌面上的应用程序窗口。通过本插件，您可以：
*   根据预设条件（如窗口标题关键词、进程名）**检测**并**过滤**当前活跃的窗口。
*   根据多种策略（如标题排序、数字排序）对检测到的窗口进行**排序**。
*   将符合条件的窗口自动**排列**成整齐的网格布局或级联布局。
*   开启**自动监测**，使程序在后台持续维护窗口布局，确保桌面始终保持整洁有序。
*   支持将监测到的事件通过 **Webhook** 推送至外部系统进行集成。

本说明书将详细介绍如何配置插件的各项参数。

### 2. 如何访问设置

1.  启动 Desktop Control & Monitoring Center 应用程序。
2.  在主窗口左侧的导航栏中，点击 **“桌面窗口管理”** 选项卡。
3.  在“桌面窗口管理”页面右上方，点击 **“排列设置”** 按钮。
4.  将弹出一个新的对话框，您可以在其中配置所有与窗口排列和监测相关的参数。

### 3. 设置项详解

设置对话框将各项参数分为了几个逻辑组，方便您进行查找和配置。

#### 3.1. 通用设置

*   **排序方案**
    *   **说明**: 决定了在检测到窗口后，窗口列表以及自动重排时所遵循的排序规则。选择一个稳定的排序方式对确保布局的可预测性非常重要。
    *   **可选值**:
        *   `默认排序 (按标题)`: 按照窗口标题的字母顺序（不区分大小写）进行升序排列，然后按进程名升序。
        *   `按标题数字排序`: 尝试从窗口标题中提取数字（例如，“会话1”、“会话10”会被正确排序），然后按照这些数字进行升序排列。如果标题中没有数字，则排在最后。
    *   **默认值**: `默认排序 (按标题)`
    *   **注意事项**: 切换排序方案后，点击“检测桌面窗口”或重新启动自动监测，以应用新规则。

#### 3.2. 自动监测设置

*   **监控模式**
    *   **说明**: 决定了自动监测服务在后台运行时的核心行为。
    *   **可选值**:
        *   `模板化自动排列`: **严格按规则维护布局。** 服务会周期性地检查当前窗口集合。
            *   **如果窗口数量或构成发生变化（有新窗口加入或旧窗口消失）**：将触发一次全面的**强制重排**（根据“排序方案”和“网格排列参数”重新计算并应用布局）。
            *   **如果窗口集合不变但有窗口位置发生移位**：只会将移位的窗口**归位**到其在模板中应有的位置。
        *   `快照式位置锁定`: **仅恢复窗口到上次排列的位置。** 服务会在启动时记录当前所有窗口的实际位置（快照）。
            *   **如果被快照的窗口位置发生移位**：将其**恢复**到快照中的位置。
            *   **新窗口加入**：**完全忽略**新窗口，不会将其纳入管理。
            *   **被快照的窗口消失**：将其从监控列表中移除，不做额外处理。
    *   **默认值**: `模板化自动排列`
    *   **注意事项**: 选择合适的模式以匹配您的使用习惯。如果希望严格按规则管理，选择“模板化”。如果只希望防止窗口被意外移动，选择“快照式”。

*   **自动监测间隔**
    *   **说明**: 自动监测服务在每次检查窗口状态之间的等待时间（秒）。
    *   **范围**: 1 秒 到 300 秒 (5 分钟)
    *   **默认值**: `5 秒`
    *   **注意事项**: 间隔越短，监测越及时，但可能消耗更多系统资源。间隔越长，资源消耗越低，但窗口恢复/重排的延迟会增加。

#### 3.3. 布局目标

*   **目标屏幕**
    *   **说明**: 指定窗口排列（无论是手动还是自动重排）将作用于哪个显示器。当您拥有多个显示器时，这非常有用。
    *   **可选值**: 列出所有检测到的显示器，并显示其分辨率和是否为主屏幕（例如：“屏幕 1 (1920x1080) (主屏幕)”）。
    *   **默认值**: `屏幕 1 (主屏幕)`

#### 3.4. 网格排列参数 (仅在模板模式下的自动重排或手动网格排列时生效)

*   **排列方向**
    *   **说明**: 决定了窗口在网格中填充的顺序。
    *   **可选值**:
        *   `先排满行 (→)`: 窗口从左到右填充第一行，然后第二行，依此类推。
        *   `先排满列 (↓)`: 窗口从上到下填充第一列，然后第二列，依此类推。
    *   **默认值**: `先排满行 (→)`

*   **行数**
    *   **说明**: 网格布局的总行数。
    *   **范围**: 1 到 20
    *   **默认值**: `2`

*   **列数**
    *   **说明**: 网格布局的总列数。
    *   **范围**: 1 到 20
    *   **默认值**: `3`

*   **屏幕边距 (px)**
    *   **说明**: 窗口网格区域距离屏幕边缘的像素距离。您可以分别设置上、下、左、右的边距。正值表示向内缩进，负值表示向外扩展（可能导致部分窗口超出屏幕）。
    *   **范围**: -500 到 500
    *   **默认值**: `0`

*   **窗口间距 (px)**
    *   **说明**: 网格中相邻窗口之间的像素间距。您可以分别设置水平和垂直间距。
    *   **范围**: -100 到 100
    *   **默认值**: `水平: 10`, `垂直: 10`

#### 3.5. 级联排列参数 (仅在手动级联排列时生效)

*   **级联X偏移 (px)**
    *   **说明**: 在级联排列中，每个后续窗口相对于前一个窗口在X轴上的偏移量。
    *   **范围**: 0 到 100
    *   **默认值**: `30`

*   **级联Y偏移 (px)**
    *   **说明**: 在级联排列中，每个后续窗口相对于前一个窗口在Y轴上的偏移量。
    *   **范围**: 0 到 100
    *   **默认值**: `30`

#### 3.6. 视觉与交互

*   **排列动画延时**
    *   **说明**: 在进行窗口排列时，每个窗口移动到新位置之间的短暂延迟（毫秒）。较高的值会使排列过程看起来更平滑，但整体时间更长。
    *   **范围**: 0 毫秒 到 500 毫秒
    *   **默认值**: `50 毫秒`
    *   **注意事项**: 在自动监测的强制重排中，为了效率，此延时通常会被忽略（即视为0）。

*   **桌面操作通知**
    *   **说明**: 是否在桌面右下角显示操作通知（例如“窗口已移位”、“已成功排列”）。
    *   **可选值**: `启用`, `禁用`
    *   **默认值**: `启用`

#### 3.7. 外部集成 (Webhook 推送)

*   **Webhook 推送**
    *   **说明**: 是否将监测到的窗口事件以 Webhook (HTTP POST 请求) 的形式推送到指定的外部系统。这对于自动化集成非常有用。
    *   **可选值**: `启用`, `禁用`
    *   **默认值**: `禁用`
    *   **注意事项**: 启用此功能前，请确保您了解 Webhook 的工作原理，并配置好目标接收服务器。

*   **推送主机**
    *   **说明**: Webhook 请求的目标主机地址（例如 `127.0.0.1` 或 `your.server.com`）。
    *   **默认值**: 默认为空，将使用平台配置的“默认推送主机”（通常为 `127.0.0.1`）。

*   **推送端口**
    *   **说明**: Webhook 请求的目标端口号（例如 `5000` 或 `8080`）。
    *   **范围**: 1 到 65535
    *   **默认值**: 默认为空，将使用平台配置的“默认推送端口”（通常为 `5000`）。

*   **推送路径**
    *   **说明**: Webhook 请求的URL路径（例如 `/alert` 或 `/api/events`）。
    *   **默认值**: `/alert`
    *   **注意事项**: 完整的Webhook URL将是 `http://<推送主机>:<推送端口><推送路径>`。例如 `http://127.0.0.1:5000/alert`。

### 4. 保存与生效

1.  在您完成所有参数设置后，点击对话框右下角的 **“保存”** 按钮。
2.  点击 **“取消”** 按钮将放弃所有未保存的更改。
3.  **部分设置立即生效**: 大部分设置（如排序方案、排列参数、过滤条件）将在您点击“保存”后，下次执行“检测桌面窗口”或“启动自动监测”时立即生效。
4.  **部分设置需要重新启动应用程序才能完全生效**: 某些平台级别的设置（例如日志级别，如果未来添加）可能需要您完全重启应用程序才能生效。

### 5. 常见问题与提示

*   **“检测桌面窗口”是基础**: 无论您使用手动排列还是自动监测，都建议先点击“检测桌面窗口”按钮，以确保程序能正确识别到您想要管理的窗口，并在UI列表中查看结果。
*   **过滤条件的重要性**: 如果您没有设置任何窗口标题关键词或进程名称关键词，程序将无法检测到任何窗口。请确保至少填写一项有效的过滤条件。
*   **手动排列会停止自动监测**: 如果自动监测正在运行，而您手动点击了“网格排列”或“级联排列”按钮，自动监测服务将自动停止，以避免冲突。若要重新启用，请再次点击“启动自动监测”按钮。
*   **模式选择**: 仔细理解“模板化自动排列”和“快照式位置锁定”的区别，它们对应了两种截然不同的自动化需求。
*   **通知与日志**: 启用桌面通知和Webhook 推送，可以帮助您更好地了解后台监测服务的工作情况和任何异常。所有事件也会记录在应用程序的日志文件 `app.log` 中。

---