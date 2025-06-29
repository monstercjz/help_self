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
        ├── exception_handler.py
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
import os
import logging
import configparser
from PySide6.QtWidgets import QApplication, QMessageBox

# --- 1. 导入项目核心模块 ---
# 遵循先导入服务、再导入UI、最后导入管理器的逻辑顺序
from src.services.config_service import ConfigService
from src.services.database_service import DatabaseService
from src.services.notification_service import NotificationService
from src.ui.main_window import MainWindow
from src.ui.settings_page import SettingsPageWidget
from src.ui.action_manager import ActionManager
from src.utils.tray_manager import TrayManager
from src.utils.exception_handler import setup_exception_handler
from src.core.context import ApplicationContext
from src.core.plugin_manager import PluginManager


# --- 2. 全局应用程序常量 ---
# 将所有硬编码的字符串和配置集中在此处，便于管理
APP_VERSION = "5.3.8-Code-Refinement"
APP_NAME_DEFAULT = "Desktop Control & Monitoring Center"
CONFIG_FILE = 'config.ini'
DB_FILE = 'history.db'
LOG_FILE = 'app.log'
PNG_ICON_FILE = 'icon.png'  # 用于窗口、托盘等
ICO_ICON_FILE = 'icon.ico'  # 专门用于Windows原生通知


def setup_logging():
    """
    配置全局日志记录器。
    此函数设计为在应用生命周期中最早被调用，它会预读配置文件以获取日志级别。
    """
    # 默认日志级别，以防配置文件无法读取
    log_level_str = "INFO"
    
    # 步骤1: 预加载配置以获取日志级别，不实例化完整的ConfigService
    try:
        pre_parser = configparser.ConfigParser()
        if pre_parser.read(CONFIG_FILE, encoding='utf-8-sig'):
            log_level_str = pre_parser.get('Logging', 'level', fallback='INFO').upper()
    except (configparser.Error, IOError):
        # 即使日志系统尚未完全建立，也可以使用Python的内置警告
        import warnings
        warnings.warn(f"无法预读配置文件 '{CONFIG_FILE}' 以获取日志级别，将使用默认的 'INFO' 级别。")

    # 步骤2: 将字符串级别转换为logging模块的常量
    log_level = getattr(logging, log_level_str, logging.INFO)

    # 步骤3: 配置日志系统
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8', mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # 打印启动横幅
    logging.info("=" * 80)
    logging.info(f"--- 应用程序启动流程开始 (v{APP_VERSION}) ---")
    logging.info("=" * 80)
    logging.info(f"[STEP 0] 日志系统初始化完成。日志级别设置为: {log_level_str}")


