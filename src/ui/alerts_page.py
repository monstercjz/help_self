# desktop_center/src/ui/alerts_page.py
import logging
from PySide6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QVBoxLayout, QLabel, QPushButton,
                               QMessageBox, QHBoxLayout, QToolButton, QFormLayout,
                               QComboBox)
from PySide6.QtCore import Slot, Qt, QEvent, QPoint
from PySide6.QtGui import QColor, QIcon
from datetime import datetime
from src.services.config_service import ConfigService
from src.services.database_service import DatabaseService

# 【核心修改】弹出窗口的布局逻辑将在这里重构
class _QuickSettingsPopup(QWidget):
    """一个自定义的弹出式窗口，用于显示快捷设置。"""
    def __init__(self, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1) # 几乎无边距，让内部容器控制
        
        container = QWidget()
        container.setStyleSheet("""
            QWidget#container { /* 使用对象名选择器确保样式只应用到这个容器 */
                background-color: #f7f7f7; 
                border-radius: 6px;
                border: 1px solid #ccc;
            }
        """)
        container.setObjectName("container")
        main_layout.addWidget(container)
        
        # 【核心修改】使用QVBoxLayout作为内容的主布局
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15) # 增大垂直间距

        # --- 上部分：常规设置组 ---
        settings_form_layout = QFormLayout()
        settings_form_layout.setSpacing(10)
        
        self.quick_enable_popup = QComboBox()
        self.quick_enable_popup.addItems(["禁用", "启用"])
        self.quick_notification_level = QComboBox()
        self.quick_notification_level.addItems(["INFO", "WARNING", "CRITICAL"])
        
        settings_form_layout.addRow("桌面弹窗通知:", self.quick_enable_popup)
        settings_form_layout.addRow("通知级别阈值:", self.quick_notification_level)
        content_layout.addLayout(settings_form_layout)

        # --- 下部分：危险操作组 ---
        self.clear_db_button = QPushButton("清空历史记录")
        self.clear_db_button.setToolTip("警告：此操作将永久删除所有告警历史！")
        self.clear_db_button.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #d32f2f;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #c62828; }
            QPushButton:pressed { background-color: #b71c1c; }
        """)
        self.clear_db_button.clicked.connect(self.close)
        # 将按钮添加到主垂直布局中，并设置对齐
        content_layout.addWidget(self.clear_db_button, 0, Qt.AlignmentFlag.AlignRight)

        # 连接信号，实现即时保存
        self.quick_enable_popup.currentTextChanged.connect(self.save_quick_settings)
        self.quick_notification_level.currentTextChanged.connect(self.save_quick_settings)

        self.load_settings()

    def load_settings(self):
        """加载配置到控件。"""
        enable_popup_value = self.config_service.get_value("InfoService", "enable_desktop_popup", "true").lower()
        self.quick_enable_popup.setCurrentText("启用" if enable_popup_value == 'true' else "禁用")
        level = self.config_service.get_value("InfoService", "notification_level", "WARNING")
        self.quick_notification_level.setCurrentText(level)

    def save_quick_settings(self):
        """立即保存设置。"""
        enable_popup_text = self.quick_enable_popup.currentText()
        self.config_service.set_option("InfoService", "enable_desktop_popup", "true" if enable_popup_text == "启用" else "false")
        self.config_service.set_option("InfoService", "notification_level", self.quick_notification_level.currentText())
        if self.config_service.save_config():
            logging.info("快捷设置已更新并保存。")
        else:
            logging.warning("保存快捷设置时失败。")


SEVERITY_COLORS = {
    "CRITICAL": QColor("#FFDDDD"),
    "WARNING": QColor("#FFFFCC"),
    "INFO": QColor("#FFFFFF")
}

class AlertsPageWidget(QWidget):
    """“信息接收中心”功能页面。"""
    def __init__(self, config_service: ConfigService, db_service: DatabaseService, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        self.db_service = db_service
        self.quick_settings_popup = None
        
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
        self.settings_button.setToolTip("快捷设置")
        self.settings_button.clicked.connect(self.show_quick_settings_popup)
        title_layout.addWidget(self.settings_button)
        main_layout.addLayout(title_layout)

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
        
        self._load_history_on_startup()

    def show_quick_settings_popup(self):
        """创建并显示快捷设置弹窗。"""
        self.quick_settings_popup = _QuickSettingsPopup(self.config_service)
        self.quick_settings_popup.clear_db_button.clicked.connect(self.clear_database)

        btn_pos = self.settings_button.mapToGlobal(QPoint(0, 0))
        # 调整定位逻辑，以适应可能变窄的弹窗
        # 让弹窗的右上角对齐到按钮的右下角
        popup_width = self.quick_settings_popup.sizeHint().width()
        popup_pos = QPoint(btn_pos.x() - popup_width + self.settings_button.width(), 
                           btn_pos.y() + self.settings_button.height() + 2)
        
        self.quick_settings_popup.move(popup_pos)
        self.quick_settings_popup.show()

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
        """公开的槽函数，用于向表格添加新行。"""
        timestamp = alert_data.get('timestamp')
        if not timestamp or not is_history:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.table.insertRow(0)
        
        severity = alert_data.get('severity', 'INFO')
        
        # 【核心修改】从alert_data中获取值的键名改为 'source_ip'
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
            self,
            "危险操作确认",
            "您确定要永久删除所有历史告警记录吗？\n此操作无法撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_service.clear_all_alerts():
                QMessageBox.information(self, "成功", "所有历史记录已成功清除。")
                self.clear_table_display()
            else:
                QMessageBox.critical(self, "失败", "清除历史记录时发生错误，请查看日志。")