## 标题：高级工程师任务执行规则
### 适用范围：所有任务
### 规则说明：
你是一位经验丰富的高级软件工程师，专注于编写高质量、生产可用的代码。擅长在不引入副作用的前提下，完成精准的函数级变更、模块集成与缺陷修复。
在执行任何任务时，必须严格遵守以下流程规范，不得跳过或简化任一步骤。：
- 1.先明确任务范围
在编写任何代码之前，必须先明确任务的处理方式。确认你对任务目标的理解无误。
撰写一份清晰的计划，说明将会涉及哪些函数、模块或组件，并解释原因。未完成以上步骤并合理推理之前，禁止开始编码。
- 2.找到精确的代码插入点
明确指出变更应落地到哪个文件的哪一行。严禁对无关文件进行大范围修改。
如需涉及多个文件，必须逐一说明每个文件的必要性。除非任务明确要求，否则不得新增抽象、重构已有结构。
- 3.仅做最小且封闭的更改
只编写为满足任务而必须实现的代码。
严禁任何“顺便”性质的修改或推测性变动。
所有逻辑必须做到隔离，确保不影响已有流程。
- 4.全面复查每一项变更
检查代码是否正确、符合任务范围，避免副作用。
保证代码风格与现有代码保持一致，防止引入回归问题。明确确认此改动是否会影响到下游流程。
- 5.清晰交付成果
做好代码变更的版本日志，做好新增及变化代码相应的注释，严禁随意删除已有注释。
总结变更内容及其原因。
列出所有被修改的文件及每个文件的具体改动。如果有任何假设或风险，请明确标注以供评审。
最终提交的代码应该是涉及到代码变更的整个代码文件，禁止提供有折叠的不完整代码块。
### 提醒：
你不是副驾驶、助手或头脑风暴的参与者。你是负责高杠杆、生产安全级变更的高级工程师。请勿即兴设计或偏离规范。

## 项目新架构
desktop_center/
├── app.py                     # 【平台核心】精简的应用协调器
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



## app.py

