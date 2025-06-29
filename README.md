## 项目新架构
desktop_center/
└── src/
    ├── core/                   # 【新增】平台核心代码
    │   ├── __init__.py
    │   ├── context.py
    │   ├── plugin_interface.py
    │   └── plugin_manager.py
    │
    ├── features/               # 【新增】所有功能插件的家
    │   ├── __init__.py         # (必须有，让其成为一个包)
    │   │
    │   └── alert_center/       # 【插件一】告警中心
    │       ├── __init__.py     # (必须有，让其成为一个包)
    │       ├── plugin.py       # 【核心】告警中心插件的实现
    │       ├── alerts_page.py  # (页面视图)
    │       ├── alert_receiver.py # (此插件独有的后台服务)
    │       ├── history_dialog.py # (此插件独有的对话框)
    │       └── statistics_dialog.py
    │
    │   └── process_sorter/     # 【插件二】未来新增的进程排序器
    │       ├── __init__.py
    │       ├── plugin.py
    │       ├── sorter_page.py
    │       └── process_monitor_thread.py
    │
    ├── services/               # 【共享服务】
    │   ├── config_service.py   # (被所有插件共享)
    │   └── database_service.py # (被需要数据库的插件共享)
    │
    ├── ui/                     # 【平台级UI和共享组件】
    │   ├── main_window.py      # (UI外壳)
    │   ├── action_manager.py
    │   └── widgets/            # (可复用的小组件)
    │
    └── utils/                  # 【平台级工具】
        └── tray_manager.py
## 这个新架构的优势
- 终极解耦: “告警中心”和未来的“进程排序器”完全不知道对方的存在。它们只与平台核心的接口和上下文交互。
- 可扩展性极强:
    添加新功能: 只需在 src/features/ 目录下创建一个新文件夹，实现 IFeaturePlugin 接口，应用重启后就会自动加载，无需修改任何核心代码。
    扩展子功能: 在插件内部，你依然可以沿用MVC等模式来组织代码，保持子功能的清晰。
- 职责清晰:
src/core: 定义游戏规则。
src/features: 玩家。
app.py: 游戏裁判和场地。
src/services: 公共设施。
- 利于团队协作: 不同的开发者可以并行开发不同的插件，只要都遵守 IFeaturePlugin 接口，就不会互相干扰。
- 按需加载: 平台可以被配置为只加载某些插件，实现不同版本（基础版/专业版）的软件分发。
