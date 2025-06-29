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
from src.ui.settings_page import SettingsPageWidget # 设置页面作为核心UI

# --- 全局应用程序常量 ---
APP_NAME = "Desktop Control & Monitoring Center"
APP_VERSION = "5.0.0-MVC-Plugin-Architecture" # 版本号更新
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
    logging.info("="*50)
    logging.info("日志系统初始化完成。")

class ApplicationOrchestrator:
    """【平台核心】应用协调器，负责组装平台和加载插件。"""
    def __init__(self):
        logging.info(f"正在启动 {APP_NAME} v{APP_VERSION} 平台核心...")

        # 1. 初始化Qt应用
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # 2. 初始化【平台级】核心服务
        self.config_service = ConfigService(CONFIG_FILE)
        try:
            self.db_service = DatabaseService(DB_FILE)
            self.db_service.init_db()
        except Exception as e:
            logging.critical(f"数据库服务初始化失败，程序无法启动: {e}", exc_info=True)
            sys.exit(1)

        # 3. 初始化【平台级】核心UI
        self.window = MainWindow()
        self.window.setWindowTitle(self.config_service.get_value("General", "app_name", APP_NAME))
        self.tray_manager = TrayManager(self.app, self.window, ICON_FILE)
        self.action_manager = ActionManager(self.app)

        # 4. 创建应用上下文，供所有插件共享
        self.context = ApplicationContext(
            app=self.app,
            main_window=self.window,
            config_service=self.config_service,
            db_service=self.db_service,
            tray_manager=self.tray_manager,
            action_manager=self.action_manager
        )

        # 5. 初始化并运行插件管理器
        self.plugin_manager = PluginManager(self.context)
        self.plugin_manager.load_plugins()
        self.plugin_manager.initialize_plugins()
        
        # 6. 添加平台级页面（如设置）
        self._add_core_pages()

        # 7. 连接退出信号
        self.app.aboutToQuit.connect(self.shutdown)
        logging.info("平台核心和所有插件初始化完毕。")

    def _add_core_pages(self):
        """添加不属于任何插件的核心页面。"""
        self.settings_page = SettingsPageWidget(self.config_service)
        self.window.add_page("设置", self.settings_page)
        logging.info("核心页面(设置)添加完成。")

    def run(self):
        """启动应用程序的事件循环。"""
        logging.info("显示主窗口并启动Qt事件循环...")
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
        logging.info("正在关闭应用程序...")
        self.plugin_manager.shutdown_plugins()
        self.db_service.close()
        logging.info("所有服务已关闭。")


if __name__ == '__main__':
    setup_logging()
    main_app = ApplicationOrchestrator()
    main_app.run()