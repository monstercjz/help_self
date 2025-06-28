# desktop_center/src/ui/settings_page.py
import logging
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGroupBox,
                               QLineEdit, QPushButton, QMessageBox, QFormLayout,
                               QComboBox, QSpinBox, QScrollArea, QHBoxLayout)
from PySide6.QtCore import Qt, QEvent

from src.services.config_service import ConfigService

SETTING_METADATA = {
    "General": {
        "app_name": {"widget": "lineedit", "label": "应用程序名称"},
        "start_minimized": {"widget": "combobox", "label": "启动时最小化到系统托盘", "items": ["禁用", "启用"], "map": {"启用": "true", "禁用": "false"}}
    },
    "WebServer": {
        "host": {"widget": "lineedit", "label": "监听地址 (0.0.0.0代表所有)"},
        "port": {"widget": "spinbox", "label": "监听端口", "min": 1024, "max": 65535}
    },
    "Notification": {
        "enable_desktop_popup": {"widget": "combobox", "label": "桌面弹窗通知", "items": ["禁用", "启用"], "map": {"启用": "true", "禁用": "false"}},
        "popup_timeout": {"widget": "spinbox", "label": "弹窗显示时长 (秒)", "min": 1, "max": 300},
        "notification_level": {"widget": "combobox", "label": "通知级别阈值", "items": ["INFO", "WARNING", "CRITICAL"]}
    }
}

class SettingsPageWidget(QWidget):
    """
    “设置”功能页面。
    采用“元数据驱动”和“卡片式布局”进行重构，提升了可维护性和用户体验。
    """
    def __init__(self, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        self.editors = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("应用程序设置")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px; color: #333;")
        main_layout.addWidget(title_label)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        content_widget = QWidget()
        self.settings_layout = QVBoxLayout(content_widget)
        self.settings_layout.setSpacing(15)
        self.settings_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        self._create_setting_cards()

        self.save_button = QPushButton("保存所有设置")
        self.save_button.setMinimumHeight(35)
        self.save_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        self.save_button.clicked.connect(self.save_settings)
        main_layout.addWidget(self.save_button, 0, Qt.AlignmentFlag.AlignRight)

        self.installEventFilter(self)

    # 【核心修改】重写此方法以实现最终的嵌套布局
    def _create_setting_cards(self):
        """根据元数据动态创建所有设置卡片，并使用嵌套布局。"""
        
        # --- 1. 创建 "General" 卡片 (保持独立) ---
        if "General" in SETTING_METADATA:
            general_card = self._build_card_group("General", SETTING_METADATA["General"])
            self.settings_layout.addWidget(general_card)
        
        # --- 2. 创建一个大的父容器 "信息服务设置" ---
        info_service_group = QGroupBox("信息服务设置")
        info_service_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                background-color: #fcfcfc;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                left: 10px;
                background-color: #fcfcfc;
            }
        """)
        
        # 在父容器内部使用水平布局
        sub_layout = QHBoxLayout(info_service_group)
        sub_layout.setSpacing(40) # 增大两列之间的间距
        sub_layout.setContentsMargins(20, 30, 20, 20)

        # --- 3. 创建 WebServer 和 Notification 的内部控件组 (使用QFormLayout) ---
        if "WebServer" in SETTING_METADATA:
            webserver_layout = QFormLayout()
            webserver_layout.setSpacing(12)
            self._populate_form_layout(webserver_layout, "WebServer", SETTING_METADATA["WebServer"])
            sub_layout.addLayout(webserver_layout)

        if "Notification" in SETTING_METADATA:
            notification_layout = QFormLayout()
            notification_layout.setSpacing(12)
            self._populate_form_layout(notification_layout, "Notification", SETTING_METADATA["Notification"])
            sub_layout.addLayout(notification_layout)
        
        # 将整个大的父容器添加到主布局中
        self.settings_layout.addWidget(info_service_group)

    # 【新增】辅助方法，用于填充一个QFormLayout
    def _populate_form_layout(self, form_layout: QFormLayout, section_name: str, options_meta: dict):
        """根据元数据，将控件填充到给定的QFormLayout中。"""
        if section_name not in self.editors:
            self.editors[section_name] = {}
        
        for key, meta in options_meta.items():
            widget_type = meta["widget"]
            label_text = meta["label"]
            editor_widget = None

            if widget_type == "lineedit":
                editor_widget = QLineEdit()
            elif widget_type == "spinbox":
                editor_widget = QSpinBox()
                editor_widget.setRange(meta.get("min", 0), meta.get("max", 99999))
            elif widget_type == "combobox":
                editor_widget = QComboBox()
                editor_widget.addItems(meta["items"])
                editor_widget.setMaximumWidth(250)

            if editor_widget:
                form_layout.addRow(QLabel(f"{label_text}:"), editor_widget)
                self.editors[section_name][key] = editor_widget

    # 【重命名】将_build_card重命名并简化，因为它现在只负责 "General"
    def _build_card_group(self, section_name: str, options_meta: dict) -> QGroupBox:
        """为独立的区段构建一个完整的QGroupBox卡片。"""
        card = QGroupBox(section_name)
        card.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                background-color: #fcfcfc;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                left: 10px;
                background-color: #fcfcfc;
            }
        """)
        
        form_layout = QFormLayout(card)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(20, 30, 20, 20)
        
        self._populate_form_layout(form_layout, section_name, options_meta)
        return card

    def _load_settings_to_ui(self):
        logging.info("正在同步全局设置页面UI...")
        for section, options in self.editors.items():
            for key, widget in options.items():
                meta = SETTING_METADATA[section][key]
                current_value = self.config_service.get_value(section, key)

                if isinstance(widget, QLineEdit):
                    widget.setText(current_value)
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(current_value) if current_value and current_value.isdigit() else meta.get("min", 0))
                elif isinstance(widget, QComboBox):
                    if "map" in meta:
                        display_text = "启用" if current_value == "true" else "禁用"
                        widget.setCurrentText(display_text)
                    else:
                        if current_value in meta["items"]:
                            widget.setCurrentText(current_value)

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj is self and event.type() == QEvent.Type.Show:
            self._load_settings_to_ui()
        return super().eventFilter(obj, event)

    def save_settings(self):
        logging.info("尝试保存所有设置...")
        try:
            for section, options in self.editors.items():
                for key, widget in options.items():
                    meta = SETTING_METADATA[section][key]
                    value = None
                    if isinstance(widget, QLineEdit):
                        value = widget.text()
                    elif isinstance(widget, QSpinBox):
                        value = str(widget.value())
                    elif isinstance(widget, QComboBox):
                        if "map" in meta:
                            value = meta["map"][widget.currentText()]
                        else:
                            value = widget.currentText()
                    
                    if value is not None:
                        self.config_service.set_option(section, key, value)
            
            if self.config_service.save_config():
                QMessageBox.information(self, "成功", "所有设置已成功保存！")
            else:
                QMessageBox.warning(self, "失败", "保存设置时发生错误，请查看日志。")
        except Exception as e:
            logging.error(f"保存设置时发生未知错误: {e}", exc_info=True)
            QMessageBox.critical(self, "严重错误", f"保存设置时发生严重错误: {e}")