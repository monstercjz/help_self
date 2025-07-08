# desktop_center/app.py
import sys
import os
import logging
import configparser
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon 
import ctypes # 【新增】导入 ctypes 用于Windows AppUserModelID
import logging.handlers

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
    # 【修改】将日志文件输出到用户主目录下的特定子目录
    log_dir = os.path.join(os.path.expanduser('~'), APP_NAME_DEFAULT, 'logs')
    os.makedirs(log_dir, exist_ok=True) # 确保日志目录存在
    log_file_path = os.path.join(log_dir, LOG_FILE)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8',
        mode='a'
    )
    stream_handler = logging.StreamHandler(sys.stdout)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
        handlers=[
            file_handler,    # 使用配置好的轮转文件处理器
            stream_handler
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
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # 如果是PyInstaller打包的单文件模式，使用_MEIPASS作为基础路径
            project_root = sys._MEIPASS
            logging.info(f"  - 检测到PyInstaller环境，使用_MEIPASS: {project_root}")
        else:
            # 否则，使用当前文件所在目录作为基础路径
            project_root = os.path.dirname(os.path.abspath(__file__))
            logging.info(f"  - 非PyInstaller环境，使用当前文件路径: {project_root}")

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