class ApplicationOrchestrator:
    """
    【平台核心】应用协调器。
    
    这是整个应用程序的“大脑”，负责以正确的顺序组装所有核心组件、
    服务和UI，加载插件，并管理应用的生命周期（启动、运行、关闭）。
    """
    def __init__(self):
        """初始化整个应用程序的架构。"""
        logging.info("[STEP 1.0] ApplicationOrchestrator: 开始初始化平台核心...")

        # --- 1.1 基础环境准备 ---
        # 计算所有资源文件的绝对路径，以避免在不同工作目录下出现问题
        project_root = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(project_root, CONFIG_FILE)
        self.db_path = os.path.join(project_root, DB_FILE)
        self.png_icon_path = os.path.join(project_root, PNG_ICON_FILE)
        self.ico_icon_path = os.path.join(project_root, ICO_ICON_FILE)
        logging.info("  - 基础路径计算完成。")

        # --- 1.2 初始化Qt应用实例 ---
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False) # 确保关闭主窗口时应用不退出
        logging.info("  - Qt Application实例初始化完成。")

        # --- 1.3 初始化核心后台服务 ---
        # 这些服务不依赖UI，是应用的基础数据和配置提供者
        self.config_service = ConfigService(self.config_path)
        try:
            self.db_service = DatabaseService(self.db_path)
            self.db_service.init_db()
        except Exception as e:
            logging.critical(f"数据库服务初始化失败，程序无法启动: {e}", exc_info=True)
            sys.exit(1)
        
        # 通知服务依赖于配置服务，因此在其后初始化
        app_name = self.config_service.get_value("General", "app_name", APP_NAME_DEFAULT)
        self.notification_service = NotificationService(
            app_name=app_name,
            app_icon=self.ico_icon_path,
            config_service=self.config_service
        )
        logging.info("  - 核心后台服务 (Config, Database, Notification) 初始化完成。")

        # --- 1.4 初始化核心UI组件 ---
        # 这些是平台级的UI元素，所有插件都可能与之交互
        self.window = MainWindow()
        self.window.setWindowTitle(app_name)
        self.tray_manager = TrayManager(self.app, self.window, self.png_icon_path)
        self.action_manager = ActionManager(self.app)
        logging.info("  - 核心UI组件 (MainWindow, TrayManager, ActionManager) 初始化完成。")

        # --- 1.5 创建共享上下文 (ApplicationContext) ---
        # 这是整个架构的核心，它像一个“工具箱”，被传递给所有插件，
        # 使插件能够安全地访问所有共享的平台资源。
        self.context = ApplicationContext(
            app=self.app,
            main_window=self.window,
            config_service=self.config_service,
            db_service=self.db_service,
            tray_manager=self.tray_manager,
            action_manager=self.action_manager,
            notification_service=self.notification_service
        )
        logging.info("  - 共享的 ApplicationContext 创建完成。")

        # --- 1.6 初始化插件系统 ---
        self.plugin_manager = PluginManager(self.context)
        logging.info("[STEP 2.0] 开始加载和初始化所有插件...")
        self.plugin_manager.load_plugins()
        self.plugin_manager.initialize_plugins()
        logging.info("[STEP 2.3] 所有插件加载和初始化完毕。")
        
        # --- 1.7 添加平台级页面 ---
        # 某些页面（如“设置”）是平台的一部分，不属于任何插件
        logging.info("[STEP 3.0] 添加平台级页面...")
        self._add_core_pages()

        # --- 1.8 连接全局信号与槽 ---
        # 这是最后一步，将所有组件连接起来，形成完整的应用逻辑
        logging.info("[STEP 4.0] 连接应用程序全局信号...")
        self.tray_manager.quit_requested.connect(self.app.quit)
        self.app.aboutToQuit.connect(self.shutdown)
        logging.info("  - 信号连接完成。")
        
        logging.info("[STEP 4.1] 平台核心初始化流程结束。")

    def _add_core_pages(self):
        """将不属于任何插件的核心页面（如设置页面）添加到主窗口。"""
        self.settings_page = SettingsPageWidget(self.config_service)
        self.window.add_page("设置", self.settings_page)
        logging.info("  - 核心页面 '设置' 已添加。")

    def run(self):
        """启动应用程序的事件循环，并处理启动时的UI逻辑。"""
        logging.info("[STEP 5.0] 启动Qt事件循环...")
        try:
            # 启动托盘图标的后台监听
            self.tray_manager.run()
            
            # 发送启动通知（如果配置允许）
            if self.config_service.get_value("General", "show_startup_notification", "true").lower() == 'true':
                self.context.notification_service.show(
                    title=f"{self.window.windowTitle()} 已启动",
                    message="程序正在后台运行。您可以通过系统托盘图标访问主窗口或退出程序。"
                )

            # 根据配置决定是显示主窗口还是最小化启动
            if self.config_service.get_value("General", "start_minimized", "false").lower() != 'true':
                self.window.center_on_screen()
                self.window.show()
                
            # 阻塞并开始执行Qt事件循环
            sys.exit(self.app.exec())
        except Exception as e:
            logging.critical(f"应用程序顶层发生未捕获的异常: {e}", exc_info=True)
            sys.exit(1)

    def shutdown(self):
        """执行安全的关闭流程，确保所有资源被正确释放。"""
        logging.info("[STEP 6.0] 应用程序关闭流程开始...")
        logging.info("  - [6.1] 关闭所有插件...")
        self.plugin_manager.shutdown_plugins()
        logging.info("  - [6.2] 关闭数据库服务...")
        self.db_service.close()
        logging.info("[STEP 6.3] 应用程序关闭流程结束。")


if __name__ == '__main__':
    """应用程序的主入口点。"""
    try:
        # 确保所有相对路径都是基于此文件所在目录的
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # 1. 优先设置日志记录，以便记录所有后续步骤
        setup_logging()
        
        # 2. 其次设置全局异常处理，作为最后一道安全防线
        setup_exception_handler()
        
        # 3. 实例化并运行应用协调器
        main_app = ApplicationOrchestrator()
        main_app.run()
        
    except Exception as e:
        # 这个except块用于捕获在ApplicationOrchestrator初始化期间发生的、
        # 无法被全局异常钩子捕获的致命错误。
        logging.critical(f"应用程序在初始化阶段发生致命错误，无法启动: {e}", exc_info=True)
        QMessageBox.critical(None, "启动失败", f"应用程序无法启动，请查看日志文件 app.log 获取详情。\n\n错误: {e}")
        sys.exit(1)
