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
做好代码变更的版本日志，做好新增及变化代码相应的注释，严禁随意修改删除已有注释。
总结变更内容及其原因。
列出所有被修改的文件及每个文件的具体改动。如果有任何假设或风险，请明确标注以供评审。
最终提交的代码应该是涉及到代码变更的整个代码文件，禁止提供有折叠的不完整代码块。
### 提醒：
你不是副驾驶、助手或头脑风暴的参与者。你是负责高杠杆、生产安全级变更的高级工程师。请勿即兴设计或偏离规范。

## 项目新架构
desktop_center/
.
├── .gitignore
├── app.py
├── config.ini
├── icon.ico
├── icon.png
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── context.py
│   │   ├── plugin_interface.py
│   │   └── plugin_manager.py
│   ├── features/
│   │   ├── __init__.py
│   │   ├── alert_center/
│   │   │   ├── __init__.py
│   │   │   ├── database_extensions.py
│   │   │   ├── plugin.py
│   │   │   ├── README.md
│   │   │   ├── controllers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── alerts_page_controller.py
│   │   │   │   ├── history_controller.py
│   │   │   │   ├── statistics_dialog_controller.py
│   │   │   │   └── statistics/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── custom_analysis_controller.py
│   │   │   │       ├── hourly_stats_controller.py
│   │   │   │       ├── ip_activity_controller.py
│   │   │   │       ├── multidim_analysis_controller.py
│   │   │   │       └── type_stats_controller.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── custom_analysis_model.py
│   │   │   │   ├── history_model.py
│   │   │   │   └── statistics_model.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   └── alert_receiver.py
│   │   │   ├── views/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── alerts_page_view.py
│   │   │   │   ├── history_dialog_view.py
│   │   │   │   ├── statistics_dialog_view.py
│   │   │   │   └── statistics/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── custom_analysis_view.py
│   │   │   │       ├── hourly_stats_view.py
│   │   │   │       ├── ip_activity_view.py
│   │   │   │       ├── multidim_analysis_view.py
│   │   │   │       └── type_stats_view.py
│   │   │   └── widgets/
│   │   │       ├── __init__.py
│   │   │       ├── date_filter_widget.py
│   │   │       └── ip_filter_widget.py
│   │   └── window_arranger/
│   │       ├── __init__.py
│   │       ├── plugin.py
│   │       ├── README.md
│   │       ├── controllers/
│   │       │   ├── __init__.py
│   │       │   ├── arranger_controller.py
│   │       │   └── sorting_strategy_manager.py
│   │       ├── models/
│   │       │   ├── __init__.py
│   │       │   └── window_info.py
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   └── monitor_service.py
│   │       ├── sorting_strategies/
│   │       │   ├── __init__.py
│   │       │   ├── default_sort_strategy.py
│   │       │   ├── numeric_sort_strategy.py
│   │       │   └── sort_strategy_interface.py
│   │       └── views/
│   │           ├── __init__.py
│   │           ├── arranger_page_view.py
│   │           └── settings_dialog_view.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── config_service.py
│   │   ├── database_service.py
│   │   ├── notification_service.py
│   │   └── webhook_service.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── action_manager.py
│   │   ├── main_window.py
│   │   └── settings_page.py
│   └── utils/
│       ├── __init__.py
│       ├── exception_handler.py
│       └── tray_manager.py
└── tests/
    └── test_config_service.py

        
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
from PySide6.QtGui import QIcon 
import ctypes # 【新增】导入 ctypes 用于Windows AppUserModelID

# --- 1. 导入项目核心模块 ---
# 遵循先导入服务、再导入UI、最后导入管理器的逻辑顺序
from src.services.config_service import ConfigService
from src.services.database_service import DatabaseService
from src.services.notification_service import NotificationService
from src.services.webhook_service import WebhookService 
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

# 【新增】定义一个唯一的应用程序用户模型ID
APP_USER_MODEL_ID = "com.YourCompany.DesktopCenter.v1"


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
        
        # 【变更】为Windows设置AppUserModelID，以确保任务栏图标的正确关联
        if sys.platform == "win32":
            try:
                # 设置AppUserModelID必须在QApplication实例创建后、主窗口显示前
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
                logging.info(f"  - Windows AppUserModelID '{APP_USER_MODEL_ID}' 已设置。")
            except Exception as e:
                logging.warning(f"  - 无法设置Windows AppUserModelID: {e}")

        # 设置QApplication的全局图标，这将影响任务栏图标
        self.app.setWindowIcon(QIcon(self.png_icon_path)) 
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
        # 【新增】实例化 WebhookService 具体配置参数应该在插件平台设置
        self.webhook_service = WebhookService()
        logging.info("  - 核心后台服务 (Config, Database, Notification, Webhook) 初始化完成。") # 【修改】更新日志

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
            notification_service=self.notification_service,
            webhook_service=self.webhook_service
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
        # 【变更】将信号连接放在启动后台服务之前，避免竞态条件
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
            # 【变更】信号已在init阶段连接，此处只负责启动
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
        """
        【变更】执行集中的、安全的关闭流程，确保所有资源被正确释放。
        """
        logging.info("[STEP 6.0] 应用程序关闭流程开始...")
        
        logging.info("  - [6.1] 停止系统托盘图标...")
        # 【新增】将托盘图标的关闭操作集中到此处
        self.tray_manager.stop_icon()
        
        logging.info("  - [6.2] 关闭所有插件...")
        self.plugin_manager.shutdown_plugins()
        
        # 【新增】安全地关闭 WebhookService 线程池
        logging.info("  - [6.3] 清理 Webhook 服务线程池...")
        self.webhook_service.thread_pool.clear()
        self.webhook_service.thread_pool.waitForDone()

        logging.info("  - [6.4] 关闭数据库服务...")
        self.db_service.close()
        
        logging.info("[STEP 6.5] 应用程序关闭流程结束。")


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
    from src.services.webhook_service import WebhookService
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
    notification_service: 'NotificationService'
    webhook_service: 'WebhookService'
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






## notification_service.py

```python
# desktop_center/src/services/notification_service.py
import logging
import os
from plyer import notification
from src.services.config_service import ConfigService

class NotificationService:
    """
    负责管理和显示桌面弹窗通知的核心服务。
    此版本使用系统的原生通知功能，通过 'plyer' 库实现。
    """
    def __init__(self, app_name: str, app_icon: str, config_service: ConfigService):
        """
        初始化通知服务。

        Args:
            app_name (str): 应用程序的名称，将显示在通知中。
            app_icon (str): 指向应用程序图标文件的路径 (.ico for Windows)。
            config_service (ConfigService): 配置服务实例。
        """
        self.app_name = app_name
        self.app_icon = app_icon
        self.config_service = config_service
        logging.info("通知服务 (NotificationService) 初始化完成。")

    def show(self, title: str, message: str, level: str = 'INFO'):
        """
        供所有插件调用的公共接口，用于显示一个系统原生通知。

        Args:
            title (str): 通知的标题。
            message (str): 通知的主体内容。
            level (str, optional): 通知的级别（暂未使用，为未来扩展保留）。
        """
        # 1. 检查全局配置是否允许弹窗
        if self.config_service.get_value("InfoService", "enable_desktop_popup", "true").lower() != 'true':
            logging.info("桌面通知被全局禁用，本次通知已忽略。")
            return

        # 2. 检查通知级别是否满足阈值 (未来可扩展)
        # ...

        # 3. 调用plyer发送通知
        try:
            # 确保图标文件存在
            icon_path = self.app_icon if os.path.exists(self.app_icon) else ''
            
            timeout_str = self.config_service.get_value("InfoService", "popup_timeout", "10")
            timeout = int(timeout_str) if timeout_str.isdigit() else 10
            
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                app_icon=icon_path,
                timeout=timeout
            )
            logging.info(f"已发送系统通知: title='{title}'")
        except Exception as e:
            # plyer在某些环境下（如无GUI的服务器或缺少依赖）可能会失败
            logging.error(f"发送系统通知时发生错误: {e}", exc_info=True)
```

