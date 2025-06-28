# src/ui/main_window.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QListWidget, QListWidgetItem, 
                               QHBoxLayout, QStackedWidget)
from PySide6.QtGui import QIcon

# 导入各个功能页面
from .alerts_page import AlertsPageWidget
from .settings_page import SettingsPageWidget
from .quick_launch_page import QuickLaunchPageWidget

class MainWindow(QMainWindow):
    """主应用程序窗口，采用可扩展的导航布局"""
    def __init__(self, config_service):
        super().__init__()
        self.setWindowTitle("桌面控制与监控中心")
        self.setGeometry(100, 100, 800, 600)
        
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(150)
        main_layout.addWidget(self.nav_list)
        
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # 创建并添加功能页面
        self.alerts_page = AlertsPageWidget()
        self.quick_launch_page = QuickLaunchPageWidget()
        self.settings_page = SettingsPageWidget(config_service)
        
        self.stacked_widget.addWidget(self.alerts_page)
        self.stacked_widget.addWidget(self.quick_launch_page)
        self.stacked_widget.addWidget(self.settings_page)
        
        self.nav_list.addItem(QListWidgetItem("告警中心"))
        self.nav_list.addItem(QListWidgetItem("快捷启动"))
        self.nav_list.addItem(QListWidgetItem("设置"))
        
        self.nav_list.currentItemChanged.connect(self.switch_page)
        self.nav_list.setCurrentRow(0)

    def switch_page(self, current_item, previous_item):
        if current_item:
            self.stacked_widget.setCurrentIndex(self.nav_list.row(current_item))

    def closeEvent(self, event):
        event.ignore()
        self.hide()