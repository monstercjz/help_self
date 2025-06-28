## 项目结构
desktop_center/
├── app.py                     # 【主入口】程序启动脚本
├── config.ini                 # 配置文件
├── icon.png                   # 图标文件
|
└── src/                       # 【核心源码包】
    ├── __init__.py            # 将src声明为一个包
    |
    ├── services/              # 存放所有后台服务逻辑
    |   ├── __init__.py
    |   ├── config_service.py    # 配置服务模块
    |   └── alert_receiver.py    # 告警接收Web服务线程模块
    |
    ├── ui/                    # 存放所有UI相关的组件
    |   ├── __init__.py
    |   ├── main_window.py       # 主窗口框架
    |   ├── alerts_page.py       # “告警中心”页面
    |   ├── settings_page.py     # “设置”页面
    |   └── quick_launch_page.py # “快捷启动”占位页面
    |
    └── utils/                 # 存放通用工具或管理器
        ├── __init__.py
        └── tray_manager.py      # 系统托盘管理器