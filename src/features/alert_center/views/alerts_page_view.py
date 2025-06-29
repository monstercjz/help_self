# src/features/alert_center/views/alerts_page_view.py
from PySide6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QVBoxLayout, QLabel, QPushButton,
                               QMenu, QHBoxLayout)
from PySide6.QtCore import Slot, Qt, QEvent, QSize, Signal
from PySide6.QtGui import QColor, QIcon, QAction
from src.ui.action_manager import ActionManager

SEVERITY_COLORS = {"CRITICAL": QColor("#FFDDDD"), "WARNING": QColor("#FFFFCC"), "INFO": QColor("#FFFFFF")}
LEVEL_DISPLAY_MAP = {"INFO": "ℹ️ 正常级别", "WARNING": "⚠️ 警告级别", "CRITICAL": "❗ 危及级别"}

class FlatButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton { border: none; background-color: transparent; text-align: left; padding: 4px 8px; color: #333; font-size: 13px; }
            QPushButton:hover { background-color: #e8e8e8; border-radius: 4px; }
            QPushButton::menu-indicator { image: none; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)

class FlatMenuButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton { border: none; background-color: transparent; text-align: left; padding: 4px 8px; color: #333; font-size: 13px; }
            QPushButton:hover { background-color: #e8e8e8; border-radius: 4px; }
            QPushButton::menu-indicator { image: none; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.clicked.connect(self.showMenu)

class AlertsPageView(QWidget):
    # --- 发往Controller的信号 ---
    clear_display_requested = Signal()
    clear_database_requested = Signal()
    load_history_requested = Signal()
    page_shown = Signal()
    popup_status_toggled = Signal()
    notification_level_changed = Signal(str)

    def __init__(self, action_manager: ActionManager, parent=None):
        super().__init__(parent)
        self.action_manager = action_manager
        
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
        for i in range(4): header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.table)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.clear_button = QPushButton("清空当前显示")
        self.clear_button.setFixedWidth(120)
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)
        
        self._connect_signals()
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
        ops_menu = QMenu(self)
        ops_menu.addAction(self.action_manager.show_history)
        ops_menu.addAction(self.action_manager.show_statistics)
        ops_menu.addSeparator()
        clear_db_action = ops_menu.addAction(QIcon.fromTheme("edit-delete"), "清空历史记录...")
        clear_db_action.triggered.connect(self.clear_database_requested)
        self.ops_button.setMenu(ops_menu)
        buttons_group_layout.addWidget(self.ops_button)
        
        toolbar_layout.addWidget(buttons_group_container)
        return toolbar_container

    def _connect_signals(self):
        self.clear_button.clicked.connect(self.clear_display_requested)
        self.popup_status_button.clicked.connect(self.popup_status_toggled)

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj is self and event.type() == QEvent.Type.Show:
            self.page_shown.emit()
            if not hasattr(self, '_loaded_once'):
                self.load_history_requested.emit()
                self._loaded_once = True
        return super().eventFilter(obj, event)

    @Slot(dict)
    def add_alert_to_table(self, alert_data: dict):
        self.table.insertRow(0)
        severity = alert_data.get('severity', 'INFO')
        items = [
            QTableWidgetItem(alert_data.get('timestamp')),
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
    def clear_table(self):
        self.table.setRowCount(0)

    @Slot(bool)
    def update_popup_button_text(self, is_enabled: bool):
        self.popup_status_button.setText(f"  📢 {'桌面通知：启用  ' if is_enabled else '桌面通知：禁用  '}")

    @Slot(str)
    def update_level_button_text(self, level_key: str):
        display_text = LEVEL_DISPLAY_MAP.get(level_key, level_key)
        self.level_status_button.setText(f"{display_text} ▾")