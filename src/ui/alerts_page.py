import logging
from functools import partial
from PySide6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QVBoxLayout, QLabel, QPushButton,
                               QMessageBox, QHBoxLayout, QMenu, QSizePolicy)
from PySide6.QtCore import Slot, Qt, QEvent
from PySide6.QtGui import QColor, QIcon, QAction # QIcon 仍然需要，因为 "操作" 按钮还在用

from datetime import datetime
from src.services.config_service import ConfigService
from src.services.database_service import DatabaseService
from .history_dialog import HistoryDialog
from .statistics_dialog import StatisticsDialog

SEVERITY_COLORS = {
    "CRITICAL": QColor("#FFDDDD"),
    "WARNING": QColor("#FFFFCC"),
    "INFO": QColor("#FFFFFF")
}

# 1. 普通扁平按钮 (用于“启用/禁用”弹窗按钮)
class FlatButton(QPushButton):
    """一个自定义的扁平化按钮，不带菜单。"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                text-align: left; /* 图标和文本左对齐 */
                padding: 4px 8px; /* 调整内边距 */
                color: #333;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border-radius: 4px;
            }
            QPushButton::menu-indicator {
                image: none; /* 确保不显示任何菜单指示器 */
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)

# 2. 带有下拉菜单的扁平按钮 (用于“通知级别”和“操作”按钮)
class FlatMenuButton(QPushButton):
    """一个自定义的扁平化按钮，点击后弹出菜单，箭头包含在文本中。"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                text-align: left; /* 图标和文本左对齐 */
                padding: 4px 8px;
                color: #333;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border-radius: 4px;
            }
            QPushButton::menu-indicator {
                image: none; /* 必须隐藏 QPushButton 的默认菜单指示器 */
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)

        # 核心：手动连接 clicked 信号来弹出菜单
        self.clicked.connect(self._show_menu_on_click)

    def _show_menu_on_click(self):
        if self.menu():
            # 将菜单弹出在按钮的左下角位置，使其位于按钮下方
            self.menu().popup(self.mapToGlobal(self.rect().bottomLeft()))


