# desktop_center/src/features/alert_center/views/alerts_page_view.py
import logging
from PySide6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QVBoxLayout, QLabel, QPushButton,
                               QHBoxLayout, QMenu, QSizePolicy)
from PySide6.QtCore import Slot, Qt, QEvent, QSize, Signal
from PySide6.QtGui import QColor, QIcon, QAction
from datetime import datetime

# UI相关的常量应保留在View层
SEVERITY_COLORS = {
    "CRITICAL": QColor("#FFDDDD"),
    "WARNING": QColor("#FFFFCC"),
    "INFO": QColor("#FFFFFF")
}
LEVEL_DISPLAY_MAP = {
    "INFO": "ℹ️ 正常级别",
    "WARNING": "⚠️ 警告级别",
    "CRITICAL": "❗ 危及级别"
}

class FlatButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("QPushButton { border: none; background-color: transparent; text-align: left; padding: 4px 8px; color: #333; font-size: 13px; } QPushButton:hover { background-color: #e8e8e8; border-radius: 4px; } QPushButton::menu-indicator { image: none; }")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)

class FlatMenuButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("QPushButton { border: none; background-color: transparent; text-align: left; padding: 4px 8px; color: #333; font-size: 13px; } QPushButton:hover { background-color: #e8e8e8; border-radius: 4px; } QPushButton::menu-indicator { image: none; }")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.clicked.connect(self.showMenu)


class AlertsPageView(QWidget):
    """
    【视图】“告警中心”主页面。
    这是一个纯UI组件，不包含任何业务逻辑。
    它通过信号与控制器通信，并通过槽函数接收数据更新。
    """
    # --- Signals to Controller ---
    toggle_popup_status_requested = Signal()
    notification_level_changed = Signal(str)
    history_dialog_requested = Signal()
    statistics_dialog_requested = Signal()
    clear_database_requested = Signal()
    clear_display_requested = Signal()
    page_shown = Signal() # 页面显示时发出

    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 0, 15, 15)
        main_layout.setSpacing(10)

        toolbar_container = self._create_toolbar()
        main_layout.addWidget(toolbar_container)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["接收时间", "严重等级", "信息类型", "来源IP", "详细内容"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.table)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.clear_button = QPushButton("清空当前显示")
        self.clear_button.setFixedWidth(120)
        self.clear_button.clicked.connect(self.clear_display_requested.emit)
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)
        
        self.installEventFilter(self)

    def _create_toolbar(self):
        toolbar_container = QWidget()
        toolbar_container.setObjectName("ToolbarContainer")
        toolbar_container.setStyleSheet("#ToolbarContainer { background-color: #F8F8F8; border-top: 1px solid #E0E0E0; border-bottom: 1px solid #E0E0E0; }")
        toolbar_container.setContentsMargins(15, 10, 15, 10)
        toolbar_container.setFixedHeight(60)

        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("实时信息接收中心")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch()

        buttons_group_container = QWidget()
        buttons_group_container.setObjectName("ButtonsGroupContainer")
        buttons_group_container.setStyleSheet("#ButtonsGroupContainer { border: 1px solid #E0E0E0; border-radius: 8px; background-color: transparent; }")
        buttons_group_layout = QHBoxLayout(buttons_group_container)
        buttons_group_layout.setContentsMargins(2, 2, 2, 2)
        buttons_group_layout.setSpacing(0)

        self.popup_status_button = FlatButton("")
        self.popup_status_button.setToolTip("点击切换启用/禁用桌面弹窗")
        self.popup_status_button.clicked.connect(self.toggle_popup_status_requested.emit)
        self.popup_status_button.setFixedWidth(153)
        buttons_group_layout.addWidget(self.popup_status_button)

        self.level_status_button = FlatMenuButton()
        self.level_status_button.setToolTip("点击选择通知级别阈值")
        level_menu = QMenu(self)
        for level_key, display_text in LEVEL_DISPLAY_MAP.items():
            action = QAction(display_text, self)
            action.triggered.connect(lambda checked=False, key=level_key: self.notification_level_changed.emit(key))
            level_menu.addAction(action)
        self.level_status_button.setMenu(level_menu)
        buttons_group_layout.addWidget(self.level_status_button)

        self.ops_button = FlatMenuButton(" 操作 ▾")
        self.ops_button.setToolTip("更多操作")
        ops_menu = QMenu(self)
        history_action = ops_menu.addAction("查看历史记录...")
        stats_action = ops_menu.addAction("打开统计分析...")
        ops_menu.addSeparator()
        clear_db_action = ops_menu.addAction("清空历史记录...")
        font = clear_db_action.font()
        font.setBold(True)
        clear_db_action.setFont(font)
        
        history_action.triggered.connect(self.history_dialog_requested.emit)
        stats_action.triggered.connect(self.statistics_dialog_requested.emit)
        clear_db_action.triggered.connect(self.clear_database_requested.emit)
        
        self.ops_button.setMenu(ops_menu)
        buttons_group_layout.addWidget(self.ops_button)
        
        toolbar_layout.addWidget(buttons_group_container)
        return toolbar_container

    @Slot(bool, str)
    def update_toolbar_labels(self, popup_enabled: bool, notification_level: str):
        """[SLOT] 更新工具栏按钮的文本。"""
        self.popup_status_button.setText(f"  📢 {'桌面通知：启用  ' if popup_enabled else '桌面通知：禁用  '}")
        display_text = LEVEL_DISPLAY_MAP.get(notification_level, notification_level)
        self.level_status_button.setText(f"{display_text} ▾")

    @Slot(dict)
    def add_alert_to_table(self, alert_data: dict):
        """[SLOT] 向表格顶部添加新行并根据严重等级上色。"""
        timestamp = alert_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        severity = alert_data.get('severity', 'INFO')
        
        self.table.insertRow(0)
        items = [
            QTableWidgetItem(timestamp),
            QTableWidgetItem(severity),
            QTableWidgetItem(alert_data.get('type', '未知')),
            QTableWidgetItem(alert_data.get('source_ip', 'N/A')),
            QTableWidgetItem(alert_data.get('message', '无内容'))
        ]
        
        color = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["INFO"])
        for col, item in enumerate(items):
            item.setBackground(color)
            self.table.setItem(0, col, item)

    @Slot()
    def clear_table_display(self):
        """[SLOT] 只清空UI表格的显示内容。"""
        self.table.setRowCount(0)

    def eventFilter(self, obj, event: QEvent) -> bool:
        """事件过滤器，用于在页面显示时通知控制器。"""
        if obj is self and event.type() == QEvent.Type.Show:
            self.page_shown.emit()
        return super().eventFilter(obj, event)