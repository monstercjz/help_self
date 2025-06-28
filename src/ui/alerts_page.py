# desktop_center/src/ui/alerts_page.py
import logging
from PySide6.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QVBoxLayout, QLabel, QPushButton,
                               QMessageBox, QHBoxLayout, QToolButton, QFormLayout,
                               QCheckBox, QComboBox)
from PySide6.QtCore import Slot, Qt, QEvent
from PySide6.QtGui import QColor, QIcon
from datetime import datetime
from src.services.config_service import ConfigService

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
    def __init__(self, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        
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
        self.clear_button = QPushButton("清空所有信息")
        self.clear_button.setFixedWidth(120)
        self.clear_button.clicked.connect(self.clear_table)
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)
        
        self.installEventFilter(self)

    # 【核心修改】重写此方法以实现右对齐和标签美化
    def _create_quick_settings_panel(self):
        """创建快捷设置面板及其内部控件，采用右对齐的水平布局。"""
        self.settings_panel = QWidget()
        panel_layout = QHBoxLayout(self.settings_panel)
        panel_layout.setContentsMargins(10, 5, 10, 5)
        panel_layout.setSpacing(15)
        
        # --- 核心改动：先添加伸缩项，实现右对齐 ---
        panel_layout.addStretch()

        # --- 第一个设置项 ---
        label1 = QLabel("桌面弹窗通知:")
        panel_layout.addWidget(label1)
        self.quick_enable_popup = QComboBox()
        self.quick_enable_popup.addItems(["禁用", "启用"])
        panel_layout.addWidget(self.quick_enable_popup)

        panel_layout.addSpacing(30)

        # --- 第二个设置项 ---
        label2 = QLabel("通知级别阈值:")
        panel_layout.addWidget(label2)
        self.quick_notification_level = QComboBox()
        self.quick_notification_level.addItems(["INFO", "WARNING", "CRITICAL"])
        panel_layout.addWidget(self.quick_notification_level)
        
        # --- 核心改动：应用统一的样式表 ---
        self.settings_panel.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0; 
                border-radius: 5px;
            }
            QLabel {
                background-color: transparent;
                color: #555; /* 标签文字颜色改为深灰色 */
                font-weight: bold; /* 字体加粗 */
            }
            QComboBox {
                min-width: 80px; /* 给下拉框一个最小宽度，避免太挤 */
            }
        """)
        
        self.quick_enable_popup.currentTextChanged.connect(self.save_quick_settings)
        self.quick_notification_level.currentTextChanged.connect(self.save_quick_settings)

        self.settings_panel.setVisible(False)

    def toggle_settings_panel(self):
        """切换快捷设置面板的显示/隐藏状态。"""
        is_visible = self.settings_panel.isVisible()
        self.settings_panel.setVisible(not is_visible)


    def load_settings_to_panel(self):
        """从ConfigService加载配置，并更新快捷设置面板中的控件状态。"""
        self.quick_enable_popup.blockSignals(True)
        self.quick_notification_level.blockSignals(True)
        
        enable_popup_value = self.config_service.get_value("Notification", "enable_desktop_popup", "true").lower()
        self.quick_enable_popup.setCurrentText("启用" if enable_popup_value == 'true' else "禁用")
        
        level = self.config_service.get_value("Notification", "notification_level", "WARNING")
        self.quick_notification_level.setCurrentText(level)
        
        self.quick_enable_popup.blockSignals(False)
        self.quick_notification_level.blockSignals(False)
        
    def save_quick_settings(self):
        """当快捷设置控件的值改变时，立即将新值保存到配置文件。"""
        enable_popup_text = self.quick_enable_popup.currentText()
        self.config_service.set_option("Notification", "enable_desktop_popup", "true" if enable_popup_text == "启用" else "false")
        
        self.config_service.set_option("Notification", "notification_level", self.quick_notification_level.currentText())
        
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
    def add_alert(self, alert_data: dict) -> None:
        """公开的槽函数，用于向表格安全地添加新行并根据严重等级上色。"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.table.insertRow(0)
        
        severity = alert_data.get('severity', 'INFO')
        
        items = [
            QTableWidgetItem(now),
            QTableWidgetItem(severity),
            QTableWidgetItem(alert_data.get('type', '未知')),
            QTableWidgetItem(alert_data.get('ip', 'N/A')),
            QTableWidgetItem(alert_data.get('message', '无内容'))
        ]
        
        color = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["INFO"])
        
        for col, item in enumerate(items):
            item.setBackground(color)
            self.table.setItem(0, col, item)

    def clear_table(self):
        """清空表格中的所有行，并弹出确认提示框。"""
        if self.table.rowCount() == 0:
            return
        reply = QMessageBox.question(
            self, "确认操作", "您确定要清空所有信息吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.table.setRowCount(0)
            logging.info("UI表格信息已被用户清空。")