## webhook_service.py

```python
# desktop_center/src/services/webhook_service.py
import logging
import requests
from PySide6.QtCore import QObject, QRunnable, QThreadPool

class WebhookWorker(QRunnable):
    """
    一个在独立线程中发送 Webhook 请求的工作器，以避免阻塞调用方。
    """
    def __init__(self, url: str, payload: dict):
        super().__init__()
        self.url = url
        self.payload = payload

    def run(self):
        """执行 HTTP POST 请求。"""
        try:
            response = requests.post(self.url, json=self.payload, timeout=5)
            response.raise_for_status() # 如果状态码不是 2xx，则抛出异常
            logging.info(f"Webhook 已成功推送到 {self.url}，响应: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"推送 Webhook 到 {self.url} 失败: {e}")

class WebhookService(QObject):
    """
    平台级共享服务，用于异步发送 Webhook (HTTP POST) 请求。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_pool = QThreadPool()
        # 设置线程池的最大线程数，以防滥用
        self.thread_pool.setMaxThreadCount(5) 
        logging.info("Webhook 服务 (WebhookService) 初始化完成。")

    def push(self, url: str, payload: dict):
        """
        异步地将一个 JSON payload 推送到指定的 URL。
        
        Args:
            url (str): 目标 URL。
            payload (dict): 要作为 JSON 发送的数据。
        """
        if not url or not url.startswith(('http://', 'https://')):
            logging.warning(f"无效的 Webhook URL: '{url}'，推送已取消。")
            return
            
        worker = WebhookWorker(url, payload)
        self.thread_pool.start(worker)
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
        "start_minimized": {"widget": "combobox", "label": "启动时最小化", "items": ["禁用", "启用"], "map": {"启用": "true", "禁用": "false"}, "default": "false"},
        "show_startup_notification": {"widget": "combobox", "label": "显示启动通知", "items": ["禁用", "启用"], "map": {"启用": "true", "禁用": "false"}, "default": "true"}
    },
    # 【新增】日志设置的元数据，上面的notification也是本次新添加的
    "Logging": {
        "level": {"widget": "combobox", "label": "日志级别", "items": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], "default": "INFO"}
    },
    # 【新增】Webhook 默认设置的元数据
    "WebhookDefaults": {
        "default_host": {"widget": "lineedit", "label": "默认推送主机", "default": "127.0.0.1"},
        "default_port": {"widget": "spinbox", "label": "默认推送端口", "min": 1, "max": 65535, "default": 5000}
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
        # 【修改】确保新卡片按预定顺序创建
        ordered_sections = ["General", "Logging", "WebhookDefaults", "InfoService"]
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
        在后台线程中启动托盘图标的事件监听，并增加异常处理。
        """
        try:
            self.tray_icon.run_detached()
            logging.info("系统托盘图标已在独立线程中运行。")
        except Exception as e:
            # 捕获 pystray 启动时可能发生的任何错误 (例如在无头服务器上)
            logging.critical(f"启动系统托盘图标失败: {e}", exc_info=True)
            self.quit_requested.emit()

    def stop_icon(self) -> None:
        """【新增】停止pystray图标的公共方法，由应用协调器调用。"""
        if self.tray_icon.visible:
            self.tray_icon.stop()
            logging.info("pystray图标已停止。")

    def show_window(self) -> None:
        """从托盘菜单显示并激活主窗口。"""
        logging.info("通过托盘菜单请求显示主窗口。")
        self.window.show()
        self.window.activateWindow()

    def quit_app(self) -> None:
        """
        【变更】安全地请求退出整个应用程序。
        此方法现在只负责发出信号，将实际的关闭操作完全委托给应用协调器。
        """
        logging.info("通过托盘菜单请求退出应用程序...")
        
        # 【变更】移除此处的stop调用，关闭操作由ApplicationOrchestrator.shutdown统一处理。
        # self.tray_icon.stop()
        
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







## window_arranger
### plugin.py
```python
# desktop_center/src/features/window_arranger/plugin.py
import logging
from PySide6.QtWidgets import QWidget
from src.core.plugin_interface import IFeaturePlugin
from src.core.context import ApplicationContext
from src.features.window_arranger.views.arranger_page_view import ArrangerPageView
from src.features.window_arranger.controllers.arranger_controller import ArrangerController

class WindowArrangerPlugin(IFeaturePlugin):
    """
    桌面窗口管理插件的入口。
    实现了 IFeaturePlugin 接口，负责插件的生命周期管理。
    """
    def name(self) -> str:
        """返回插件的唯一内部名称。"""
        return "window_arranger"

    def display_name(self) -> str:
        """返回插件在用户界面上显示的名称。"""
        return "桌面窗口管理"

    def load_priority(self) -> int:
        """
        返回插件的加载优先级。
        """
        return 110

    def initialize(self, context: ApplicationContext):
        """
        初始化窗口排列插件。
        """
        super().initialize(context)
        logging.info(f"  - 插件 '{self.name()}': 正在初始化视图和控制器...")
        self.page_widget = ArrangerPageView()
        self.controller = ArrangerController(self.context, self.page_widget)
        logging.info(f"  - 插件 '{self.name()}' 初始化完成。")

    def get_background_services(self) -> list:
        """此插件的核心后台服务(MonitorService)由其控制器管理，因此这里返回空。"""
        return []

    def shutdown(self):
        """
        在应用程序关闭时，安全地执行插件的关闭操作。
        """
        logging.info(f"  - 插件 '{self.name()}': 正在执行关闭前操作...")
        if hasattr(self, 'controller') and self.controller:
            self.controller._save_settings_from_view()
            if hasattr(self.controller, 'shutdown'):
                self.controller.shutdown()
        super().shutdown()
```
### arranger_controller.py
```python
# desktop_center/src/features/window_arranger/controllers/arranger_controller.py
import logging
import time
from datetime import datetime
import math
import pygetwindow as gw
import psutil
import win32process
from PySide6.QtWidgets import QDialog, QApplication
from PySide6.QtCore import Signal, QObject
from src.core.context import ApplicationContext
from src.features.window_arranger.views.arranger_page_view import ArrangerPageView
from src.features.window_arranger.views.settings_dialog_view import SettingsDialog
from src.features.window_arranger.models.window_info import WindowInfo
from src.features.window_arranger.controllers.sorting_strategy_manager import SortingStrategyManager
from src.features.window_arranger.services.monitor_service import MonitorService
from PySide6.QtGui import QScreen