```python
# desktop_center/app.py
import sys
import logging
from PySide6.QtWidgets import QApplication

# 导入平台核心组件
from src.core.context import ApplicationContext
from src.core.plugin_manager import PluginManager
from src.ui.main_window import MainWindow
from src.utils.tray_manager import TrayManager
from src.ui.action_manager import ActionManager
from src.services.config_service import ConfigService
from src.services.database_service import DatabaseService
from src.ui.settings_page import SettingsPageWidget

# --- 全局应用程序常量 ---
APP_NAME = "Desktop Control & Monitoring Center"
APP_VERSION = "5.2.2-Stability-Fix" # 版本号更新
CONFIG_FILE = 'config.ini'
ICON_FILE = 'icon.png'
LOG_FILE = 'app.log'
DB_FILE = 'history.db'

def setup_logging():
    """配置全局日志记录器。"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8', mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("="*80)
    logging.info(f"--- 应用程序启动流程开始 (v{APP_VERSION}) ---")
    logging.info("="*80)
    logging.info("[STEP 0] 日志系统初始化完成。")

class ApplicationOrchestrator:
    """【平台核心】应用协调器，负责组装平台和加载插件。"""
    def __init__(self):
        logging.info("[STEP 1.0] ApplicationOrchestrator: 开始初始化平台核心...")

        logging.info("[STEP 1.1] 初始化Qt Application实例。")
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        logging.info("[STEP 1.2] 初始化平台级核心服务 (Config, Database)。")
        self.config_service = ConfigService(CONFIG_FILE)
        try:
            self.db_service = DatabaseService(DB_FILE)
            self.db_service.init_db()
        except Exception as e:
            logging.critical(f"数据库服务初始化失败，程序无法启动: {e}", exc_info=True)
            sys.exit(1)

        logging.info("[STEP 1.3] 初始化平台级核心UI (MainWindow, TrayManager, ActionManager)。")
        self.window = MainWindow()
        self.window.setWindowTitle(self.config_service.get_value("General", "app_name", APP_NAME))
        self.tray_manager = TrayManager(self.app, self.window, ICON_FILE)
        self.action_manager = ActionManager(self.app)
        
        # 【新增】将托盘管理器的退出请求信号连接到应用程序的退出槽
        # 这是解决跨线程调用GUI问题的关键步骤
        self.tray_manager.quit_requested.connect(self.app.quit)
        logging.info("[STEP 1.3.1] TrayManager退出信号已连接到主应用退出槽。")


        logging.info("[STEP 1.4] 创建共享的 ApplicationContext。")
        self.context = ApplicationContext(
            app=self.app,
            main_window=self.window,
            config_service=self.config_service,
            db_service=self.db_service,
            tray_manager=self.tray_manager,
            action_manager=self.action_manager
        )

        logging.info("[STEP 1.5] 初始化插件管理器 (PluginManager)。")
        self.plugin_manager = PluginManager(self.context)
        
        logging.info("[STEP 2.0] ApplicationOrchestrator: 开始加载和初始化插件...")
        self.plugin_manager.load_plugins()
        self.plugin_manager.initialize_plugins()
        logging.info("[STEP 2.3] ApplicationOrchestrator: 所有插件加载和初始化完毕。")
        
        logging.info("[STEP 4.0] 添加平台级页面 (如设置页面)。")
        self._add_core_pages()

        logging.info("[STEP 4.1] 连接应用程序退出信号。")
        self.app.aboutToQuit.connect(self.shutdown)
        logging.info("[STEP 4.2] 平台核心初始化流程结束。")

    def _add_core_pages(self):
        """添加不属于任何插件的核心页面。"""
        self.settings_page = SettingsPageWidget(self.config_service)
        self.window.add_page("设置", self.settings_page)
        logging.info("  - 核心页面 '设置' 已添加。")

    def run(self):
        """启动应用程序的事件循环。"""
        logging.info("[STEP 5.0] 显示主窗口并启动Qt事件循环...")
        try:
            self.tray_manager.run()
            if self.config_service.get_value("General", "start_minimized", "false").lower() != 'true':
                self.window.show()
            sys.exit(self.app.exec())
        except Exception as e:
            logging.critical(f"应用程序顶层发生未捕获的异常: {e}", exc_info=True)
            sys.exit(1)

    def shutdown(self):
        """安全关闭应用，先关闭插件，再关闭核心服务。"""
        logging.info("[STEP 6.0] 应用程序关闭流程开始...")
        logging.info("[STEP 6.1] 关闭所有插件。")
        self.plugin_manager.shutdown_plugins()
        logging.info("[STEP 6.2] 关闭数据库服务。")
        self.db_service.close()
        logging.info("[STEP 6.3] 应用程序关闭流程结束。")


if __name__ == '__main__':
    setup_logging()
    main_app = ApplicationOrchestrator()
    main_app.run()
```

## context.py

```python
# src/core/context.py
from dataclasses import dataclass
from PySide6.QtWidgets import QApplication
from src.services.config_service import ConfigService
from src.services.database_service import DatabaseService
from src.ui.main_window import MainWindow
from src.utils.tray_manager import TrayManager
from src.ui.action_manager import ActionManager

@dataclass
class ApplicationContext:
    """一个数据类，持有所有核心/共享服务和组件的引用，供插件使用。"""
    app: QApplication
    main_window: MainWindow
    config_service: ConfigService
    db_service: DatabaseService
    tray_manager: TrayManager
    action_manager: ActionManager
```
## plugin_interface.py

