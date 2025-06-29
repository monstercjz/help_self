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
APP_VERSION = "5.2.0-Verbose-Logging" # 版本号更新
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