```

## context.py

```python
# desktop_center/src/core/context.py
from dataclasses import dataclass
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QApplication

# 【修改】使用类型检查块来避免循环导入
if TYPE_CHECKING:
    from src.services.config_service import ConfigService
    from src.services.database_service import DatabaseService
    from src.services.notification_service import NotificationService
    from src.ui.main_window import MainWindow
    from src.utils.tray_manager import TrayManager
    from src.ui.action_manager import ActionManager

@dataclass
class ApplicationContext:
    """一个数据类，持有所有核心/共享服务和组件的引用，供插件使用。"""
    app: QApplication
    main_window: 'MainWindow'
    config_service: 'ConfigService'
    db_service: 'DatabaseService'
    tray_manager: 'TrayManager'
    action_manager: 'ActionManager'
    notification_service: 'NotificationService' # 【新增】通知服务引用
```
## plugin_interface.py

```python
# desktop_center/src/core/plugin_interface.py
from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget
from .context import ApplicationContext

class IFeaturePlugin(ABC):
    """
    【文档化】所有功能插件必须实现的接口（契约）。

    这个接口定义了一个插件的基本行为和与平台核心交互的方式。
    平台核心通过这些方法来识别、加载、初始化和关闭插件。
    """
    
    @abstractmethod
    def name(self) -> str:
        """
        返回插件的唯一内部名称。

        这个名称用于日志记录、内部管理和插件间的唯一识别。
        它应该是简短、无空格的ASCII字符串，例如 "alert_center"。

        Returns:
            str: 插件的唯一标识符。
        """
        pass

    @abstractmethod
    def display_name(self) -> str:
        """
        返回插件在用户界面上显示的名称。

        这个名称将用于主窗口的导航栏、菜单项等面向用户的地方。
        它可以是任何UTF-8字符串，例如 "告警中心"。

        Returns:
            str: 插件的显示名称。
        """
        pass
        
    @abstractmethod
    def load_priority(self) -> int:
        """
        返回插件的加载优先级，数字越小，优先级越高。

        这个值决定了插件 `initialize` 方法的调用顺序。
        如果插件A依赖于插件B，则插件B的优先级应高于（即数值小于）插件A。

        建议使用以下范围：
        - 0-99: 核心服务型插件
        - 100-199: 普通独立功能插件
        - 200+: 依赖其他插件的功能插件

        Returns:
            int: 加载优先级。
        """
        pass

    def initialize(self, context: ApplicationContext):
        """
        初始化插件。

        平台核心在加载所有插件后会调用此方法。插件应该在这里：
        1. 保存 `context` 的引用，以便后续访问共享服务。
        2. 创建并准备其UI页面（如果需要）。
        3. 创建并准备其后台服务（如果需要）。
        4. 注册全局动作到 `ActionManager`。
        5. 连接到核心或其他服务的信号。

        Args:
            context (ApplicationContext): 包含所有共享服务和组件的应用上下文。
        """
        self.context = context
        self.background_services = []
        self.page_widget = None

    def get_page_widget(self) -> QWidget | None:
        """
        返回此插件的主UI页面控件实例。

        如果插件没有UI页面，应返回 `None`。
        返回的控件将被添加到主窗口的内容区域。

        Returns:
            QWidget | None: 插件的UI页面实例或None。
        """
        return self.page_widget

    def get_background_services(self) -> list:
        """
        返回此插件需要在后台运行的服务列表。

        这些服务通常是继承自 `QThread` 的对象。
        平台核心会自动调用每个服务的 `start()` 方法。

        Returns:
            list: 需要在后台运行的服务实例列表。
        """
        return self.background_services

    def shutdown(self):
        """
        在应用程序关闭时，安全地关闭插件。

        平台核心在退出前会调用此方法。插件应该在这里：
        1. 停止并等待所有后台线程结束。
        2. 断开所有信号连接。
        3. 释放所有持有的资源。

        默认实现会尝试优雅地停止 `get_background_services()` 返回的服务。
        如果插件有更复杂的关闭逻辑，应重写此方法。
        """
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
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QThread
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
        self.plugins.sort(key=lambda p: p.load_priority())
        logging.info(f"  - 插件将按以下优先级顺序初始化: {[p.name() for p in self.plugins]}")
        
        for plugin in self.plugins:
            try:
                logging.info(f"  - 正在初始化插件: '{plugin.name()}' (优先级: {plugin.load_priority()})...")
                plugin.initialize(self.context)
                
                # 【修改】对插件返回值进行健壮性检查
                page_widget = plugin.get_page_widget()
                if page_widget:
                    if isinstance(page_widget, QWidget):
                        self.context.main_window.add_page(plugin.display_name(), page_widget)
                        logging.info(f"    - 插件 '{plugin.name()}' 的主页面已添加到主窗口。")
                    else:
                        logging.warning(f"    - 插件 '{plugin.name()}' 的 get_page_widget() 返回的不是有效QWidget，已忽略。")

                background_services = plugin.get_background_services()
                if background_services:
                    for service in background_services:
                        if isinstance(service, QThread) and hasattr(service, 'start'):
                            service.start()
                            logging.info(f"    - 已启动插件 '{plugin.name()}' 的后台服务: {type(service).__name__}")
                        else:
                            logging.warning(f"    - 插件 '{plugin.name()}' 返回的后台服务 {type(service).__name__} 不是有效的QThread，已忽略。")
                
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
import logging
# 【新增】导入 QApplication 以便访问屏幕信息
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QListWidget, 
                               QListWidgetItem, QHBoxLayout, QStackedWidget)
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

    def center_on_screen(self) -> None:
        """
        【新增】将窗口移动到主屏幕的中央。
        """
        try:
            # 获取主屏幕的几何信息
            screen_geometry = QApplication.primaryScreen().geometry()
            # 获取窗口自身的几何信息 (包括标题栏)
            window_geometry = self.frameGeometry()
            # 计算居中位置
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            # 移动窗口到计算出的位置
            self.move(window_geometry.topLeft())
            logging.info(f"主窗口已居中到屏幕位置: {window_geometry.topLeft().toTuple()}")
        except Exception as e:
            logging.warning(f"无法自动居中窗口: {e}", exc_info=True)
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

