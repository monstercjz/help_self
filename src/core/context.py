# desktop_center/src/core/context.py
from dataclasses import dataclass
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QApplication

# 【修改】使用类型检查块来避免循环导入
if TYPE_CHECKING:
    from src.services.config_service import ConfigService
    from src.services.database_service import DatabaseService
    from src.services.notification_service import NotificationService
    from src.ui.main_window import MainWindow
    from src.utils.tray_manager import TrayManager
    from src.ui.action_manager import ActionManager

@dataclass
class ApplicationContext:
    """一个数据类，持有所有核心/共享服务和组件的引用，供插件使用。"""
    app: QApplication
    main_window: 'MainWindow'
    config_service: 'ConfigService'
    db_service: 'DatabaseService'
    tray_manager: 'TrayManager'
    action_manager: 'ActionManager'
    notification_service: 'NotificationService'