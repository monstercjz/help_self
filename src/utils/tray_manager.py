# src/utils/tray_manager.py
import logging
from PySide6.QtGui import QIcon
from pystray import MenuItem, Icon
from PIL import Image

class TrayManager:
    """负责管理系统托盘图标及其菜单"""
    def __init__(self, app, window, icon_path):
        self.app = app
        self.window = window
        self.icon_path = icon_path
        
        # 将主窗口的图标也设置一下
        self.window.setWindowIcon(QIcon(icon_path))
        
        image = Image.open(self.icon_path)
        menu = (MenuItem('显示监控中心', self.show_window, default=True),
                MenuItem('退出', self.quit_app))
        self.tray_icon = Icon("DesktopCenter", image, "桌面控制与监控中心", menu)

    def run(self):
        self.tray_icon.run_detached()

    def show_window(self):
        self.window.show()
        self.window.activateWindow()

    def quit_app(self):
        logging.info("正在通过托盘菜单退出应用程序...")
        # 停止托盘图标自身
        self.tray_icon.stop()
        # 调用QApplication的quit，这将安全地结束事件循环
        self.app.quit()