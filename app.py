# app.py
import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.services.alert_receiver import AlertReceiverThread
from src.services.config_service import ConfigService
from src.utils.tray_manager import TrayManager

# --- 全局常量 ---
CONFIG_FILE = 'config.ini'
ICON_FILE = 'icon.png'

class MainApplication:
    """组装并运行所有模块的主应用程序"""
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # 1. 初始化服务
        self.config_service = ConfigService(CONFIG_FILE)
        
        # 2. 初始化UI
        self.window = MainWindow(self.config_service)
        
        # 3. 初始化并启动后台线程
        self.receiver_thread = AlertReceiverThread()
        # 建立后台线程与UI的通信
        self.receiver_thread.new_alert.connect(self.window.alerts_page.add_alert_to_table)
        self.receiver_thread.start()

        # 4. 初始化系统托盘
        self.tray_manager = TrayManager(self.app, self.window, ICON_FILE)

    def run(self):
        """启动应用程序"""
        self.tray_manager.run()
        self.window.show()
        sys.exit(self.app.exec())

if __name__ == '__main__':
    main_app = MainApplication()
    main_app.run()