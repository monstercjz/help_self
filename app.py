# desktop_center/app.py
import sys
import logging
from PySide6.QtWidgets import QApplication

# 导入核心架构组件
from src.ui.main_window import MainWindow
from src.services.config_service import ConfigService
from src.utils.tray_manager import TrayManager

# --- 导入新增的功能模块 ---
from src.ui.alerts_page import AlertsPageWidget
from src.ui.settings_page import SettingsPageWidget
from src.services.alert_receiver import AlertReceiverThread

# --- 全局应用程序常量 ---
# 这些常量定义了应用的基本属性和资源文件路径
APP_NAME = "Desktop Control & Monitoring Center"
APP_VERSION = "1.2.0-integrated"
CONFIG_FILE = 'config.ini'
ICON_FILE = 'icon.png'
LOG_FILE = 'app.log'

def setup_logging():
    """
    配置全局日志记录器。
    将日志同时输出到文件和控制台，便于调试和追溯问题。
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
        handlers=[
            # 日志文件处理器，记录所有级别的日志
            logging.FileHandler(LOG_FILE, encoding='utf-8', mode='a'),
            # 控制台处理器，方便开发时实时查看
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("="*50)
    logging.info("日志系统初始化完成。")

class ApplicationOrchestrator:
    """
    应用协调器 (The Conductor)。
    此类是应用程序的最高指挥官，负责以正确的顺序创建、连接和启动所有模块，
    并管理应用的整个生命周期。
    """
    def __init__(self):
        """
        初始化应用所需的所有核心对象。
        此构造函数遵循一个清晰的初始化顺序：
        核心服务 -> UI框架 -> 功能页面 -> 后台服务 -> 生命周期管理器。
        """
        logging.info(f"正在启动 {APP_NAME} v{APP_VERSION}...")
        
        # 1. 初始化Qt应用程序实例，这是所有UI的基础
        self.app = QApplication(sys.argv)
        # 设置当最后一个窗口关闭时，应用程序不退出，以便在托盘中继续运行
        self.app.setQuitOnLastWindowClosed(False)

        # 2. 初始化核心服务
        # ConfigService是基础，很多其他组件可能依赖它
        self.config_service = ConfigService(CONFIG_FILE)

        # 3. 初始化主UI框架
        self.window = MainWindow()
        # 从配置中读取应用名称并设置窗口标题，提供动态性
        self.window.setWindowTitle(self.config_service.get_value("General", "app_name", APP_NAME))

        # 4. 初始化并集成所有功能页面
        self._add_pages_to_main_window()
        
        # 5. 初始化并启动后台服务线程
        self.alert_receiver_thread = self._setup_background_services()

        # 6. 初始化系统托盘管理器，它负责控制应用的显示/隐藏和退出
        try:
            self.tray_manager = TrayManager(self.app, self.window, ICON_FILE)
        except FileNotFoundError:
            logging.error(f"关键资源文件 '{ICON_FILE}' 未找到。托盘图标无法加载，程序即将退出。")
            sys.exit(1) # 这是一个致命错误，无法继续运行
            
        logging.info("所有组件初始化和集成完毕，应用准备就绪。")

    def _add_pages_to_main_window(self):
        """将所有功能页面添加到主窗口的堆栈窗口中。"""
        logging.info("正在创建并添加功能页面...")
        # 创建页面实例，注意SettingsPage需要注入ConfigService依赖
        self.alerts_page = AlertsPageWidget()
        self.settings_page = SettingsPageWidget(self.config_service)
        
        # 按希望的顺序将页面添加到主窗口
        self.window.add_page("信息接收中心", self.alerts_page)
        self.window.add_page("设置", self.settings_page)
        logging.info("功能页面添加完成。")
        
    def _setup_background_services(self) -> AlertReceiverThread:
        """配置并启动所有后台服务线程，并建立与UI的通信。"""
        logging.info("正在配置和启动后台服务...")
        # 从配置中读取Web服务的参数，如果配置不存在则使用默认值
        host = self.config_service.get_value("WebServer", "host", "0.0.0.0")
        port = int(self.config_service.get_value("WebServer", "port", 5000))
        
        # 创建后台线程实例，并将config_service注入，以便线程内部可以读取配置
        receiver_thread = AlertReceiverThread(
            config_service=self.config_service, 
            host=host, 
            port=port
        )
        
        # 【核心步骤】将后台线程的信号连接到UI页面的槽函数。
        # 这是实现线程安全UI更新的关键，保证了后台逻辑和UI逻辑的解耦。
        receiver_thread.new_alert_received.connect(self.alerts_page.add_alert)
        logging.info("后台服务信号已连接到UI槽函数。")
        
        # 启动线程，使其开始在后台运行Flask服务
        receiver_thread.start()
        return receiver_thread

    def run(self):
        """启动应用程序的事件循环和所有后台服务。"""
        logging.info("显示主窗口并启动Qt事件循环...")
        try:
            # 启动系统托盘图标（它将在后台线程中运行）
            self.tray_manager.run()
            
            # 根据配置决定是否在启动时显示主窗口，或直接最小化到托盘
            if self.config_service.get_value("General", "start_minimized", "false").lower() != 'true':
                self.window.show()
                
            # 启动Qt的事件循环。程序将在此处阻塞，直到被self.app.quit()终止。
            # sys.exit()确保退出码能被正确传递给操作系统。
            sys.exit(self.app.exec())
        except Exception as e:
            logging.critical(f"应用程序顶层发生未捕获的异常: {e}", exc_info=True)
            sys.exit(1)

if __name__ == '__main__':
    # 应用程序的唯一入口
    
    # 1. 优先设置日志系统，以便后续所有操作都能被记录
    setup_logging()
    
    # 2. 创建应用协调器实例并运行
    main_app = ApplicationOrchestrator()
    main_app.run()