```python
# desktop_center/src/core/plugin_interface.py
from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget
from .context import ApplicationContext

class IFeaturePlugin(ABC):
    """所有功能插件必须实现的接口。"""
    
    @abstractmethod
    def name(self) -> str:
        """返回插件的唯一名称，用于内部识别。"""
        pass

    @abstractmethod
    def display_name(self) -> str:
        """返回显示在UI上的名称（如导航栏标题）。"""
        pass
        
    @abstractmethod
    def load_priority(self) -> int:
        """
        【新增】返回插件的加载优先级。数字越小，优先级越高。
        例如：核心服务插件=0, 普通功能=100, 依赖其他插件的功能=200。
        """
        pass

    def initialize(self, context: ApplicationContext):
        self.context = context
        self.background_services = []
        self.page_widget = None

    def get_page_widget(self) -> QWidget | None:
        return self.page_widget

    def get_background_services(self) -> list:
        return self.background_services

    def shutdown(self):
        for service in self.background_services:
            if hasattr(service, 'running') and hasattr(service, 'quit'):
                if service.running:
                    service.running = False
                    service.quit()
                    service.wait(5000)
```

## plugin_manager.py

```python
# desktop_center/src/core/plugin_manager.py
import importlib
import pkgutil
import logging
from src.core.plugin_interface import IFeaturePlugin

class PluginManager:
    """负责发现、加载和管理所有插件的管理器。"""
    def __init__(self, context):
        self.context = context
        self.plugins: list[IFeaturePlugin] = []

    def load_plugins(self):
        """
        使用 walk_packages 递归地发现并加载所有在 src.features 包下的插件。
        """
        import src.features
        logging.info("[STEP 2.1] PluginManager: 开始扫描 'src/features' 目录以发现插件...")
        
        for module_info in pkgutil.walk_packages(path=src.features.__path__, prefix=src.features.__name__ + '.'):
            try:
                module = importlib.import_module(module_info.name)
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if isinstance(item, type) and issubclass(item, IFeaturePlugin) and item is not IFeaturePlugin:
                        if not any(isinstance(p, item) for p in self.plugins):
                            plugin_instance = item()
                            self.plugins.append(plugin_instance)
                            logging.info(f"  - 插件已发现并加载: {plugin_instance.name()} (from {module_info.name})")
            except Exception as e:
                logging.error(f"加载插件模块 {module_info.name} 时失败: {e}", exc_info=True)
        logging.info("[STEP 2.1] PluginManager: 插件扫描和加载完成。")


    def initialize_plugins(self):
        """初始化所有已加载的插件。"""
        logging.info("[STEP 2.2] PluginManager: 开始初始化所有已加载的插件...")
        # 【修改】使用新的 load_priority() 方法进行排序，移除硬编码依赖
        self.plugins.sort(key=lambda p: p.load_priority())
        logging.info(f"  - 插件将按以下优先级顺序初始化: {[p.name() for p in self.plugins]}")
        
        for plugin in self.plugins:
            try:
                logging.info(f"  - 正在初始化插件: '{plugin.name()}' (优先级: {plugin.load_priority()})...")
                plugin.initialize(self.context)
                
                page_widget = plugin.get_page_widget()
                if page_widget:
                    self.context.main_window.add_page(plugin.display_name(), page_widget)
                    logging.info(f"    - 插件 '{plugin.name()}' 的主页面已添加到主窗口。")

                for service in plugin.get_background_services():
                    service.start()
                    logging.info(f"    - 已启动插件 '{plugin.name()}' 的后台服务: {type(service).__name__}")
                logging.info(f"  - 插件 '{plugin.name()}' 初始化完成。")
            except Exception as e:
                logging.error(f"初始化插件 {plugin.name()} 失败: {e}", exc_info=True)

    def shutdown_plugins(self):
        """安全关闭所有插件。"""
        for plugin in self.plugins:
            try:
                plugin.shutdown()
                logging.info(f"  - 插件 '{plugin.name()}' 已成功关闭。")
            except Exception as e:
                logging.error(f"关闭插件 {plugin.name()} 时发生错误: {e}", exc_info=True)

```

## config_service.py

