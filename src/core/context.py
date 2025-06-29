# src/core/context.py
from dataclasses import dataclass
from PySide6.QtWidgets import QApplication
from src.services.config_service import ConfigService
from src.services.database_service import DatabaseService
from src.ui.main_window import MainWindow
from src.utils.tray_manager import TrayManager
from src.ui.action_manager import ActionManager

@dataclass
class ApplicationContext:
    """一个数据类，持有所有核心/共享服务和组件的引用，供插件使用。"""
    app: QApplication
    main_window: MainWindow
    config_service: ConfigService
    db_service: DatabaseService
    tray_manager: TrayManager
    action_manager: ActionManager