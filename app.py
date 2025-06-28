# desktop_center/app.py
import sys
import logging
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

# 导入核心架构组件
from src.ui.main_window import MainWindow
from src.services.config_service import ConfigService
from src.utils.tray_manager import TrayManager

# --- 全局应用程序常量 ---
# 将配置信息集中在此处，便于管理
APP_NAME = "Desktop Control & Monitoring Center"
APP_VERSION = "1.0.0-skeleton"
CONFIG_FILE = 'config.ini'
ICON_FILE = 'icon.png'
LOG_FILE = 'app.log'

def setup_logging():
    """配置全局日志记录器"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)  # 同时输出到控制台
        ]
    )
    logging.info("日志系统初始化完成。")

class ApplicationOrchestrator:
    """
    应用协调器类 (The Conductor)。
    负责以正确的顺序创建和连接所有核心组件，并管理应用的生命周期。
    """
    def __init__(self):
        """初始化应用所需的所有核心对象。"""
        logging.info(f"正在启动 {APP_NAME} v{APP_VERSION}...")

        # 1. 初始化Qt应用程序实例
        # 这是所有UI组件存在的基础。
        self.app = QApplication(sys.argv)
        # 设置当最后一个窗口关闭时，应用程序不退出，以便在托盘中继续运行。
        self.app.setQuitOnLastWindowClosed(False)

        # 2. 初始化核心服务 (非UI部分)
        # ConfigService是基础，很多其他组件可能依赖它。
        self.config_service = ConfigService(CONFIG_FILE)

        # 3. 初始化主UI框架 (窗口的骨架)
        self.window = MainWindow()

        # 4. 初始化系统托盘管理器 (生命周期控制)
        # TrayManager需要app和window的实例来控制它们。这是一种“依赖注入”。
        try:
            self.tray_manager = TrayManager(self.app, self.window, ICON_FILE)
        except FileNotFoundError:
            logging.error(f"关键资源文件 '{ICON_FILE}' 未找到。托盘图标无法加载，程序即将退出。")
            sys.exit(1) # 严重错误，直接退出

        # 5. 动态地向主窗口添加页面 (展示架构的可扩展性)
        # 这里是未来添加新功能页面的地方。
        self._add_pages_to_main_window()
        
        logging.info("所有核心组件初始化完毕，应用准备就绪。")

    def _add_pages_to_main_window(self):
        """
        将所有功能页面添加到主窗口的堆栈窗口中。
        这个方法清晰地展示了如何扩展新页面。
        """
        # 创建一个简单的欢迎页面作为示例
        welcome_page = QWidget()
        layout = QVBoxLayout(welcome_page)
        label = QLabel(f"欢迎使用 {APP_NAME}\n\n这是一个基础架构，请在此基础上添加功能页面。")
        label.setStyleSheet("font-size: 16px; color: #333;")
        layout.addWidget(label)
        
        # 将页面添加到主窗口
        self.window.add_page("欢迎", welcome_page)
        # 未来添加其他页面：
        # from src.ui.alerts_page import AlertsPageWidget
        # self.alerts_page = AlertsPageWidget()
        # self.window.add_page("告警中心", self.alerts_page)

    def run(self):
        """启动应用程序的事件循环和所有后台服务。"""
        try:
            # 启动系统托盘图标（它将在后台线程中运行）
            self.tray_manager.run()
            
            # 显示主窗口
            # 默认启动时显示，也可以根据配置决定是否仅启动到托盘
            self.window.show()

            # 启动Qt的事件循环。程序将在此处阻塞，直到退出。
            # sys.exit()确保退出码能被正确传递。
            sys.exit(self.app.exec())
        except Exception as e:
            logging.critical(f"应用程序顶层发生未捕获的异常: {e}", exc_info=True)
            sys.exit(1)

if __name__ == '__main__':
    # 1. 首先设置日志
    setup_logging()
    
    # 2. 创建并运行应用
    main_app = ApplicationOrchestrator()
    main_app.run()