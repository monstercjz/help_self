# desktop_center/app.py
import sys
import logging
from PySide6.QtWidgets import QApplication

# 导入核心架构组件
from src.ui.main_window import MainWindow
from src.services.config_service import ConfigService
from src.utils.tray_manager import TrayManager
from src.services.database_service import DatabaseService

# --- 导入功能模块 ---
from src.ui.alerts_page import AlertsPageWidget
from src.ui.settings_page import SettingsPageWidget
from src.services.alert_receiver import AlertReceiverThread
# 导入新的对话框类
from src.ui.history_dialog import HistoryDialog
from src.ui.statistics_dialog import StatisticsDialog

# --- 全局应用程序常量 ---
APP_NAME = "Desktop Control & Monitoring Center"
APP_VERSION = "3.0.1-critical-app-fix" # 版本号更新
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
    """应用协调器。"""
    def __init__(self):
        logging.info(f"正在启动 {APP_NAME} v{APP_VERSION}...")
        
        # 1. 初始化Qt应用程序实例
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # 2. 初始化核心服务
        self.config_service = ConfigService(CONFIG_FILE)
        try:
            self.db_service = DatabaseService(DB_FILE)
            self.db_service.init_db()
        except Exception as e:
            logging.critical(f"数据库服务初始化失败，程序无法启动: {e}", exc_info=True)
            sys.exit(1)

        # 3. 初始化主UI框架
        self.window = MainWindow()
        self.window.setWindowTitle(self.config_service.get_value("General", "app_name", APP_NAME))
        
        # 4. 初始化并添加功能页面
        self._add_pages_to_main_window()
        
        # 5. 初始化并启动后台服务线程
        self.alert_receiver_thread = self._setup_background_services()
        
        # 6. 初始化系统托盘管理器
        try:
            self.tray_manager = TrayManager(self.app, self.window, ICON_FILE)
        except FileNotFoundError:
            logging.error(f"关键资源文件 '{ICON_FILE}' 未找到。程序即将退出。")
            sys.exit(1)
            
        # 确保在应用退出时关闭数据库连接
        self.app.aboutToQuit.connect(self.db_service.close)
        logging.info("所有组件初始化和集成完毕。")

    def _add_pages_to_main_window(self):
        """将所有功能页面添加到主窗口。"""
        logging.info("正在创建并添加功能页面...")
        self.alerts_page = AlertsPageWidget(self.config_service, self.db_service)
        self.settings_page = SettingsPageWidget(self.config_service)
        
        self.window.add_page("信息接收中心", self.alerts_page)
        self.window.add_page("设置", self.settings_page)
        logging.info("功能页面添加完成。")
        
    def _setup_background_services(self) -> AlertReceiverThread:
        """配置并启动后台服务线程。"""
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

if __name__ == '__main__':
    setup_logging()
    main_app = ApplicationOrchestrator()
    main_app.run()