class ArrangerController(QObject):
    """
    负责窗口排列功能的业务逻辑。
    """
    def __init__(self, context: ApplicationContext, view: ArrangerPageView):
        super().__init__()
        self.context = context
        self.view = view
        self.detected_windows: list[WindowInfo] = []
        self.strategy_manager = SortingStrategyManager()
        self.monitor_service = MonitorService(self.context, self)

        # 连接主视图的信号
        self.view.detect_windows_requested.connect(self.detect_windows)
        self.view.open_settings_requested.connect(self.open_settings_dialog)
        self.view.toggle_monitoring_requested.connect(self.toggle_monitoring)
        self.view.arrange_grid_requested.connect(self.arrange_windows_grid)
        self.view.arrange_cascade_requested.connect(self.arrange_windows_cascade)
        
        # 连接后台服务的信号
        self.monitor_service.status_updated.connect(self.view.status_label.setText)
        self.monitor_service.trigger_rearrange.connect(self.template_rearrange)

        self._load_filter_settings()
        self._initial_monitor_start()

    def _initial_monitor_start(self):
        """根据配置决定是否在启动时开启监控。"""
        if self.context.config_service.get_value("WindowArranger", "auto_monitor_enabled", "false") == 'true':
            self.view.monitor_toggle_button.setChecked(True)

    def toggle_monitoring(self, checked: bool):
        """启动或停止后台监控服务。"""
        self.context.config_service.set_option("WindowArranger", "auto_monitor_enabled", str(checked).lower())
        self.context.config_service.save_config()
        
        if checked:
            if not self.detected_windows:
                self._show_notification_if_enabled("无法启动监控", "请先至少成功检测一次窗口，以确定监控目标。")
                self.view.set_monitoring_status(False)
                return
            
            if not self.monitor_service.isRunning():
                self.monitor_service.update_snapshot_states(self.detected_windows)
                self.monitor_service.start()
        else:
            if self.monitor_service.isRunning():
                self.monitor_service.stop()
        
        self.view.set_monitoring_status(self.monitor_service.isRunning())

    def open_settings_dialog(self):
        """打开设置对话框，并在保存后自动重新检测窗口。"""
        dialog = SettingsDialog(self.context, self.strategy_manager, self.view)
        
        if dialog.exec() == QDialog.Accepted:
            logging.info("[WindowArranger] 设置已保存，将自动重新检测窗口以应用新设置...")
            # 【修改】自动触发的检测不应保存UI状态
            self.detect_windows(from_user_action=False)
        else:
            logging.info("[WindowArranger] 设置对话框已取消。")

    def _load_filter_settings(self):
        """从配置加载过滤相关的设置并更新主视图UI。"""
        config = self.context.config_service
        self.view.filter_keyword_input.setText(config.get_value("WindowArranger", "filter_keyword", ""))
        self.view.process_name_input.setText(config.get_value("WindowArranger", "process_name_filter", ""))
        self.view.exclude_title_input.setText(config.get_value("WindowArranger", "exclude_title_keywords", ""))

    def _save_settings_from_view(self):
        """仅保存主视图上的过滤相关设置。"""
        filter_keyword = self.view.get_filter_keyword()
        process_name_filter = self.view.get_process_name_filter()
        exclude_keywords = self.view.get_exclude_keywords()
        config = self.context.config_service
        config.set_option("WindowArranger", "filter_keyword", filter_keyword)
        config.set_option("WindowArranger", "process_name_filter", process_name_filter)
        config.set_option("WindowArranger", "exclude_title_keywords", exclude_keywords)
        config.save_config()
        
    def _show_notification_if_enabled(self, title: str, message: str):
        """如果配置允许，则显示通知。"""
        if self.context.config_service.get_value("WindowArranger", "enable_notifications", "true") == 'true':
            self.context.notification_service.show(title=title, message=message)
    
    def detect_windows(self, from_user_action=True):
        """
        检测并使用选定的策略对窗口进行排序。
        Args:
            from_user_action (bool): 如果为True，则表示由用户直接点击按钮触发，会保存当前UI设置。
                                     如果为False，则表示由程序自动触发，不会保存UI设置。
        """
        logging.info("[WindowArranger] 正在检测窗口...")
        # 【修改】只有用户直接操作才保存设置
        if from_user_action:
            self._save_settings_from_view()
            logging.info("[WindowArranger] 用户触发检测，过滤设置已保存。")
        
        config = self.context.config_service
        title_keyword_str = config.get_value("WindowArranger", "filter_keyword", "")
        process_keyword_str = config.get_value("WindowArranger", "process_name_filter", "")
        exclude_keywords_str = config.get_value("WindowArranger", "exclude_title_keywords", "")
        
        title_keywords = [kw.strip().lower() for kw in title_keyword_str.split(',') if kw.strip()]
        process_keywords = [kw.strip().lower() for kw in process_keyword_str.split(',') if kw.strip()]
        exclude_keywords_list = [kw.strip().lower() for kw in exclude_keywords_str.split(',') if kw.strip()]
        
        if not title_keywords and not process_keywords:
            self._show_notification_if_enabled(title="检测失败", message="请输入窗口标题关键词或进程名称进行过滤。")
            self.view.update_detected_windows_list([])
            self.view.summary_label.setText("无有效过滤条件，请重新输入。")
            return

        all_windows = gw.getAllWindows()
        unfiltered_windows = []
        app_main_window_id = self.context.main_window.winId()
        
        for win in all_windows:
            if not (win.title and win.visible and not win.isMinimized and win._hWnd != app_main_window_id): continue
            current_window_title = win.title
            if exclude_keywords_list and any(ex_kw in current_window_title.lower() for ex_kw in exclude_keywords_list): continue
            is_title_match = not title_keywords or any(kw in current_window_title.lower() for kw in title_keywords)
            current_process_name, is_process_match = "[未知进程]", not process_keywords
            if process_keywords:
                try:
                    thread_id, pid = win32process.GetWindowThreadProcessId(win._hWnd)
                    if pid != 0:
                        process = psutil.Process(pid)
                        current_process_name = process.name()
                        if any(kw in current_process_name.lower() for kw in process_keywords): is_process_match = True
                        else: is_process_match = False
                except Exception: is_process_match = False
            
            should_add = (process_keywords and is_process_match and (is_title_match or not title_keywords)) or \
                         (title_keywords and not process_keywords and is_title_match)
            if should_add:
                unfiltered_windows.append(WindowInfo(
                    title=win.title, left=win.left, top=win.top, width=win.width, height=win.height,
                    process_name=current_process_name, pygw_window_obj=win
                ))

        strategy_name = config.get_value("WindowArranger", "sorting_strategy", "默认排序 (按标题)")
        strategy = self.strategy_manager.get_strategy(strategy_name)
        if not strategy:
            logging.error(f"未找到排序策略 '{strategy_name}'，将使用默认策略。")
            strategy = self.strategy_manager.get_strategy("默认排序 (按标题)")
            if not strategy:
                self.detected_windows = unfiltered_windows
                self.view.update_detected_windows_list(self.detected_windows)
                self._show_notification_if_enabled(title="排序失败", message="无法加载任何排序策略。")
                return

        self.detected_windows = strategy.sort(unfiltered_windows)
        
        num_detected = len(self.detected_windows)
        color_a, color_b, color_c = "#333", "#005a9e", "#5cb85c"
        summary_text = f"<span style='color: {color_a};'>检测结果 (</span><span style='color: {color_b}; font-weight: bold;'>{num_detected}</span><span style='color: {color_a};'> 个) | 排序: </span><span style='color: {color_c};'>{strategy_name}</span>"
        self.view.summary_label.setText(summary_text)
        
        self.view.update_detected_windows_list(self.detected_windows)
        self._show_notification_if_enabled(title="窗口检测完成", message=f"已检测到 {num_detected} 个符合条件的窗口。")
        self.view.status_label.setText("检测完成，准备排列。")

    def _arrange_windows(self, arrange_function):
        """通用排列逻辑，包含延时和状态更新。"""
        delay_ms = int(self.context.config_service.get_value("WindowArranger", "animation_delay", "50"))
        delay_s = delay_ms / 1000.0
        windows_to_arrange = self.view.get_selected_window_infos()
        if not windows_to_arrange:
            self._show_notification_if_enabled(title="窗口排列失败", message="没有选择可排列的窗口。")
            return None
        
        arranged_count = arrange_function(windows_to_arrange, delay_s)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.status_label.setText(f"上次排列于 {timestamp} 完成 ({arranged_count} 个窗口)")
        if self.monitor_service.isRunning():
            self.monitor_service.update_snapshot_states(windows_to_arrange)
        
        return arranged_count

    def arrange_windows_grid(self):
        """将选定的窗口按网格布局排列。"""
        logging.info("[WindowArranger] 正在按网格排列...")
        count = self._arrange_windows(self._get_grid_arrangement_function())
        if count is not None:
            self._show_notification_if_enabled(title="网格排列完成", message=f"已成功排列 {count} 个窗口。")

    def arrange_windows_cascade(self):
        """将选定的窗口按级联布局排列。"""
        logging.info("[WindowArranger] 正在按级联排列...")
        count = self._arrange_windows(self._get_cascade_arrangement_function())
        if count is not None:
            self._show_notification_if_enabled(title="级联排列完成", message=f"已成功排列 {count} 个窗口。")
    
    def template_rearrange(self):
        """由MonitorService在模板模式下触发，执行一次完整的检测和排列。"""
        logging.info("[MonitorService-Template] 触发模板化重排...")
        # 【修改】后台任务触发的检测不保存UI状态
        self.detect_windows(from_user_action=False)
        
        all_detected_windows = self.detected_windows
        if not all_detected_windows:
            return

        grid_arranger = self._get_grid_arrangement_function()
        grid_arranger(all_detected_windows, 0)
        self.monitor_service.update_snapshot_states(all_detected_windows)

    def _get_grid_arrangement_function(self):
        """返回一个闭包，该闭包封装了网格排列的完整逻辑。"""
        def do_grid_arrangement(windows, delay):
            config = self.context.config_service; rows = int(config.get_value("WindowArranger", "grid_rows", "2")); cols = int(config.get_value("WindowArranger", "grid_cols", "3")); margin_top = int(config.get_value("WindowArranger", "grid_margin_top", "0")); margin_bottom = int(config.get_value("WindowArranger", "grid_margin_bottom", "0")); margin_left = int(config.get_value("WindowArranger", "grid_margin_left", "0")); margin_right = int(config.get_value("WindowArranger", "grid_margin_right", "0")); spacing_h = int(config.get_value("WindowArranger", "grid_spacing_h", "10")); spacing_v = int(config.get_value("WindowArranger", "grid_spacing_v", "10")); grid_direction = config.get_value("WindowArranger", "grid_direction", "row-major"); target_screen_index = int(config.get_value("WindowArranger", "target_screen_index", "0")); screens = self.context.app.screens()
            if not (0 <= target_screen_index < len(screens)): return 0
            target_screen = screens[target_screen_index]; screen_geometry = target_screen.geometry(); screen_x_offset = screen_geometry.x(); screen_y_offset = screen_geometry.y(); usable_screen_width = screen_geometry.width(); usable_screen_height = screen_geometry.height()
            if len(windows) > rows * cols: logging.warning(f"窗口数量({len(windows)})超过网格槽位。")
            available_width = usable_screen_width - margin_left - margin_right - (cols - 1) * spacing_h; available_height = usable_screen_height - margin_top - margin_bottom - (rows - 1) * spacing_v; avg_width = available_width / cols if cols > 0 else available_width; avg_height = available_height / rows if rows > 0 else available_height; avg_width, avg_height = max(100, int(avg_width)), max(100, int(avg_height))
            arranged_count = 0
            for i, window_info in enumerate(windows):
                if i >= rows * cols: break
                row, col = (i // cols, i % cols) if grid_direction == "row-major" else (i % rows, i // rows)
                x = screen_x_offset + margin_left + col * (avg_width + spacing_h); y = screen_y_offset + margin_top + row * (avg_height + spacing_v)
                try:
                    window_info.pygw_window_obj.restore(); window_info.pygw_window_obj.moveTo(int(x), int(y)); window_info.pygw_window_obj.resizeTo(avg_width, avg_height); arranged_count += 1
                    if delay > 0: QApplication.processEvents(); time.sleep(delay)
                except Exception as e: logging.error(f"排列窗口 '{window_info.title}' 失败: {e}", exc_info=True)
            return arranged_count
        return do_grid_arrangement

    def _get_cascade_arrangement_function(self):
        """返回一个闭包，该闭包封装了级联排列的完整逻辑。"""
        def do_cascade_arrangement(windows, delay):
            config = self.context.config_service; x_offset = int(config.get_value("WindowArranger", "cascade_x_offset", "30")); y_offset = int(config.get_value("WindowArranger", "cascade_y_offset", "30")); target_screen_index = int(config.get_value("WindowArranger", "target_screen_index", "0")); screens = self.context.app.screens()
            if not (0 <= target_screen_index < len(screens)): return 0
            target_screen = screens[target_screen_index]; screen_geometry = target_screen.geometry(); screen_x, screen_y, usable_w, usable_h = screen_geometry.x(), screen_geometry.y(), screen_geometry.width(), screen_geometry.height()
            base_w = max(300, min(int(usable_w * 0.5), int(usable_w * 0.8))); base_h = max(200, min(int(usable_h * 0.5), int(usable_h * 0.8)))
            arranged_count = 0
            for i, window_info in enumerate(windows):
                start_x, start_y = 20, 20; curr_x = start_x + (i * x_offset); curr_y = start_y + (i * y_offset)
                if curr_x + base_w > usable_w - 10: curr_x = start_x + ((curr_x + base_w - (usable_w - 10)) % (usable_w - base_w - start_x))
                if curr_y + base_h > usable_h - 10: curr_y = start_y + ((curr_y + base_h - (usable_h - 10)) % (usable_h - base_h - start_y))
                x = screen_x + curr_x; y = screen_y + curr_y
                try:
                    window_info.pygw_window_obj.restore(); window_info.pygw_window_obj.moveTo(int(x), int(y)); window_info.pygw_window_obj.resizeTo(base_w, base_h); arranged_count += 1
                    if delay > 0: QApplication.processEvents(); time.sleep(delay)
                except Exception as e: logging.error(f"排列窗口 '{window_info.title}' 失败: {e}", exc_info=True)
            return arranged_count
        return do_cascade_arrangement

    def shutdown(self):
        """由插件的 shutdown 方法调用，确保后台线程被安全停止。"""
        if self.monitor_service.isRunning():
            self.monitor_service.stop()
```
### sorting_strategy_manager.py
```python
# desktop_center/src/features/window_arranger/controllers/sorting_strategy_manager.py
import importlib
import pkgutil
import logging
from typing import Dict, List, Type
from src.features.window_arranger.sorting_strategies.sort_strategy_interface import ISortStrategy

class SortingStrategyManager:
    """
    负责发现、加载和管理所有排序策略。
    """
    def __init__(self):
        self.strategies: Dict[str, Type[ISortStrategy]] = {}
        self._load_strategies()

    def _load_strategies(self):
        """
        动态扫描 sorting_strategies 包，加载所有实现了 ISortStrategy 接口的类。
        """
        import src.features.window_arranger.sorting_strategies as strategies_package
        
        for module_info in pkgutil.walk_packages(path=strategies_package.__path__, prefix=strategies_package.__name__ + '.'):
            try:
                module = importlib.import_module(module_info.name)
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if isinstance(item, type) and issubclass(item, ISortStrategy) and item is not ISortStrategy:
                        # 使用策略的 name 属性作为键
                        strategy_instance = item()
                        if strategy_instance.name in self.strategies:
                            logging.warning(f"排序策略名称冲突: '{strategy_instance.name}' 已存在。将覆盖。")
                        self.strategies[strategy_instance.name] = item
                        logging.info(f"[WindowArranger] 已加载排序策略: '{strategy_instance.name}'")
            except Exception as e:
                logging.error(f"加载排序策略模块 {module_info.name} 时失败: {e}", exc_info=True)

    def get_strategy_names(self) -> List[str]:
        """获取所有已加载策略的名称列表。"""
        return sorted(list(self.strategies.keys()))

    def get_strategy(self, name: str) -> ISortStrategy | None:
        """
        根据名称获取一个排序策略的实例。
        
        Args:
            name (str): 策略的显示名称。

        Returns:
            ISortStrategy | None: 策略的实例，如果未找到则返回 None。
        """
        strategy_class = self.strategies.get(name)
        if strategy_class:
            return strategy_class()
        return None
```
### window_info.py
```python
# desktop_center/src/features/window_arranger/models/window_info.py
from dataclasses import dataclass

@dataclass
class WindowInfo:
    """数据类，用于存储检测到的窗口信息。
    pygw_window_obj 字段存储 pygetwindow.Window 对象的引用，以便直接操作。
    """
    title: str
    left: int
    top: int
    width: int
    height: int
    process_name: str # 【新增】进程名
    pygw_window_obj: object # 存储 pygetwindow.Window 实例
```
### monitor_service.py
```python
# desktop_center/src/features/window_arranger/services/monitor_service.py
import logging
import time
from datetime import datetime
import pygetwindow as gw
import win32process
import psutil
from PySide6.QtCore import QThread, Signal, QRect
from src.core.context import ApplicationContext
from src.features.window_arranger.models.window_info import WindowInfo

class MonitorService(QThread):
    """
    后台监控服务，用于自动检测窗口变化并执行排列。
    支持两种模式：'template' (模板化) 和 'snapshot' (快照式)。
    """
    status_updated = Signal(str)
    trigger_rearrange = Signal()
    
    def __init__(self, context: ApplicationContext, controller, parent=None):
        super().__init__(parent)
        self.context = context
        self.controller = controller
        self.running = False
        self._snapshot_states = {} # {hWnd: QRect}

    def run(self):
        """线程主循环。"""
        self.running = True
        logging.info("[MonitorService] 自动监测服务已启动。")
        self.status_updated.emit("监控中...")

        while self.running:
            config = self.context.config_service
            interval = int(config.get_value("WindowArranger", "monitor_interval", "5"))
            time.sleep(interval)

            if not self.running: 
                break

            logging.debug("[MonitorService] 开始新一轮监测...")
            self._check_and_correct_windows()

        logging.info("[MonitorService] 自动监测服务已停止。")
        self.status_updated.emit("监控已停止")

    def stop(self):
        """停止线程循环。"""
        self.running = False
        logging.info("[MonitorService] 正在请求停止监测服务...")
        self.quit()
        self.wait(2000)

    def update_snapshot_states(self, windows: list[WindowInfo]):
        """
        由外部（ArrangerController）调用，以更新“快照模式”的期望状态。
        """
        self._snapshot_states.clear()
        for win_info in windows:
            win = win_info.pygw_window_obj
            try:
                # 【修复】通过访问一个属性并捕获异常来检查句柄有效性
                _ = win.visible 
                self._snapshot_states[win._hWnd] = QRect(win.left, win.top, win.width, win.height)
            except gw.PyGetWindowException:
                logging.warning(f"更新快照时，窗口 '{win.title}' 句柄已失效，已忽略。")
            except Exception as e:
                # 捕获其他可能的未知错误
                logging.error(f"更新快照时，处理窗口 '{win.title}' 发生未知错误: {e}")

        logging.info(f"[MonitorService] 快照状态已更新，当前管理 {len(self._snapshot_states)} 个窗口。")
    
    def _check_and_correct_windows(self):
        """核心监测与校正逻辑，根据配置的模式执行。"""
        mode = self.context.config_service.get_value("WindowArranger", "monitor_mode", "template")
        
        if mode == 'template':
            self._execute_template_mode_check()
        elif mode == 'snapshot':
            self._execute_snapshot_mode_check()
        else:
            logging.warning(f"未知的监控模式: '{mode}'")

    def _execute_snapshot_mode_check(self):
        """执行快照模式的检查与恢复。"""
        if not self._snapshot_states:
            logging.debug("[MonitorService-Snapshot] 快照为空，跳过监测。")
            return

        current_windows_map = {win._hWnd: win for win in gw.getAllWindows() if win.title and win.visible}
        
        closed_hwnds = set(self._snapshot_states.keys()) - set(current_windows_map.keys())
        if closed_hwnds:
            for hwnd in list(closed_hwnds):
                title = f"hWnd={hwnd} (已关闭)" # 因为窗口已关闭，无法再获取标题
                message = f"窗口 '{title}' 已关闭 (快照模式)。"
                logging.info(f"[MonitorService] {message}")
                self._push_event("Window Closed (Snapshot)", message, "INFO")
                del self._snapshot_states[hwnd]
            self.status_updated.emit(f"窗口关闭，快照剩余 {len(self._snapshot_states)} 个。")

        for hwnd, expected_rect in list(self._snapshot_states.items()):
            if hwnd in current_windows_map:
                current_win = current_windows_map[hwnd]
                try:
                    current_rect = QRect(current_win.left, current_win.top, current_win.width, current_win.height)
                    
                    if not self._is_rect_close(current_rect, expected_rect):
                        message = f"窗口 '{current_win.title}' 位置已从快照恢复。"
                        logging.info(f"[MonitorService] {message} 从 {current_rect.getRect()} -> {expected_rect.getRect()}")
                        self._push_event("Window Corrected (Snapshot)", message, "INFO")
                        
                        current_win.restore()
                        current_win.moveTo(expected_rect.left(), expected_rect.top())
                        current_win.resizeTo(expected_rect.width(), expected_rect.height())
                        self.status_updated.emit(f"已校正窗口 '{current_win.title}'")
                except gw.PyGetWindowException:
                     # 在检查和校正之间，窗口可能瞬间关闭
                     logging.warning(f"校正窗口 '{current_win.title}' 时句柄失效，已跳过。")
                except Exception as e:
                    logging.error(f"校正窗口 '{current_win.title}' 失败: {e}")

    def _execute_template_mode_check(self):
        """执行模板模式的检查与重排。"""
        logging.debug("[MonitorService-Template] 执行模板化监测。")
        self.trigger_rearrange.emit()

    def _is_rect_close(self, rect1: QRect, rect2: QRect, tolerance=2):
        """比较两个矩形元组是否在容差范围内近似相等。"""
        return (abs(rect1.left() - rect2.left()) <= tolerance and
                abs(rect1.top() - rect2.top()) <= tolerance and
                abs(rect1.width() - rect2.width()) <= tolerance and
                abs(rect1.height() - rect2.height()) <= tolerance)

    def _push_event(self, event_type: str, message: str, severity: str):
        """构建并发送 Webhook 事件。"""
        config = self.context.config_service
        if config.get_value("WindowArranger", "enable_push", "false").lower() != 'true':
            return
            
        host = config.get_value("WindowArranger", "push_host").strip() or config.get_value("WebhookDefaults", "default_host", "127.0.0.1").strip()
        port = config.get_value("WindowArranger", "push_port").strip() or config.get_value("WebhookDefaults", "default_port", "5000").strip()
        path = config.get_value("WindowArranger", "push_path", "/alert").strip()
        url = f"http://{host}:{port}{path if path.startswith('/') else '/' + path}"
        
        payload = {"type": event_type, "message": message, "severity": severity, "source": "WindowArrangerPlugin", "timestamp": datetime.now().isoformat()}
        self.context.webhook_service.push(url, payload)
```
### default_sort_strategy.py
```python
# desktop_center/src/features/window_arranger/sorting_strategies/default_sort_strategy.py
from typing import List
from .sort_strategy_interface import ISortStrategy
from src.features.window_arranger.models.window_info import WindowInfo

class DefaultSortStrategy(ISortStrategy):
    """
    默认的排序策略：按窗口标题升序，然后按进程名升序。
    """
    @property
    def name(self) -> str:
        return "默认排序 (按标题)"

    def sort(self, windows: List[WindowInfo]) -> List[WindowInfo]:
        return sorted(windows, key=lambda w: (w.title.lower(), w.process_name.lower()))
```
### numeric_sort_strategy.py
```python
# desktop_center/src/features/window_arranger/sorting_strategies/numeric_sort_strategy.py
import re
from typing import List, Tuple
from .sort_strategy_interface import ISortStrategy
from src.features.window_arranger.models.window_info import WindowInfo

class NumericSortStrategy(ISortStrategy):
    """
    按窗口标题中提取的数字进行排序的策略。
    例如，从 "1-41704 - 完全控制" 中提取 141704。
    """
    @property
    def name(self) -> str:
        return "按标题数字排序"

    def _extract_numeric_key(self, title: str) -> Tuple[int, str]:
        """
        辅助方法，从标题中提取数字作为排序键。
        
        Returns:
            A tuple (numeric_key, original_title).
            numeric_key is the extracted number, or float('inf') if no number is found.
            original_title is for stable secondary sorting.
        """
        # 使用正则表达式找到所有数字字符
        digits = re.findall(r'\d', title)
        
        if digits:
            try:
                # 将找到的数字字符拼接起来并转换为整数
                numeric_value = int("".join(digits))
                return (numeric_value, title)
            except (ValueError, TypeError):
                # 如果转换失败（不太可能发生，但作为保障），则视为无数字
                return (float('inf'), title)
        else:
            # 如果标题中没有数字，则将其排在最后
            return (float('inf'), title)

    def sort(self, windows: List[WindowInfo]) -> List[WindowInfo]:
        """
        使用提取的数字作为主键，对窗口列表进行排序。
        """
        return sorted(windows, key=lambda w: self._extract_numeric_key(w.title))
```
### sort_strategy_interface.py
```python
# desktop_center/src/features/window_arranger/sorting_strategies/sort_strategy_interface.py
from abc import ABC, abstractmethod
from typing import List
from src.features.window_arranger.models.window_info import WindowInfo

class ISortStrategy(ABC):
    """
    排序策略的接口。所有排序方案都必须实现这个接口。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        返回策略的显示名称，将用于UI下拉框中。
        例如："默认排序 (按标题)"
        """
        pass

    @abstractmethod
    def sort(self, windows: List[WindowInfo]) -> List[WindowInfo]:
        """
        对窗口信息列表进行排序。
        
        Args:
            windows (List[WindowInfo]): 未排序的窗口信息列表。

        Returns:
            List[WindowInfo]: 已排序的窗口信息列表。
        """
        pass
```
### arranger_page_view.py
```python
# desktop_center/src/features/window_arranger/views/arranger_page_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                   QGroupBox, QFormLayout, QLabel,
                                   QListWidget, QListWidgetItem, QLineEdit,
                                   QAbstractItemView)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon

