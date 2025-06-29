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
        【修改】在后台线程中启动托盘图标的事件监听，并增加异常处理。
        """
        try:
            self.tray_icon.run_detached()
            logging.info("系统托盘图标已在独立线程中运行。")
        except Exception as e:
            # 捕获 pystray 启动时可能发生的任何错误 (例如在无头服务器上)
            logging.critical(f"启动系统托盘图标失败: {e}", exc_info=True)
            self.quit_requested.emit()


    def show_window(self) -> None:
        """从托盘菜单显示并激活主窗口。"""
        logging.info("通过托盘菜单请求显示主窗口。")
        self.window.show()
        self.window.activateWindow()

    def quit_app(self) -> None:
        """
        安全地请求退出整个应用程序。
        """
        logging.info("通过托盘菜单请求退出应用程序...")
        
        self.tray_icon.stop()
        logging.info("pystray图标已停止。")
        
        logging.info("正在发射信号以触发应用程序的优雅关闭流程...")
        self.quit_requested.emit()