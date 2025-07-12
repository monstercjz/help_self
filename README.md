## 项目新架构
pip freeze > requirements.txt
```bash
pyinstaller --onefile --windowed --icon=icon.ico HelpSelf.py --add-data "config.ini;." --add-data "icon.png;." --add-data "icon.ico;." --add-data "src;src" --collect-submodules src --hidden-import flask --hidden-import pandas --hidden-import uuid --hidden-import pygetwindow --hidden-import win32process --hidden-import plyer.platforms.win.notification --hidden-import ansi2html --hidden-import paramiko

```
desktop_center/
├── HelpSelf.py                     # 【平台核心】精简的应用协调器
├── config.ini
├── icon.png
├── requirements.txt
│
└── src/
    ├── __init__.py
    │
    ├── core/                   # 【新增】平台核心代码
    │   ├── __init__.py
    │   ├── context.py
    │   ├── plugin_interface.py
    │   └── plugin_manager.py
    │
    ├── features/               # 【新增】所有功能插件的家
    │   ├── __init__.py
    │   └── alert_center/       # 【插件一】告警中心
    │       ├── __init__.py
    │       ├── plugin.py       # 插件入口，连接所有组件
    │       │
    │       ├── models/         # 【新增】MVC中的Model (数据处理)
    │       │   ├── __init__.py
    │       │   ├── history_model.py
    │       │   └── statistics_model.py
    │       │
    │       ├── views/          # 【新增】MVC中的View (纯UI)
    │       │   ├── __init__.py
    │       │   ├── alerts_page_view.py
    │       │   ├── history_dialog_view.py
    │       │   └── statistics_dialog_view.py
    │       │
    │       ├── controllers/    # 【新增】MVC中的Controller (逻辑控制)
    │       │   ├── __init__.py
    │       │   ├── alerts_page_controller.py
    │       │   ├── history_controller.py
    │       │   └── statistics_controller.py
    │       │
    │       └── services/       # 【插件私有服务】
    │           ├── __init__.py
    │           └── alert_receiver.py
    │
    ├── services/               # 【共享服务】
    │   ├── __init__.py
    │   ├── config_service.py
    │   └── database_service.py
    │
    ├── ui/                     # 【平台级UI和共享组件】
    │   ├── __init__.py
    │   ├── main_window.py
    │   ├── action_manager.py
    │   └── settings_page.py
    │
    └── utils/                  # 【平台级工具】
        ├── __init__.py
        └── tray_manager.py
## 这个新架构的优势
- 终极解耦: “告警中心”和未来的“进程排序器”完全不知道对方的存在。它们只与平台核心的接口和上下文交互。
- 可扩展性极强:
    添加新功能: 只需在 src/features/ 目录下创建一个新文件夹，实现 IFeaturePlugin 接口，应用重启后就会自动加载，无需修改任何核心代码。
    扩展子功能: 在插件内部，你依然可以沿用MVC等模式来组织代码，保持子功能的清晰。
- 职责清晰:
src/core: 定义游戏规则。
src/features: 玩家。
HelpSelf.py: 游戏裁判和场地。
src/services: 公共设施。
- 利于团队协作: 不同的开发者可以并行开发不同的插件，只要都遵守 IFeaturePlugin 接口，就不会互相干扰。
- 按需加载: 平台可以被配置为只加载某些插件，实现不同版本（基础版/专业版）的软件分发。

## 启动流程
整个启动过程可以分为三个主要阶段：
平台核心初始化 (Platform Core Initialization): HelpSelf.py 负责创建应用程序实例、核心服务（配置、数据库）、核心UI（主窗口、托盘）以及最重要的“上下文”和“插件管理器”。
插件加载与初始化 (Plugin Loading & Initialization): plugin_manager.py 负责扫描 features 目录，动态加载所有插件，并调用每个插件的 initialize 方法。
插件内部组装 (Plugin Internal Assembly): 在插件的 initialize 方法中，插件负责组装自己的MVC（Model, View, Controller）组件，创建自己的后台服务，并将自己的功能连接到平台提供的接口上（如 ActionManager）。