# desktop_center/src/ui/alerts_page.py
import logging
from PySide6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QVBoxLayout, QLabel, QPushButton,
                               QMessageBox, QHBoxLayout, QToolButton, QFormLayout,
                               QComboBox)
from PySide6.QtCore import Slot, Qt, QEvent
from PySide6.QtGui import QColor, QIcon
from datetime import datetime
from src.services.config_service import ConfigService
from src.services.database_service import DatabaseService

SEVERITY_COLORS = {
    "CRITICAL": QColor("#FFDDDD"),
    "WARNING": QColor("#FFFFCC"),
    "INFO": QColor("#FFFFFF")
}

class AlertsPageWidget(QWidget):
    """
    “信息接收中心”功能页面。
    包含实时信息表格和快捷设置面板，实现了混合设置模式。
    """
    def __init__(self, config_service: ConfigService, db_service: DatabaseService, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        self.db_service = db_service
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        title_layout = QHBoxLayout()
        title_label = QLabel("实时信息接收中心")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        self.settings_button = QToolButton()
        icon = QIcon.fromTheme("preferences-system")
        if icon.isNull():
            self.settings_button.setText("⚙️")
            self.settings_button.setFixedSize(32, 32)
            self.settings_button.setStyleSheet("font-size: 18px;")
        else:
            self.settings_button.setIcon(icon)
        self.settings_button.setToolTip("显示/隐藏快捷设置")
        self.settings_button.clicked.connect(self.toggle_settings_panel)
        title_layout.addWidget(self.settings_button)
        main_layout.addLayout(title_layout)

        self._create_quick_settings_panel()
        main_layout.addWidget(self.settings_panel)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["接收时间", "严重等级", "信息类型", "来源IP", "详细内容"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
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

    def _create_quick_settings_panel(self):
        """创建快捷设置面板及其内部控件，采用水平布局。"""
        self.settings_panel = QWidget()
        panel_layout = QHBoxLayout(self.settings_panel)
        panel_layout.setContentsMargins(10, 5, 10, 5)
        panel_layout.setSpacing(15)
        
        # --- 创建左侧的普通设置 ---
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.quick_enable_popup = QComboBox()
        self.quick_enable_popup.addItems(["禁用", "启用"])
        self.quick_notification_level = QComboBox()
        self.quick_notification_level.addItems(["INFO", "WARNING", "CRITICAL"])
        
        form_layout.addRow("桌面弹窗通知:", self.quick_enable_popup)
        form_layout.addRow("通知级别阈值:", self.quick_notification_level)
        panel_layout.addLayout(form_layout)
        
        panel_layout.addStretch()

        # --- 创建右侧的危险操作按钮 ---
        self.clear_db_button = QPushButton("清空历史记录")
        self.clear_db_button.setStyleSheet("color: #d32f2f; font-weight: bold;")
        self.clear_db_button.setToolTip("警告：此操作将永久删除所有告警历史！")
        self.clear_db_button.clicked.connect(self.clear_database)
        panel_layout.addWidget(self.clear_db_button)

        self.settings_panel.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        
        self.quick_enable_popup.currentTextChanged.connect(self.save_quick_settings)
        self.quick_notification_level.currentTextChanged.connect(self.save_quick_settings)

        self.settings_panel.setVisible(False)

    def _load_history_on_startup(self):
        """在程序启动时，根据配置加载历史告警记录。"""
        try:
            limit_str = self.config_service.get_value("InfoService", "load_history_on_startup", "100")
            limit = int(limit_str)
            if limit > 0:
                logging.info(f"正在从数据库加载最近 {limit} 条历史记录...")
                records = self.db_service.get_recent_alerts(limit)
                # 反转列表，让最新的记录在最上面
                for record in reversed(records):
                    self.add_alert(record, is_history=True)
        except (ValueError, TypeError) as e:
            logging.warning(f"无效的 'load_history_on_startup' 配置值: '{limit_str}'. 错误: {e}")

    def toggle_settings_panel(self):
        """切换快捷设置面板的显示/隐藏状态。"""
        is_visible = self.settings_panel.isVisible()
        self.settings_panel.setVisible(not is_visible)

    def load_settings_to_panel(self):
        """从ConfigService加载配置，并更新快捷设置面板中的控件状态。"""
        self.quick_enable_popup.blockSignals(True)
        self.quick_notification_level.blockSignals(True)
        
        enable_popup_value = self.config_service.get_value("InfoService", "enable_desktop_popup", "true").lower()
        self.quick_enable_popup.setCurrentText("启用" if enable_popup_value == 'true' else "禁用")

        level = self.config_service.get_value("InfoService", "notification_level", "WARNING")
        self.quick_notification_level.setCurrentText(level)
        
        self.quick_enable_popup.blockSignals(False)
        self.quick_notification_level.blockSignals(False)
        
    def save_quick_settings(self):
        """当快捷设置控件的值改变时，立即将新值保存到配置文件。"""
        enable_popup_text = self.quick_enable_popup.currentText()
        self.config_service.set_option("InfoService", "enable_desktop_popup", "true" if enable_popup_text == "启用" else "false")
        self.config_service.set_option("InfoService", "notification_level", self.quick_notification_level.currentText())
        if self.config_service.save_config():
            logging.info("快捷设置已更新并保存。")
        else:
            logging.warning("保存快捷设置时失败。")

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj is self and event.type() == QEvent.Type.Show:
            logging.info("信息接收中心页面变为可见，正在同步快捷设置...")
            self.load_settings_to_panel()
        return super().eventFilter(obj, event)

    @Slot(dict)
    def add_alert(self, alert_data: dict, is_history: bool = False):
        """公开的槽函数，用于向表格添加新行。"""
        # 如果是历史记录，直接使用数据库中的时间戳
        timestamp = alert_data.get('timestamp')
        if not timestamp or not is_history:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.table.insertRow(0)
        
        severity = alert_data.get('severity', 'INFO')
        
        items = [
            QTableWidgetItem(timestamp),
            QTableWidgetItem(severity),
            QTableWidgetItem(alert_data.get('type', '未知')),
            QTableWidgetItem(alert_data.get('ip', 'N/A')),
            QTableWidgetItem(alert_data.get('message', '无内容'))
        ]
        
        color = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["INFO"])
        
        for col, item in enumerate(items):
            item.setBackground(color)
            self.table.setItem(0, col, item)

    def clear_table_display(self):
        """只清空UI表格的显示内容。"""
        self.table.setRowCount(0)
        logging.info("UI表格显示已被用户清空。")

    def clear_database(self):
        """清空数据库中的所有历史记录，并带有严格的确认。"""
        reply = QMessageBox.warning(
            self,
            "危险操作确认",
            "您确定要永久删除所有历史告警记录吗？\n此操作无法撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_service.clear_all_alerts():
                QMessageBox.information(self, "成功", "所有历史记录已成功清除。")
                # 可选：同时清空当前显示
                self.clear_table_display()
            else:
                QMessageBox.critical(self, "失败", "清除历史记录时发生错误，请查看日志。")