```python
# desktop_center/src/services/config_service.py
import configparser
import logging
from typing import List, Tuple

class ConfigService:
    """
    健壮的配置服务，负责所有 config.ini 文件的读写逻辑。
    设计目标是即使在配置文件损坏或丢失的情况下也能让主程序安全启动。
    """
    def __init__(self, filepath: str):
        """
        初始化配置服务。

        Args:
            filepath (str): config.ini 文件的路径。
        """
        self.filepath = filepath
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self) -> None:
        """
        从磁盘加载配置文件。
        如果文件不存在或无法解析，将记录一个错误并使用一个空的配置对象，
        这可以防止应用程序在启动时崩溃。
        """
        try:
            # 使用utf-8-sig可以处理带有BOM头的UTF-8文件
            read_files = self.config.read(self.filepath, encoding='utf-8-sig')
            if not read_files:
                logging.warning(f"配置文件 '{self.filepath}' 未找到。将使用空配置。")
            else:
                logging.info(f"成功加载配置文件: {self.filepath}")
        except configparser.Error as e:
            logging.error(f"解析配置文件 '{self.filepath}' 失败: {e}")
            # 解析失败时重置为一个空对象，保证程序健壮性
            self.config = configparser.ConfigParser()

    def get_sections(self) -> List[str]:
        """获取所有配置区段的名称列表。"""
        return self.config.sections()

    def get_options(self, section: str) -> List[Tuple[str, str]]:
        """获取指定区段下的所有键值对。"""
        if self.config.has_section(section):
            return self.config.items(section)
        return []

    def get_value(self, section: str, option: str, fallback: str = None) -> str:
        """安全地获取一个配置值，可提供默认值。"""
        return self.config.get(section, option, fallback=fallback)

    def set_option(self, section: str, option: str, value: str) -> None:
        """设置一个配置值。如果区段不存在，则自动创建。"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))

    def save_config(self) -> bool:
        """
        将当前配置状态写回文件。

        Returns:
            bool: 如果保存成功则返回 True，否则返回 False。
        """
        try:
            with open(self.filepath, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
            logging.info(f"配置文件已成功保存到: {self.filepath}")
            return True
        except IOError as e:
            logging.error(f"保存配置文件到 '{self.filepath}' 失败: {e}")
            return False

```



## main_window.py

```python
# desktop_center/src/ui/main_window.py
import logging  # 【新增】添加对logging模块的导入
from PySide6.QtWidgets import (QMainWindow, QWidget, QListWidget, QListWidgetItem, 
                               QHBoxLayout, QStackedWidget)
from PySide6.QtCore import QEvent, QSize

class MainWindow(QMainWindow):
    """
    主应用程序窗口框架。
    采用“导航-内容”布局，设计为可扩展的容器。
    它自身不实现任何具体功能页面，只提供添加和切换页面的能力。
    """
    def __init__(self, parent: QWidget = None):
        """
        初始化主窗口。

        Args:
            parent (QWidget, optional): 父组件。默认为 None。
        """
        super().__init__(parent)
        self.setWindowTitle("Application Skeleton") # 初始标题，可由app.py覆盖
        self.setGeometry(100, 100, 900, 700) # 初始尺寸

        # --- 创建主布局 ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # 无边距，让子组件填满
        main_layout.setSpacing(0)

        # --- 左侧导航栏 ---
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(180)
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #f0f0f0;
                border: none;
                font-size: 14px;
                padding-top: 10px;
            }
            QListWidget::item {
                padding: 12px 20px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
                font-weight: bold;
                border-left: 5px solid #005a9e;
            }
        """)
        main_layout.addWidget(self.nav_list)
        
        # --- 右侧内容区 (使用QStackedWidget实现页面切换) ---
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # --- 连接信号与槽 ---
        # 当导航栏的当前项改变时，切换到对应的页面
        self.nav_list.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)
    
    def add_page(self, title: str, widget: QWidget) -> None:
        """
        向主窗口动态添加一个功能页面。

        Args:
            title (str): 显示在导航栏中的页面标题。
            widget (QWidget): 要添加的功能页面的实例。
        """
        # 将页面实例添加到堆栈窗口中
        self.stacked_widget.addWidget(widget)
        # 将页面标题添加到导航列表
        self.nav_list.addItem(QListWidgetItem(title))
        
        # 默认选中第一个添加的页面
        if self.nav_list.count() == 1:
            self.nav_list.setCurrentRow(0)

    def closeEvent(self, event: QEvent) -> None:
        """
        重写窗口关闭事件。
        默认行为是隐藏窗口而不是退出应用，以便在系统托盘中继续运行。
        
        Args:
            event (QEvent): 关闭事件对象。
        """
        logging.info("关闭事件触发：隐藏主窗口到系统托盘。")
        event.ignore()  # 忽略默认的关闭行为（即退出）
        self.hide()     # 将窗口隐藏
```