class ArrangerPageView(QWidget):
    """
    桌面窗口排列功能的主UI页面。
    """
    detect_windows_requested = Signal()
    open_settings_requested = Signal()
    toggle_monitoring_requested = Signal(bool)
    arrange_grid_requested = Signal()
    arrange_cascade_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("窗口排列器")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        header_layout = QHBoxLayout()
        title_label = QLabel("桌面窗口排列")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #333;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.monitor_toggle_button = QPushButton("启动自动监控")
        self.monitor_toggle_button.setCheckable(True)
        self.monitor_toggle_button.setMinimumHeight(30)
        self.monitor_toggle_button.toggled.connect(self.toggle_monitoring_requested.emit)
        self.set_monitoring_status(False)
        header_layout.addWidget(self.monitor_toggle_button)
        
        self.settings_button = QPushButton("排列设置")
        try:
            settings_icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView)
            self.settings_button.setIcon(settings_icon)
        except:
            pass
        self.settings_button.setMinimumHeight(30)
        self.settings_button.clicked.connect(self.open_settings_requested.emit)
        header_layout.addWidget(self.settings_button)
        main_layout.addLayout(header_layout)
        
        filter_group = QGroupBox("窗口过滤")
        filter_group.setStyleSheet("QGroupBox { font-size: 16px; font-weight: bold; color: #333; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; }")
        filter_layout = QFormLayout(filter_group)
        filter_layout.setSpacing(12)
        filter_layout.setContentsMargins(20, 30, 20, 20)
        
        self.filter_keyword_input = QLineEdit()
        self.filter_keyword_input.setPlaceholderText("输入标题关键词, 用逗号分隔多个")
        filter_layout.addRow("标题关键词:", self.filter_keyword_input)

        self.process_name_input = QLineEdit()
        self.process_name_input.setPlaceholderText("输入进程名, 用逗号分隔多个")
        filter_layout.addRow("进程名称:", self.process_name_input)
        
        self.exclude_title_input = QLineEdit()
        self.exclude_title_input.setPlaceholderText("输入要排除的标题关键词，用逗号分隔")
        filter_layout.addRow("排除标题包含:", self.exclude_title_input)
        
        main_layout.addWidget(filter_group)

        self.windows_list_group = QGroupBox()
        self.windows_list_group.setStyleSheet("QGroupBox { margin-top: 10px; }")
        windows_list_layout = QVBoxLayout(self.windows_list_group)
        windows_list_layout.setContentsMargins(15, 15, 15, 15)

        self.summary_label = QLabel("请先检测窗口")
        self.summary_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        windows_list_layout.addWidget(self.summary_label)

        self.detected_windows_list_widget = QListWidget()
        self.detected_windows_list_widget.setMinimumHeight(200)
        self.detected_windows_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.detected_windows_list_widget.setStyleSheet("QListWidget { border: 1px solid #ddd; border-radius: 5px; padding: 5px; } QListWidget::item { padding: 5px; } QListWidget::indicator { width: 16px; height: 16px; }")
        windows_list_layout.addWidget(self.detected_windows_list_widget)
        
        detect_button = QPushButton("检测桌面窗口")
        detect_button.setMinimumHeight(30)
        detect_button.setStyleSheet("QPushButton { font-size: 14px; background-color: #5cb85c; color: white; border: none; border-radius: 5px; padding: 5px 15px; } QPushButton:hover { background-color: #4cae4c; } QPushButton:pressed { background-color: #449d44; }")
        detect_button.clicked.connect(self.detect_windows_requested.emit)
        windows_list_layout.addWidget(detect_button)
        main_layout.addWidget(self.windows_list_group)
        
        action_buttons_layout = QHBoxLayout()
        self.arrange_grid_button = QPushButton("网格排列")
        self.arrange_grid_button.setMinimumHeight(35)
        self.arrange_grid_button.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; background-color: #007bff; color: white; border: none; border-radius: 5px; padding: 0 20px; } QPushButton:hover { background-color: #0056b3; } QPushButton:pressed { background-color: #004085; }")
        self.arrange_grid_button.clicked.connect(self.arrange_grid_requested.emit)
        action_buttons_layout.addWidget(self.arrange_grid_button)

        self.arrange_cascade_button = QPushButton("级联排列")
        self.arrange_cascade_button.setMinimumHeight(35)
        self.arrange_cascade_button.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; background-color: #17a2b8; color: white; border: none; border-radius: 5px; padding: 0 20px; } QPushButton:hover { background-color: #138496; } QPushButton:pressed { background-color: #117a8b; }")
        self.arrange_cascade_button.clicked.connect(self.arrange_cascade_requested.emit)
        action_buttons_layout.addWidget(self.arrange_cascade_button)
        main_layout.addLayout(action_buttons_layout)
        
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("color: #666; font-style: italic; margin-top: 5px;")
        self.status_label.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.status_label)

        main_layout.addStretch(1)
        
    def set_monitoring_status(self, is_monitoring: bool):
        """更新监控按钮的视觉状态。"""
        # Block signals to prevent emitting toggled signal when we set state programmatically
        self.monitor_toggle_button.blockSignals(True)
        self.monitor_toggle_button.setChecked(is_monitoring)
        self.monitor_toggle_button.blockSignals(False)

        if is_monitoring:
            self.monitor_toggle_button.setText("停止自动监控")
            self.monitor_toggle_button.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold;")
        else:
            self.monitor_toggle_button.setText("启动自动监控")
            self.monitor_toggle_button.setStyleSheet("") # 恢复默认样式
    
    def update_detected_windows_list(self, window_infos: list[object]):
        """更新UI上的检测到的窗口列表，并为每个项目添加复选框。"""
        self.detected_windows_list_widget.clear()
        if not window_infos:
            self.detected_windows_list_widget.addItem("未检测到符合条件的窗口。")
        else:
            for win_info in window_infos:
                display_text = f"{win_info.title} (进程: {win_info.process_name if win_info.process_name not in ['[未知进程]', '[PID获取失败]', '[进程不存在]', '[权限不足]', '[获取进程名失败]'] else 'N/A'})"
                item = QListWidgetItem(display_text)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                item.setData(Qt.UserRole, win_info)
                self.detected_windows_list_widget.addItem(item)
    
    def get_selected_window_infos(self) -> list[object]:
        """获取当前列表中所有被勾选的窗口的 WindowInfo 对象。"""
        selected_windows = []
        for i in range(self.detected_windows_list_widget.count()):
            item = self.detected_windows_list_widget.item(i)
            if item.checkState() == Qt.Checked:
                window_info = item.data(Qt.UserRole)
                if window_info:
                    selected_windows.append(window_info)
        return selected_windows

    def get_filter_keyword(self) -> str:
        """获取当前设置的窗口标题过滤关键词。"""
        return self.filter_keyword_input.text().strip()

    def get_process_name_filter(self) -> str:
        """获取当前设置的进程名过滤关键词。"""
        return self.process_name_input.text().strip()
    
    def get_exclude_keywords(self) -> str:
        """获取排除关键词字符串。"""
        return self.exclude_title_input.text().strip()
