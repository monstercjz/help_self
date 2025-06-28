# desktop_center/app.py
import sys
import logging
from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow
from src.services.config_service import ConfigService
from src.utils.tray_manager import TrayManager
from src.services.database_service import DatabaseService
from src.ui.alerts_page import AlertsPageWidget
from src.ui.settings_page import SettingsPageWidget
from src.services.alert_receiver import AlertReceiverThread
# 不再需要导入占位页面
# from src.ui.history_page import HistoryPageWidget 

APP_NAME = "Desktop Control & Monitoring Center"
APP_VERSION = "2.3.0-final-ui-polish"
CONFIG_FILE = 'config.ini'
ICON_FILE = 'icon.png'
LOG_FILE = 'app.log'
DB_FILE = 'history.db'

def setup_logging():
    # ... (保持不变) ...
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
    def __init__(self):
        # ... (大部分 __init__ 保持不变) ...
        logging.info(f"正在启动 {APP_NAME} v{APP_VERSION}...")
        
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.config_service = ConfigService(CONFIG_FILE)
        try:
            self.db_service = DatabaseService(DB_FILE)
            self.db_service.init_db()
        except Exception as e:
            logging.critical(f"数据库服务初始化失败，程序无法启动: {e}", exc_info=True)
            sys.exit(1)

        self.window = MainWindow()
        self.window.setWindowTitle(self.config_service.get_value("General", "app_name", APP_NAME))
        self._add_pages_to_main_window()
        self.alert_receiver_thread = self._setup_background_services()
        try:
            self.tray_manager = TrayManager(self.app, self.window, ICON_FILE)
        except FileNotFoundError:
            logging.error(f"关键资源文件 '{ICON_FILE}' 未找到。程序即将退出。")
            sys.exit(1)
            
        self.app.aboutToQuit.connect(self.db_service.close)
        logging.info("所有组件初始化和集成完毕。")

    # 【核心修改】移除 history_page 的创建和添加
    def _add_pages_to_main_window(self):
        """将所有功能页面添加到主窗口。"""
        logging.info("正在创建并添加功能页面...")
        self.alerts_page = AlertsPageWidget(self.config_service, self.db_service)
        self.settings_page = SettingsPageWidget(self.config_service)
        
        self.window.add_page("信息接收中心", self.alerts_page)
        self.window.add_page("设置", self.settings_page)
        logging.info("功能页面添加完成。")
        
    def _setup_background_services(self) -> AlertReceiverThread:
        # ... (保持不变) ...
        logging.info("正在配置和启动后台服务...")
        host = self.config_service.get_value("InfoService", "host", "0.0.0.0")
        port = int(self.config_service.get_value("InfoService", "port", 5000))
        
        receiver_thread = AlertReceiverThread(
            config_service=self.config_service, 
            db_service=self.db_service,
            host=host, 
            port=port
        )
        
        receiver_thread.new_alert_received.connect(self.alerts_page.add_alert)
        logging.info("后台服务信号已连接到UI槽函数。")
        
        receiver_thread.start()
        return receiver_thread

    def run(self):
        # ... (保持不变) ...
        logging.info("显示主窗口并启动Qt事件循环...")
        try:
            self.tray_manager.run()
            if self.config_service.get_value("General", "start_minimized", "false").lower() != 'true':
                self.window.show()
            sys.exit(self.app.exec())
        except Exception as e:
            logging.critical(f"应用程序顶层发生未捕获的异常: {e}", exc_info=True)
            sys.exit(1)

if __name__ == '__main__':
    setup_logging()
    main_app = ApplicationOrchestrator()
    main_app.run()