## action_manager.py

```python
# desktop_center/src/ui/action_manager.py
from PySide6.QtCore import QObject
from PySide6.QtGui import QAction
from typing import Dict

class ActionManager(QObject):
    """
    【修改】中央动作管理器，作为一个通用的动作注册中心。
    插件或其他组件可以注册全局可用的QAction，实现功能触发和UI组件的解耦。
    它本身不应持有任何特定功能的动作实例。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._actions: Dict[str, QAction] = {}

    def register_action(self, name: str, action: QAction) -> None:
        """
        【新增】注册一个全局动作。

        Args:
            name (str): 动作的唯一标识符，例如 'alert_center.show_history'。
            action (QAction): 要注册的QAction实例。
        
        Raises:
            ValueError: 如果同名动作已被注册。
        """
        if name in self._actions:
            raise ValueError(f"动作 '{name}' 已经被注册。")
        self._actions[name] = action

    def get_action(self, name: str) -> QAction | None:
        """
        【新增】根据名称获取一个已注册的动作。

        Args:
            name (str): 动作的唯一标识符。

        Returns:
            QAction | None: 返回找到的QAction实例，如果未找到则返回None。
        """
        return self._actions.get(name)
```

## settings_page.py

```python
# desktop_center/src/ui/settings_page.py
import logging
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGroupBox,
                               QLineEdit, QPushButton, QMessageBox, QFormLayout,
                               QComboBox, QSpinBox, QScrollArea, QHBoxLayout)
from PySide6.QtCore import Qt, QEvent

from src.services.config_service import ConfigService

# 【核心修改】元数据结构现在与最终的config.ini完全匹配
SETTING_METADATA = {
    "General": {
        "app_name": {"widget": "lineedit", "label": "应用程序名称"},
        "start_minimized": {"widget": "combobox", "label": "启动时最小化", "items": ["禁用", "启用"], "map": {"启用": "true", "禁用": "false"}}
    },
    "InfoService": { # 新的统一区段
        "host": {"widget": "lineedit", "label": "监听地址", "col": 0},
        "port": {"widget": "spinbox", "label": "监听端口", "min": 1024, "max": 65535, "col": 0},
        "enable_desktop_popup": {"widget": "combobox", "label": "桌面弹窗通知", "items": ["禁用", "启用"], "map": {"启用": "true", "禁用": "false"}, "col": 0},
        "popup_timeout": {"widget": "spinbox", "label": "弹窗显示时长 (秒)", "min": 1, "max": 300, "col": 1},
        "notification_level": {"widget": "combobox", "label": "通知级别阈值", "items": ["INFO", "WARNING", "CRITICAL"], "col": 1},
        "load_history_on_startup": {"widget": "combobox", "label": "启动时加载历史", "items": ["不加载", "加载最近50条", "加载最近100条", "加载最近500条"], "map": {"不加载": "0", "加载最近50条": "50", "加载最近100条": "100", "加载最近500条": "500"}, "col": 1}
    }
}

class SettingsPageWidget(QWidget):
    """
    “设置”功能页面。
    采用“元数据驱动”和“卡片式布局”进行重构，提升了可维护性和用户体验。
    """
    def __init__(self, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        self.editors = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("应用程序设置")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px; color: #333;")
        main_layout.addWidget(title_label)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        content_widget = QWidget()
        self.settings_layout = QVBoxLayout(content_widget)
        self.settings_layout.setSpacing(15)
        self.settings_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        self._create_setting_cards()

        self.save_button = QPushButton("保存所有设置")
        self.save_button.setMinimumHeight(35)
        self.save_button.setStyleSheet("""
            QPushButton { font-size: 14px; font-weight: bold; background-color: #0078d4; color: white; border: none; border-radius: 5px; padding: 0 20px; }
            QPushButton:hover { background-color: #005a9e; }
            QPushButton:pressed { background-color: #004578; }
        """)
        self.save_button.clicked.connect(self.save_settings)
        main_layout.addWidget(self.save_button, 0, Qt.AlignmentFlag.AlignRight)

        self.installEventFilter(self)

    # 【核心修改】UI创建逻辑大幅简化
    def _create_setting_cards(self):
        """根据元数据动态创建所有设置卡片。"""
        for section, options_meta in SETTING_METADATA.items():
            card = QGroupBox(section)
            card.setStyleSheet("""
                QGroupBox { font-size: 16px; font-weight: bold; color: #333; background-color: #fcfcfc; border: 1px solid #e0e0e0; border-radius: 8px; margin-top: 10px; }
                QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; background-color: #fcfcfc; }
            """)
            
            # 【核心修改】根据section名，选择不同的布局策略
            if section == "InfoService":
                self._populate_multi_column_layout(card, section, options_meta)
            else:
                form_layout = QFormLayout(card)
                form_layout.setSpacing(12)
                form_layout.setContentsMargins(20, 30, 20, 20)
                self._populate_form_layout(form_layout, section, options_meta)
            
            self.settings_layout.addWidget(card)

    def _populate_multi_column_layout(self, parent_group: QGroupBox, section_name: str, options_meta: dict):
        """为InfoService卡片创建多列布局。"""
        # 主水平布局
        main_hbox = QHBoxLayout(parent_group)
        main_hbox.setSpacing(40)
        main_hbox.setContentsMargins(20, 30, 20, 20)

        # 创建两个垂直的表单布局作为列
        column1_layout = QFormLayout()
        column1_layout.setSpacing(12)
        column2_layout = QFormLayout()
        column2_layout.setSpacing(12)

        # 根据元数据中的 'col' 键，将控件分配到不同的列
        for key, meta in options_meta.items():
            target_layout = column1_layout if meta.get("col", 0) == 0 else column2_layout
            self._add_widget_to_form(target_layout, section_name, key, meta)
        
        main_hbox.addLayout(column1_layout)
        main_hbox.addLayout(column2_layout)

    def _populate_form_layout(self, form_layout: QFormLayout, section_name: str, options_meta: dict):
        """将控件填充到给定的单列QFormLayout中。"""
        for key, meta in options_meta.items():
            self._add_widget_to_form(form_layout, section_name, key, meta)

    def _add_widget_to_form(self, form_layout: QFormLayout, section_name: str, key: str, meta: dict):
        """辅助方法：创建一个控件并将其添加到表单布局中。"""
        if section_name not in self.editors:
            self.editors[section_name] = {}
            
        widget_type = meta["widget"]
        label_text = meta["label"]
        editor_widget = None

        if widget_type == "lineedit":
            editor_widget = QLineEdit()
        elif widget_type == "spinbox":
            editor_widget = QSpinBox()
            editor_widget.setRange(meta.get("min", 0), meta.get("max", 99999))
        elif widget_type == "combobox":
            editor_widget = QComboBox()
            editor_widget.addItems(meta["items"])
            editor_widget.setMaximumWidth(200) # 稍微减小最大宽度

        if editor_widget:
            form_layout.addRow(QLabel(f"{label_text}:"), editor_widget)
            self.editors[section_name][key] = editor_widget

    # ... (其他方法保持不变, 逻辑上不再需要做任何特殊处理)

    def _load_settings_to_ui(self):
        logging.info("正在同步全局设置页面UI...")
        for section, options in self.editors.items():
            for key, widget in options.items():
                meta = SETTING_METADATA[section][key]
                current_value = self.config_service.get_value(section, key)

                if isinstance(widget, QLineEdit):
                    widget.setText(current_value)
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(current_value) if current_value and current_value.isdigit() else meta.get("min", 0))
                elif isinstance(widget, QComboBox):
                    if "map" in meta:
                        display_text = next((text for text, val in meta["map"].items() if val == current_value), meta["items"][0])
                        widget.setCurrentText(display_text)
                    else:
                        if current_value in meta["items"]:
                            widget.setCurrentText(current_value)

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj is self and event.type() == QEvent.Type.Show:
            self._load_settings_to_ui()
        return super().eventFilter(obj, event)

    def save_settings(self):
        logging.info("尝试保存所有设置...")
        try:
            for section, options in self.editors.items():
                for key, widget in options.items():
                    meta = SETTING_METADATA[section][key]
                    value = None
                    if isinstance(widget, QLineEdit):
                        value = widget.text()
                    elif isinstance(widget, QSpinBox):
                        value = str(widget.value())
                    elif isinstance(widget, QComboBox):
                        if "map" in meta:
                            value = meta["map"].get(widget.currentText())
                        else:
                            value = widget.currentText()
                    
                    if value is not None:
                        self.config_service.set_option(section, key, value)
            
            if self.config_service.save_config():
                QMessageBox.information(self, "成功", "所有设置已成功保存！")
            else:
                QMessageBox.warning(self, "失败", "保存设置时发生错误，请查看日志。")
        except Exception as e:
            logging.error(f"保存设置时发生未知错误: {e}", exc_info=True)
            QMessageBox.critical(self, "严重错误", f"保存设置时发生严重错误: {e}")

```