class AlertsPageWidget(QWidget):
    """“信息接收中心”功能页面。"""
    def __init__(self, config_service: ConfigService, db_service: DatabaseService, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        self.db_service = db_service
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        toolbar_layout = self._create_toolbar()
        main_layout.addLayout(toolbar_layout)

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
        self.clear_button.clicked.connect(self.clear_table_display)
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)
        
        self.installEventFilter(self)
        self._load_history_on_startup()
        self._update_toolbar_labels() # 初次加载时更新按钮文本

    def _create_toolbar(self):
        """创建最终的、带图标和优化字体的、右对齐的工具栏。"""
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 5)

        title_label = QLabel("实时信息接收中心")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch() # 将后面的按钮推到右侧

        # 通知级别阈值按钮 (对应新图的“语言”样式，但功能是设置级别)
        self.level_status_button = FlatMenuButton() # 文本将在 _update_toolbar_labels 中设置
        self.level_status_button.setToolTip("点击选择通知级别阈值")
        # 【修改点1】移除 setIcon，因为我们将使用 Emoji 字符作为“图标”
        # self.level_status_button.setIcon(QIcon.fromTheme("emblem-important")) 
        
        level_menu = QMenu(self)
        levels = ["INFO", "WARNING", "CRITICAL"]
        for level in levels:
            action = QAction(level, self)
            action.triggered.connect(partial(self.set_notification_level, level))
            level_menu.addAction(action)
        self.level_status_button.setMenu(level_menu)
        self.level_status_button.setFixedWidth(120) # 考虑到 "CRITICAL" 文本较长，设置一个能容纳的固定宽度
        toolbar_layout.addWidget(self.level_status_button)

        # 启用/禁用桌面弹窗按钮 (对应新图的“帮助”样式，但功能是切换弹窗)
        self.popup_status_button = FlatButton("") # 文本将在 _update_toolbar_labels 中设置
        self.popup_status_button.setToolTip("点击切换启用/禁用桌面弹窗")
        self.popup_status_button.clicked.connect(self.toggle_popup_status)
        # 【修改点2】移除 setIcon，因为我们将使用 Emoji 字符作为“图标”
        # self.popup_status_button.setIcon(QIcon.fromTheme("dialog-information"))
        self.popup_status_button.setFixedWidth(90) # 固定宽度
        toolbar_layout.addWidget(self.popup_status_button)
        
        # 操作菜单按钮 (对应新图的“操作”样式，功能不变)
        self.ops_button = FlatMenuButton(" 操作 ▾") # 文本直接包含 '▾'
        self.ops_button.setToolTip("更多操作")
        ops_icon = QIcon.fromTheme("preferences-system") # 齿轮图标，这里继续使用 QIcon
        if not ops_icon.isNull():
            self.ops_button.setIcon(ops_icon)
        else:
            self.ops_button.setText("⚙️ 操作 ▾") # 如果主题图标不存在，使用 Emoji 作为后备
        
        ops_menu = QMenu(self)
        history_action = ops_menu.addAction(QIcon.fromTheme("document-open-recent"), "查看历史记录...")
        stats_action = ops_menu.addAction(QIcon.fromTheme("utilities-system-monitor"), "打开统计分析...")
        ops_menu.addSeparator()
        clear_db_action = ops_menu.addAction(QIcon.fromTheme("edit-delete"), "清空历史记录...")
        
        # 设置清空历史记录为粗体
        font = clear_db_action.font()
        font.setBold(True)
        clear_db_action.setFont(font)
        
        history_action.triggered.connect(self.show_history_dialog)
        stats_action.triggered.connect(self.show_statistics_dialog)
        clear_db_action.triggered.connect(self.clear_database)
        
        self.ops_button.setMenu(ops_menu)
        self.ops_button.setFixedWidth(100) # 固定宽度
        toolbar_layout.addWidget(self.ops_button)
        
        return toolbar_layout

    def _update_toolbar_labels(self):
        """根据当前配置更新工具栏上按钮的文本，并包含 Emoji 图标。"""
        # 更新通知级别按钮的文本，确保包含 '🔔' 和 '▾'
        level = self.config_service.get_value("InfoService", "notification_level", "WARNING")
        # 【修改点3】在文本前添加 '🔔 ' 作为图标
        self.level_status_button.setText(f"🔔 {level} ▾")

        # 更新启用/禁用按钮的文本，确保包含 'ℹ️'
        is_enabled = self.config_service.get_value("InfoService", "enable_desktop_popup", "true").lower() == 'true'
        # 【修改点4】在文本前添加 'ℹ️ ' 作为图标
        self.popup_status_button.setText(f"ℹ️ {'启用' if is_enabled else '禁用'}")

        # 操作按钮的文本是固定的，所以不需要在这里更新
        pass

    def toggle_popup_status(self):
        """切换桌面弹窗的启用/禁用状态。"""
        is_enabled = self.config_service.get_value("InfoService", "enable_desktop_popup", "true").lower() == 'true'
        new_status = not is_enabled
        self.config_service.set_option("InfoService", "enable_desktop_popup", str(new_status).lower())
        self.config_service.save_config()
        self._update_toolbar_labels() # 更新按钮文本以反映新状态
        logging.info(f"桌面弹窗状态已切换为: {'启用' if new_status else '禁用'}")

    def set_notification_level(self, level: str):
        """设置新的通知级别。"""
        self.config_service.set_option("InfoService", "notification_level", level)
        self.config_service.save_config()
        self._update_toolbar_labels() # 更新按钮文本以反映新级别
        logging.info(f"通知级别已设置为: {level}")

    def show_history_dialog(self):
        """创建并显示历史记录对话框。"""
        dialog = HistoryDialog(self.db_service, self.window())
        dialog.exec()

    def show_statistics_dialog(self):
        """创建并显示统计分析对话框。"""
        dialog = StatisticsDialog(self.db_service, self.window())
        dialog.exec()

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj is self and event.type() == QEvent.Type.Show:
            logging.info("信息接收中心页面变为可见，正在同步工具栏状态...")
            self._update_toolbar_labels() # 页面显示时也更新一下
        return super().eventFilter(obj, event)

    def _load_history_on_startup(self):
        try:
            limit_str = self.config_service.get_value("InfoService", "load_history_on_startup", "100")
            limit = int(limit_str)
            if limit > 0:
                logging.info(f"正在从数据库加载最近 {limit} 条历史记录...")
                records = self.db_service.get_recent_alerts(limit)
                for record in reversed(records):
                    self.add_alert(record, is_history=True)
        except (ValueError, TypeError) as e:
            logging.warning(f"无效的 'load_history_on_startup' 配置值: '{limit_str}'. 错误: {e}")

    @Slot(dict)
    def add_alert(self, alert_data: dict, is_history: bool = False):
        timestamp = alert_data.get('timestamp')
        if not timestamp or not is_history:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.table.insertRow(0)
        
        severity = alert_data.get('severity', 'INFO')
        
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

    def clear_table_display(self):
        self.table.setRowCount(0)
        logging.info("UI表格显示已被用户清空。")

    def clear_database(self):
        reply = QMessageBox.warning(
            self, "危险操作确认", "您确定要永久删除所有历史告警记录吗？\n此操作无法撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_service.clear_all_alerts():
                QMessageBox.information(self, "成功", "所有历史记录已成功清除。")
                self.clear_table_display()
            else:
                QMessageBox.critical(self, "失败", "清除历史记录时发生错误，请查看日志。")