# desktop_center/src/ui/main_window.py
import logging  # 【新增】添加对logging模块的导入
from PySide6.QtWidgets import (QMainWindow, QWidget, QListWidget, QListWidgetItem, 
                               QHBoxLayout, QStackedWidget)
from PySide6.QtCore import QEvent, QSize

class MainWindow(QMainWindow):
    """
    主应用程序窗口框架。
    采用“导航-内容”布局，设计为可扩展的容器。
    它自身不实现任何具体功能页面，只提供添加和切换页面的能力。
    """
    def __init__(self, parent: QWidget = None):
        """
        初始化主窗口。

        Args:
            parent (QWidget, optional): 父组件。默认为 None。
        """
        super().__init__(parent)
        self.setWindowTitle("Application Skeleton") # 初始标题，可由app.py覆盖
        self.setGeometry(100, 100, 900, 700) # 初始尺寸

        # --- 创建主布局 ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # 无边距，让子组件填满
        main_layout.setSpacing(0)

        # --- 左侧导航栏 ---
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(180)
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #f0f0f0;
                border: none;
                font-size: 14px;
                padding-top: 10px;
            }
            QListWidget::item {
                padding: 12px 20px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
                font-weight: bold;
                border-left: 5px solid #005a9e;
            }
        """)
        main_layout.addWidget(self.nav_list)
        
        # --- 右侧内容区 (使用QStackedWidget实现页面切换) ---
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # --- 连接信号与槽 ---
        # 当导航栏的当前项改变时，切换到对应的页面
        self.nav_list.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)
    
    def add_page(self, title: str, widget: QWidget) -> None:
        """
        向主窗口动态添加一个功能页面。

        Args:
            title (str): 显示在导航栏中的页面标题。
            widget (QWidget): 要添加的功能页面的实例。
        """
        # 将页面实例添加到堆栈窗口中
        self.stacked_widget.addWidget(widget)
        # 将页面标题添加到导航列表
        self.nav_list.addItem(QListWidgetItem(title))
        
        # 默认选中第一个添加的页面
        if self.nav_list.count() == 1:
            self.nav_list.setCurrentRow(0)

    def closeEvent(self, event: QEvent) -> None:
        """
        重写窗口关闭事件。
        默认行为是隐藏窗口而不是退出应用，以便在系统托盘中继续运行。
        
        Args:
            event (QEvent): 关闭事件对象。
        """
        logging.info("关闭事件触发：隐藏主窗口到系统托盘。")
        event.ignore()  # 忽略默认的关闭行为（即退出）
        self.hide()     # 将窗口隐藏