# 【修改】元数据结构添加 "default" 字段
SETTING_METADATA = {
    "General": {
        "app_name": {"widget": "lineedit", "label": "应用程序名称", "default": "Desktop Control & Monitoring Center"},
        "start_minimized": {"widget": "combobox", "label": "启动时最小化", "items": ["禁用", "启用"], "map": {"启用": "true", "禁用": "false"}, "default": "false"}
    },
    # 【新增】日志设置的元数据
    "Logging": {
        "level": {"widget": "combobox", "label": "日志级别", "items": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], "default": "INFO"}
    },
    "InfoService": {
        "host": {"widget": "lineedit", "label": "监听地址", "col": 0, "default": "0.0.0.0"},
        "port": {"widget": "spinbox", "label": "监听端口", "min": 1024, "max": 65535, "col": 0, "default": 9527},
        "enable_desktop_popup": {"widget": "combobox", "label": "桌面弹窗通知", "items": ["禁用", "启用"], "map": {"启用": "true", "禁用": "false"}, "col": 0, "default": "true"},
        "popup_timeout": {"widget": "spinbox", "label": "弹窗显示时长 (秒)", "min": 1, "max": 300, "col": 1, "default": 10},
        "notification_level": {"widget": "combobox", "label": "通知级别阈值", "items": ["INFO", "WARNING", "CRITICAL"], "col": 1, "default": "INFO"},
        "load_history_on_startup": {"widget": "combobox", "label": "启动时加载历史", "items": ["不加载", "加载最近50条", "加载最近100条", "加载最近500条"], "map": {"不加载": "0", "加载最近50条": "50", "加载最近100条": "100", "加载最近500条": "500"}, "col": 1, "default": "100"}
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

    def _create_setting_cards(self):
        """根据元数据动态创建所有设置卡片。"""
        # 【修改】确保卡片按预定顺序创建
        ordered_sections = ["General", "Logging", "InfoService"]
        for section in ordered_sections:
            if section in SETTING_METADATA:
                options_meta = SETTING_METADATA[section]
                card = QGroupBox(section)
                card.setStyleSheet("""
                    QGroupBox { font-size: 16px; font-weight: bold; color: #333; background-color: #fcfcfc; border: 1px solid #e0e0e0; border-radius: 8px; margin-top: 10px; }
                    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; background-color: #fcfcfc; }
                """)
                
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
        main_hbox = QHBoxLayout(parent_group)
        main_hbox.setSpacing(40)
        main_hbox.setContentsMargins(20, 30, 20, 20)

        column1_layout = QFormLayout()
        column1_layout.setSpacing(12)
        column2_layout = QFormLayout()
        column2_layout.setSpacing(12)

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
            editor_widget.setMaximumWidth(200)

        if editor_widget:
            form_layout.addRow(QLabel(f"{label_text}:"), editor_widget)
            self.editors[section_name][key] = editor_widget

    def _load_settings_to_ui(self):
        logging.info("正在同步全局设置页面UI...")
        for section, options in self.editors.items():
            for key, widget in options.items():
                meta = SETTING_METADATA[section][key]
                # 【修改】使用元数据中的 'default' 作为 fallback
                default_value = meta.get("default")
                if isinstance(default_value, int): default_value = str(default_value)
                
                current_value = self.config_service.get_value(section, key, fallback=default_value)

                if isinstance(widget, QLineEdit):
                    widget.setText(current_value)
                elif isinstance(widget, QSpinBox):
                    # 【修改】确保即使是默认值也能被正确处理
                    widget.setValue(int(current_value) if current_value and current_value.isdigit() else meta.get("min", 0))
                elif isinstance(widget, QComboBox):
                    if "map" in meta:
                        display_text = next((text for text, val in meta["map"].items() if val == str(current_value)), None)
                        # 如果找不到映射，尝试直接匹配文本
                        if display_text is None and current_value in meta["items"]:
                            display_text = current_value
                        # 如果还找不到，就用默认值的映射
                        if display_text is None:
                            display_text = next((text for text, val in meta["map"].items() if val == str(default_value)), meta["items"][0])
                        widget.setCurrentText(display_text)
                    else:
                        if current_value in meta["items"]:
                            widget.setCurrentText(current_value)
                        else:
                            widget.setCurrentText(str(default_value))


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
                QMessageBox.information(self, "成功", "所有设置已成功保存！\n部分设置（如日志级别）需要重启应用才能生效。")
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
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from pystray import MenuItem, Icon
from PIL import Image

class TrayManager(QObject):
    """
    负责管理系统托盘图标及其菜单。
    这是一个独立的组件，控制着应用的显示、隐藏和退出逻辑。
    """
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
        """
        【修改】在后台线程中启动托盘图标的事件监听，并增加异常处理。
        """
        try:
            self.tray_icon.run_detached()
            logging.info("系统托盘图标已在独立线程中运行。")
        except Exception as e:
            # 捕获 pystray 启动时可能发生的任何错误 (例如在无头服务器上)
            logging.critical(f"启动系统托盘图标失败: {e}", exc_info=True)
            self.quit_requested.emit()


    def show_window(self) -> None:
        """从托盘菜单显示并激活主窗口。"""
        logging.info("通过托盘菜单请求显示主窗口。")
        self.window.show()
        self.window.activateWindow()

    def quit_app(self) -> None:
        """
        安全地请求退出整个应用程序。
        """
        logging.info("通过托盘菜单请求退出应用程序...")
        
        self.tray_icon.stop()
        logging.info("pystray图标已停止。")
        
        logging.info("正在发射信号以触发应用程序的优雅关闭流程...")
        self.quit_requested.emit()
```

## exception_handler.py

```python
# desktop_center/src/utils/exception_handler.py
import sys
import logging
import traceback
from PySide6.QtWidgets import QMessageBox

def global_exception_hook(exctype, value, tb):
    """
    全局异常处理钩子。当任何线程中出现未被捕获的异常时，此函数将被调用。
    """
    # 格式化异常信息
    traceback_details = "".join(traceback.format_exception(exctype, value, tb))
    
    # 记录致命错误日志
    logging.critical(f"捕获到未处理的全局异常:\n{traceback_details}")

    # 准备向用户显示的消息
    error_message = (
        "应用程序遇到了一个严重错误，需要关闭。\n\n"
        "我们对此造成的不便深表歉意。\n\n"
        f"错误类型: {exctype.__name__}\n"
        f"错误信息: {value}\n\n"
        "详细信息已记录到 app.log 文件中，请联系技术支持。"
    )

    # 显示一个阻塞的错误消息框
    # 注意: 这个QMessageBox是在异常发生后创建的，可能在非GUI线程中。
    # Qt通常能处理这种情况，但最稳妥的方式是确保它在主线程显示。
    # 在这个简单场景下，直接显示通常是可行的。
    error_box = QMessageBox()
    error_box.setIcon(QMessageBox.Icon.Critical)
    error_box.setWindowTitle("应用程序严重错误")
    error_box.setText(error_message)
    error_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    error_box.exec()

    # 退出应用程序
    sys.exit(1)

def setup_exception_handler():
    """设置全局异常钩子。"""
    sys.excepthook = global_exception_hook
    logging.info("全局异常处理器已设置。")
```

## 目前需要做的
分析这个架构是否合理，如果合理，当前我提供的代码中是否有需要完善的点
