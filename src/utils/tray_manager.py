# desktop_center/src/utils/tray_manager.py
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QAction
from pystray import MenuItem, Icon
from PIL import Image

class TrayManager:
    """
    系统托盘管理器。
    负责创建托盘图标、管理其右键菜单，并处理应用的显示、隐藏和退出逻辑。
    这是一个独立的组件，控制着应用的生命周期。
    """
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
        self.app = app
        self.window = window

        # 设置主窗口的图标
        self.window.setWindowIcon(QIcon(icon_path))
        
        # pystray需要Pillow Image对象
        try:
            image = Image.open(icon_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Icon file not found at: {icon_path}")

        # 定义托盘菜单项
        menu = (
            MenuItem('显示主窗口', self.show_window, default=True),
            MenuItem('退出程序', self.quit_app)
        )
        
        # 创建pystray图标实例
        self.tray_icon = Icon("AppName", image, "Application Title", menu)
        logging.info("系统托盘管理器初始化完成。")

    def run(self) -> None:
        """在后台线程中启动托盘图标的事件监听。"""
        self.tray_icon.run_detached()
        logging.info("系统托盘图标已在独立线程中运行。")

    def show_window(self) -> None:
        """从托盘菜单显示并激活主窗口。"""
        logging.info("通过托盘菜单请求显示主窗口。")
        self.window.show()
        self.window.activateWindow() # 确保窗口在最前端

    def quit_app(self) -> None:
        """安全地退出整个应用程序。"""
        logging.info("通过托盘菜单请求退出应用程序。")
        # 1. 停止pystray图标的事件循环
        self.tray_icon.stop()
        # 2. 调用QApplication的quit，这将安全地结束Qt事件循环并释放资源
        self.app.quit()