# desktop_center/src/core/context.py
import os
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QApplication

# 【修改】使用类型检查块来避免循环导入
if TYPE_CHECKING:
    from src.services.config_service import ConfigService
    from src.services.notification_service import NotificationService
    from src.services.webhook_service import WebhookService
    from src.services.database_initializer import DatabaseInitializerService
    from src.services.database_switch_service import DatabaseSwitchService
    from src.utils.tray_manager import TrayManager
    from src.ui.action_manager import ActionManager
    from src.ui.main_window import MainWindow

class ApplicationContext:
    """一个数据类，持有所有核心/共享服务和组件的引用，供插件使用。"""
    def __init__(self, app: QApplication, main_window: 'MainWindow',
                 config_service: 'ConfigService',
                 tray_manager: 'TrayManager', action_manager: 'ActionManager',
                 notification_service: 'NotificationService', webhook_service: 'WebhookService',
                 db_initializer: 'DatabaseInitializerService',
                 database_switch_service: 'DatabaseSwitchService',
                 app_data_dir: str):
        self.app = app
        self.main_window = main_window
        self.config_service = config_service
        self.tray_manager = tray_manager
        self.action_manager = action_manager
        self.notification_service = notification_service
        self.webhook_service = webhook_service
        self.db_initializer = db_initializer
        self.database_switch_service = database_switch_service
        self.app_data_dir = app_data_dir

    def get_data_path(self, relative_path: str) -> str:
        """
        获取一个保证在应用数据目录下可写的绝对路径。
        会自动创建所有必要的父目录。

        Args:
            relative_path (str): 相对于应用数据根目录的文件或目录路径。

        Returns:
            str: 最终的绝对路径。
        """
        absolute_path = os.path.join(self.app_data_dir, relative_path)
        # 确保文件所在的目录存在
        dir_name = os.path.dirname(absolute_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        return absolute_path