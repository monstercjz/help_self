# desktop_center/app.py
import sys
import os
import logging
import configparser
import shutil
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
import ctypes  # 【新增】导入 ctypes 用于Windows AppUserModelID
if sys.platform == "win32":
    try:
        import pythoncom
        from win32com.shell import shell, shellcon
    except ImportError:
        logging.warning("pywin32 is not installed, cannot create Start Menu shortcut.")
        pythoncom = None
import logging.handlers

# --- 1. 导入项目核心模块 ---
# 遵循先导入服务、再导入UI、最后导入管理器的逻辑顺序
from src.services.config_service import ConfigService
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
APP_NAME_DEFAULT = "HelpSelf"
CONFIG_FILE = 'config.ini'
DB_FILE = 'history.db'
LOG_FILE = 'app.log'
PNG_ICON_FILE = 'icon.png'  # 用于窗口、托盘等
ICO_ICON_FILE = 'icon.ico'  # 专门用于Windows原生通知

# 【新增】定义一个唯一的应用程序用户模型ID
APP_USER_MODEL_ID = "Cj.Helpself.MonitoringCenter"


def get_app_data_dir():
    """获取并确保应用数据根目录存在。"""
    app_data_dir = os.path.join(os.path.expanduser('~'), APP_NAME_DEFAULT)
    os.makedirs(app_data_dir, exist_ok=True)
    return app_data_dir

def get_resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境和PyInstaller打包环境。"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller环境
        base_path = sys._MEIPASS
    else:
        # 开发环境
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def prepare_config_file():
    """
    准备配置文件。如果用户数据目录中不存在，则从包内复制一份。
    返回可用的配置文件路径。
    """
    app_data_dir = get_app_data_dir()
    config_path_in_data_dir = os.path.join(app_data_dir, CONFIG_FILE)

    if not os.path.exists(config_path_in_data_dir):
        logging.info(f"配置文件在 '{config_path_in_data_dir}' 未找到，将从程序包中复制默认配置。")
        default_config_path = get_resource_path(CONFIG_FILE)
        if os.path.exists(default_config_path):
            try:
                shutil.copy(default_config_path, config_path_in_data_dir)
                logging.info(f"默认配置文件已成功复制到: {config_path_in_data_dir}")
            except Exception as e:
                logging.error(f"复制默认配置文件失败: {e}", exc_info=True)
                return None # 复制失败，无法继续
        else:
            logging.warning(f"在程序包内也未找到默认配置文件: {default_config_path}")
            return None # 找不到源文件，无法继续
            
    return config_path_in_data_dir

def setup_logging():
    """
    配置全局日志记录器。
    此函数设计为在应用生命周期中最早被调用，它会预读配置文件以获取日志级别。
    """
    log_level_str = "INFO"
    
    config_path = prepare_config_file()
    if config_path:
        try:
            pre_parser = configparser.ConfigParser()
            if pre_parser.read(config_path, encoding='utf-8-sig'):
                log_level_str = pre_parser.get('Logging', 'level', fallback='INFO').upper()
        except (configparser.Error, IOError):
            import warnings
            warnings.warn(f"无法预读配置文件 '{config_path}' 以获取日志级别，将使用默认的 'INFO' 级别。")

    log_level = getattr(logging, log_level_str, logging.INFO)

    # 将日志文件输出到用户主目录下的特定子目录
    log_dir = os.path.join(get_app_data_dir(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
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
        self.app_data_dir = get_app_data_dir()
        self.config_path = prepare_config_file()
        if not self.config_path:
            QMessageBox.critical(None, "致命错误", "无法创建或找到配置文件，应用程序无法启动。")
            sys.exit(1)
            
        self.db_path = os.path.join(self.app_data_dir, DB_FILE) # 稍后会被配置文件中的值覆盖
        self.png_icon_path = get_resource_path(PNG_ICON_FILE)
        self.ico_icon_path = get_resource_path(ICO_ICON_FILE)
        logging.info(f"  - 应用数据目录: {self.app_data_dir}")
        logging.info(f"  - 配置文件路径: {self.config_path}")

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
        # 【修复】在config_service初始化后调用快捷方式创建，因为快捷方式需要读取app_name
        if sys.platform == "win32":
            self._create_shortcut()
        # 通知服务依赖于配置服务，因此在其后初始化
        app_name = self.config_service.get_value("General", "app_name", APP_NAME_DEFAULT)
        self.notification_service = NotificationService(
            app_name=app_name,
            app_icon=self.ico_icon_path,
            config_service=self.config_service,
            app_id=APP_USER_MODEL_ID
        )
        # 【新增】实例化 WebhookService 具体配置参数应该在插件平台设置
        self.webhook_service = WebhookService()
        logging.info("  - 核心后台服务 (Config, Notification, Webhook) 初始化完成。")

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
            tray_manager=self.tray_manager,
            action_manager=self.action_manager,
            notification_service=self.notification_service,
            webhook_service=self.webhook_service,
            app_data_dir=self.app_data_dir
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

        logging.info("[STEP 6.4] 应用程序关闭流程结束。")

    def _create_shortcut(self):
        """
        为应用在开始菜单创建或更新快捷方式，并绑定AUMID。
        这是让非打包应用正确显示在Windows通知中心设置的关键。
        """
        if not (sys.platform == "win32" and pythoncom):
            return

        try:
            from win32com.propsys import propsys, pscon

            app_name = self.config_service.get_value("General", "app_name", APP_NAME_DEFAULT)
            programs_path = shell.SHGetFolderPath(0, shellcon.CSIDL_PROGRAMS, None, 0)
            shortcut_path = os.path.join(programs_path, f"{app_name}.lnk")

            if os.path.exists(shortcut_path):
                logging.info(f"Existing Start Menu shortcut found at: {shortcut_path}. Attempting to remove it.")
                try:
                    os.remove(shortcut_path)
                    logging.info("Existing shortcut removed successfully.")
                except Exception as e:
                    logging.warning(f"Failed to remove existing shortcut: {e}")
                    # 如果无法删除现有快捷方式，我们仍然尝试创建新的，可能会覆盖或失败

            target = sys.executable
            script_path = os.path.abspath(__file__)
            work_dir = os.path.dirname(script_path)
            icon = self.ico_icon_path

            shortcut = pythoncom.CoCreateInstance(
                shell.CLSID_ShellLink, None,
                pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
            )
            shortcut.SetPath(target)
            shortcut.SetArguments(f'"{script_path}"')
            shortcut.SetWorkingDirectory(work_dir)
            shortcut.SetIconLocation(icon, 0)

            prop_store = shortcut.QueryInterface(propsys.IID_IPropertyStore)
            PKEY_AppUserModel_ID = pscon.PKEY_AppUserModel_ID
            prop_store.SetValue(PKEY_AppUserModel_ID, propsys.PROPVARIANTType(APP_USER_MODEL_ID))
            prop_store.Commit()

            persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
            persist_file.Save(shortcut_path, 0)
            logging.info(f"Successfully created Start Menu shortcut with AUMID at {shortcut_path}")

        except Exception as e:
            logging.error(f"Failed to create Start Menu shortcut: {e}", exc_info=True)


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