```
### settings_dialog_view
```python
# desktop_center/src/features/window_arranger/views/settings_dialog_view.py
import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                                   QGroupBox, QFormLayout, QSpinBox, QLabel,
                                   QComboBox, QDialogButtonBox, QLineEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QScreen

from src.core.context import ApplicationContext
from src.features.window_arranger.controllers.sorting_strategy_manager import SortingStrategyManager

class SettingsDialog(QDialog):
    """
    一个独立的对话框，用于管理窗口排列的所有设置。
    """
    def __init__(self, context: ApplicationContext, strategy_manager: SortingStrategyManager, parent=None):
        super().__init__(parent)
        self.context = context
        self.strategy_manager = strategy_manager
        self.setWindowTitle("排列设置")
        self.setMinimumWidth(600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)

        # --- 左列：网格与监控设置 ---
        grid_group = QGroupBox("网格与监控设置")
        grid_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        grid_form_layout = QFormLayout(grid_group)
        grid_form_layout.setSpacing(12)
        
        self.sorting_strategy_combobox = QComboBox()
        self.sorting_strategy_combobox.setMaximumWidth(200)
        grid_form_layout.addRow("排序方案:", self.sorting_strategy_combobox)

        # 【新增】监控模式选择
        self.monitor_mode_combobox = QComboBox()
        self.monitor_mode_combobox.addItems(["模板化自动排列", "快照式位置锁定"])
        self.monitor_mode_combobox.setToolTip(
            "模板化：严格按规则排列，自动处理增减窗口。\n"
            "快照式：仅恢复窗口到上次手动排列的位置，忽略新增窗口。"
        )
        self.monitor_mode_combobox.setMaximumWidth(200)
        grid_form_layout.addRow("监控模式:", self.monitor_mode_combobox)

        self.monitor_interval_spinbox = QSpinBox()
        self.monitor_interval_spinbox.setRange(1, 300)
        self.monitor_interval_spinbox.setSuffix(" 秒")
        self.monitor_interval_spinbox.setMaximumWidth(200)
        grid_form_layout.addRow("自动监测间隔:", self.monitor_interval_spinbox)
        
        grid_form_layout.addRow(QLabel("---"))

        self.screen_selection_combobox = QComboBox()
        self.screen_selection_combobox.setMaximumWidth(200)
        grid_form_layout.addRow("目标屏幕:", self.screen_selection_combobox)

        self.grid_direction_combobox = QComboBox()
        self.grid_direction_combobox.addItems(["先排满行 (→)", "先排满列 (↓)"])
        self.grid_direction_combobox.setMaximumWidth(200)
        grid_form_layout.addRow("排列方向:", self.grid_direction_combobox)

        self.rows_spinbox = QSpinBox()
        self.rows_spinbox.setRange(1, 20)
        self.rows_spinbox.setMaximumWidth(200)
        grid_form_layout.addRow("行数:", self.rows_spinbox)

        self.cols_spinbox = QSpinBox()
        self.cols_spinbox.setRange(1, 20)
        self.cols_spinbox.setMaximumWidth(200)
        grid_form_layout.addRow("列数:", self.cols_spinbox)
        
        margin_layout = QHBoxLayout()
        self.margin_top_spinbox = QSpinBox(); self.margin_top_spinbox.setRange(-500, 500); self.margin_top_spinbox.setMaximumWidth(60)
        self.margin_bottom_spinbox = QSpinBox(); self.margin_bottom_spinbox.setRange(-500, 500); self.margin_bottom_spinbox.setMaximumWidth(60)
        self.margin_left_spinbox = QSpinBox(); self.margin_left_spinbox.setRange(-500, 500); self.margin_left_spinbox.setMaximumWidth(60)
        self.margin_right_spinbox = QSpinBox(); self.margin_right_spinbox.setRange(-500, 500); self.margin_right_spinbox.setMaximumWidth(60)
        margin_layout.addWidget(QLabel("上:")); margin_layout.addWidget(self.margin_top_spinbox)
        margin_layout.addWidget(QLabel("下:")); margin_layout.addWidget(self.margin_bottom_spinbox)
        margin_layout.addWidget(QLabel("左:")); margin_layout.addWidget(self.margin_left_spinbox)
        margin_layout.addWidget(QLabel("右:")); margin_layout.addWidget(self.margin_right_spinbox)
        margin_layout.addStretch()
        grid_form_layout.addRow("屏幕边距 (px):", margin_layout)

        spacing_layout = QHBoxLayout()
        self.spacing_horizontal_spinbox = QSpinBox(); self.spacing_horizontal_spinbox.setRange(-100, 100); self.spacing_horizontal_spinbox.setMaximumWidth(80)
        self.spacing_vertical_spinbox = QSpinBox(); self.spacing_vertical_spinbox.setRange(-100, 100); self.spacing_vertical_spinbox.setMaximumWidth(80)
        spacing_layout.addWidget(QLabel("水平:")); spacing_layout.addWidget(self.spacing_horizontal_spinbox)
        spacing_layout.addWidget(QLabel("垂直:")); spacing_layout.addWidget(self.spacing_vertical_spinbox)
        spacing_layout.addStretch()
        grid_form_layout.addRow("窗口间距 (px):", spacing_layout)

        self.animation_delay_spinbox = QSpinBox()
        self.animation_delay_spinbox.setRange(0, 500)
        self.animation_delay_spinbox.setSuffix(" ms")
        self.animation_delay_spinbox.setMaximumWidth(200)
        grid_form_layout.addRow("排列动画延时:", self.animation_delay_spinbox)
        
        columns_layout.addWidget(grid_group)

        # --- 右列：其他与推送设置 ---
        other_group = QGroupBox("其他与推送设置")
        other_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        
        other_v_layout = QVBoxLayout(other_group)
        other_form_layout = QFormLayout()
        other_form_layout.setSpacing(12)
        
        self.cascade_x_offset_spinbox = QSpinBox(); self.cascade_x_offset_spinbox.setRange(0, 100); self.cascade_x_offset_spinbox.setMaximumWidth(200)
        self.cascade_y_offset_spinbox = QSpinBox(); self.cascade_y_offset_spinbox.setRange(0, 100); self.cascade_y_offset_spinbox.setMaximumWidth(200)
        other_form_layout.addRow("级联X偏移 (px):", self.cascade_x_offset_spinbox)
        other_form_layout.addRow("级联Y偏移 (px):", self.cascade_y_offset_spinbox)
        
        other_form_layout.addRow(QLabel("---"))

        self.enable_notifications_combobox = QComboBox()
        self.enable_notifications_combobox.addItems(["启用", "禁用"])
        self.enable_notifications_combobox.setMaximumWidth(200)
        other_form_layout.addRow("桌面操作通知:", self.enable_notifications_combobox)

        self.enable_push_combobox = QComboBox()
        self.enable_push_combobox.addItems(["启用", "禁用"])
        self.enable_push_combobox.setMaximumWidth(200)
        other_form_layout.addRow("Webhook推送:", self.enable_push_combobox)

        self.push_host_input = QLineEdit()
        self.push_host_input.setMaximumWidth(200)
        other_form_layout.addRow("推送主机:", self.push_host_input)

        self.push_port_input = QSpinBox()
        self.push_port_input.setRange(1, 65535)
        self.push_port_input.setMaximumWidth(200)
        other_form_layout.addRow("推送端口:", self.push_port_input)

        self.push_path_input = QLineEdit()
        self.push_path_input.setMaximumWidth(200)
        other_form_layout.addRow("推送路径:", self.push_path_input)
        
        other_v_layout.addLayout(other_form_layout)
        other_v_layout.addStretch()
        columns_layout.addWidget(other_group, 1)

        main_layout.addLayout(columns_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._populate_sorting_strategies()
        self._populate_screen_selection()
        self.load_settings()

    def _populate_sorting_strategies(self):
        """填充排序策略下拉框。"""
        strategy_names = self.strategy_manager.get_strategy_names()
        self.sorting_strategy_combobox.addItems(strategy_names)

    def _populate_screen_selection(self):
        """填充屏幕选择下拉框。"""
        screens = self.context.app.screens()
        screen_names = []
        for i, screen in enumerate(screens):
            screen_name = f"屏幕 {i+1} ({screen.geometry().width()}x{screen.geometry().height()})"
            if screen == self.context.app.primaryScreen():
                screen_name += " (主屏幕)"
            screen_names.append(screen_name)
        
        self.screen_selection_combobox.clear()
        if not screen_names:
            self.screen_selection_combobox.addItem("未检测到屏幕")
            self.screen_selection_combobox.setEnabled(False)
        else:
            self.screen_selection_combobox.addItems(screen_names)
            self.screen_selection_combobox.setEnabled(True)

    def load_settings(self):
        """从 ConfigService 加载设置到UI。"""
        config = self.context.config_service
        default_host = config.get_value("WebhookDefaults", "default_host", "127.0.0.1")
        default_port = config.get_value("WebhookDefaults", "default_port", "5000")

        self.sorting_strategy_combobox.setCurrentText(config.get_value("WindowArranger", "sorting_strategy", "默认排序 (按标题)"))
        monitor_mode = config.get_value("WindowArranger", "monitor_mode", "template")
        self.monitor_mode_combobox.setCurrentIndex(0 if monitor_mode == "template" else 1)
        self.monitor_interval_spinbox.setValue(int(config.get_value("WindowArranger", "monitor_interval", "5")))
        self.screen_selection_combobox.setCurrentIndex(int(config.get_value("WindowArranger", "target_screen_index", "0")))
        self.enable_notifications_combobox.setCurrentIndex(0 if config.get_value("WindowArranger", "enable_notifications", "true") == 'true' else 1)
        self.grid_direction_combobox.setCurrentIndex(0 if config.get_value("WindowArranger", "grid_direction", "row-major") == "row-major" else 1)
        self.rows_spinbox.setValue(int(config.get_value("WindowArranger", "grid_rows", "2")))
        self.cols_spinbox.setValue(int(config.get_value("WindowArranger", "grid_cols", "3")))
        self.margin_top_spinbox.setValue(int(config.get_value("WindowArranger", "grid_margin_top", "0")))
        self.margin_bottom_spinbox.setValue(int(config.get_value("WindowArranger", "grid_margin_bottom", "0")))
        self.margin_left_spinbox.setValue(int(config.get_value("WindowArranger", "grid_margin_left", "0")))
        self.margin_right_spinbox.setValue(int(config.get_value("WindowArranger", "grid_margin_right", "0")))
        self.spacing_horizontal_spinbox.setValue(int(config.get_value("WindowArranger", "grid_spacing_h", "10")))
        self.spacing_vertical_spinbox.setValue(int(config.get_value("WindowArranger", "grid_spacing_v", "10")))
        self.animation_delay_spinbox.setValue(int(config.get_value("WindowArranger", "animation_delay", "50")))
        self.cascade_x_offset_spinbox.setValue(int(config.get_value("WindowArranger", "cascade_x_offset", "30")))
        self.cascade_y_offset_spinbox.setValue(int(config.get_value("WindowArranger", "cascade_y_offset", "30")))
        self.enable_push_combobox.setCurrentIndex(0 if config.get_value("WindowArranger", "enable_push", "false") == 'true' else 1)
        self.push_host_input.setText(config.get_value("WindowArranger", "push_host", ""))
        self.push_port_input.setValue(int(config.get_value("WindowArranger", "push_port") or default_port))
        self.push_path_input.setText(config.get_value("WindowArranger", "push_path", "/alert"))
        self.push_host_input.setPlaceholderText(f"默认: {default_host}")
        self.push_port_input.setSpecialValueText(f"默认: {default_port}")

        logging.info("[WindowArranger] 设置对话框已加载配置。")
        
    def save_settings(self):
        """将UI上的设置保存到 ConfigService。"""
        config = self.context.config_service
        config.set_option("WindowArranger", "sorting_strategy", self.sorting_strategy_combobox.currentText())
        monitor_mode = "template" if self.monitor_mode_combobox.currentIndex() == 0 else "snapshot"
        config.set_option("WindowArranger", "monitor_mode", monitor_mode)
        config.set_option("WindowArranger", "monitor_interval", str(self.monitor_interval_spinbox.value()))
        config.set_option("WindowArranger", "enable_notifications", "true" if self.enable_notifications_combobox.currentIndex() == 0 else "false")
        config.set_option("WindowArranger", "target_screen_index", str(self.screen_selection_combobox.currentIndex()))
        config.set_option("WindowArranger", "grid_direction", "row-major" if self.grid_direction_combobox.currentIndex() == 0 else "col-major")
        config.set_option("WindowArranger", "grid_rows", str(self.rows_spinbox.value()))
        config.set_option("WindowArranger", "grid_cols", str(self.cols_spinbox.value()))
        config.set_option("WindowArranger", "grid_margin_top", str(self.margin_top_spinbox.value()))
        config.set_option("WindowArranger", "grid_margin_bottom", str(self.margin_bottom_spinbox.value()))
        config.set_option("WindowArranger", "grid_margin_left", str(self.margin_left_spinbox.value()))
        config.set_option("WindowArranger", "grid_margin_right", str(self.margin_right_spinbox.value()))
        config.set_option("WindowArranger", "grid_spacing_h", str(self.spacing_horizontal_spinbox.value()))
        config.set_option("WindowArranger", "grid_spacing_v", str(self.spacing_vertical_spinbox.value()))
        config.set_option("WindowArranger", "animation_delay", str(self.animation_delay_spinbox.value()))
        config.set_option("WindowArranger", "cascade_x_offset", str(self.cascade_x_offset_spinbox.value()))
        config.set_option("WindowArranger", "cascade_y_offset", str(self.cascade_y_offset_spinbox.value()))
        config.set_option("WindowArranger", "enable_push", "true" if self.enable_push_combobox.currentIndex() == 0 else "false")
        config.set_option("WindowArranger", "push_host", self.push_host_input.text())
        config.set_option("WindowArranger", "push_port", str(self.push_port_input.value()))
        config.set_option("WindowArranger", "push_path", self.push_path_input.text())
        config.save_config()
        logging.info("[WindowArranger] 排列设置已保存。")

    def save_and_accept(self):
        """保存设置并关闭对话框。"""
        self.save_settings()
        self.accept()
```

## 目前需要做的
分析下window_arranger这个插件的代码是否有错误，如果没有错误，就看看有没有需要优化重构的。