## tray_manager.py

```python
# desktop_center/src/utils/tray_manager.py
import logging
import os
# 【新增】导入 QObject 和 Signal 以实现线程安全的信号/槽机制
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from pystray import MenuItem, Icon
from PIL import Image

# 【修改】使 TrayManager 继承自 QObject，以便使用信号
class TrayManager(QObject):
    """
    负责管理系统托盘图标及其菜单。
    这是一个独立的组件，控制着应用的显示、隐藏和退出逻辑。
    """
    # 【新增】定义一个信号，用于从后台线程向主线程请求退出
    quit_requested = Signal()

    def __init__(self, app: QApplication, window: 'MainWindow', icon_path: str):
        """
        初始化托盘管理器。

        Args:
            app (QApplication): Qt应用程序实例，用于安全退出。
            window (MainWindow): 主窗口实例，用于控制其显示/隐藏。
            icon_path (str): 图标文件的路径。

        Raises:
            FileNotFoundError: 如果图标文件不存在。
        """
        # 【新增】必须调用父类QObject的构造函数
        super().__init__()
        
        self.app = app
        self.window = window

        self.window.setWindowIcon(QIcon(icon_path))
        
        try:
            image = Image.open(icon_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Icon file not found at: {icon_path}")

        menu = (
            MenuItem('显示主窗口', self.show_window, default=True),
            MenuItem('退出程序', self.quit_app)
        )
        
        self.tray_icon = Icon("DesktopCenter", image, "桌面控制与监控中心", menu)
        
        logging.info("系统托盘管理器初始化完成。")

    def run(self) -> None:
        """在后台线程中启动托盘图标的事件监听。"""
        self.tray_icon.run_detached()
        logging.info("系统托盘图标已在独立线程中运行。")

    def show_window(self) -> None:
        """从托盘菜单显示并激活主窗口。"""
        logging.info("通过托盘菜单请求显示主窗口。")
        self.window.show()
        self.window.activateWindow()

    def quit_app(self) -> None:
        """
        【修改】安全地请求退出整个应用程序。
        此方法在pystray的后台线程中被调用。
        它发射一个信号，该信号连接到主线程中的槽，以避免跨线程GUI调用。
        """
        logging.info("通过托盘菜单请求退出应用程序...")
        
        # 1. 停止pystray图标的事件循环。
        self.tray_icon.stop()
        logging.info("pystray图标已停止。")
        
        # 2. 【修改】发射信号，请求主线程执行退出操作，而不是直接调用。
        logging.info("正在发射信号以触发应用程序的优雅关闭流程...")
        self.quit_requested.emit()
```

## 目前需要做的
分析这个架构是否合理，如果合理，当前我提供的代码中是否有需要完善的点
