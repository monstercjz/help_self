# desktop_center/src/ui/settings_page.py
import logging
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGroupBox,
                               QLineEdit, QPushButton, QMessageBox, QFormLayout,
                               QComboBox, QSpinBox, QScrollArea, QHBoxLayout)
from PySide6.QtCore import Qt, QEvent

from src.services.config_service import ConfigService

# 【核心修改】元数据结构现在与最终的config.ini完全匹配
SETTING_METADATA = {
    "General": {
        "app_name": {"widget": "lineedit", "label": "应用程序名称"},
        "start_minimized": {"widget": "combobox", "label": "启动时最小化", "items": ["禁用", "启用"], "map": {"启用": "true", "禁用": "false"}}
    },
    "InfoService": { # 新的统一区段
        "host": {"widget": "lineedit", "label": "监听地址", "col": 0},
        "port": {"widget": "spinbox", "label": "监听端口", "min": 1024, "max": 65535, "col": 0},
        "enable_desktop_popup": {"widget": "combobox", "label": "桌面弹窗通知", "items": ["禁用", "启用"], "map": {"启用": "true", "禁用": "false"}, "col": 0},
        "popup_timeout": {"widget": "spinbox", "label": "弹窗显示时长 (秒)", "min": 1, "max": 300, "col": 1},
        "notification_level": {"widget": "combobox", "label": "通知级别阈值", "items": ["INFO", "WARNING", "CRITICAL"], "col": 1},
        "load_history_on_startup": {"widget": "combobox", "label": "启动时加载历史", "items": ["不加载", "加载最近50条", "加载最近100条", "加载最近500条"], "map": {"不加载": "0", "加载最近50条": "50", "加载最近100条": "100", "加载最近500条": "500"}, "col": 1}
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
            QPushButton { font-size: 14px; font-weight: bold; background-color: #0078d4; color: white; border: none; border-radius: 5px; padding: 0 20px; }
            QPushButton:hover { background-color: #005a9e; }
            QPushButton:pressed { background-color: #004578; }
        """)
        self.save_button.clicked.connect(self.save_settings)
        main_layout.addWidget(self.save_button, 0, Qt.AlignmentFlag.AlignRight)

        self.installEventFilter(self)

    # 【核心修改】UI创建逻辑大幅简化
    def _create_setting_cards(self):
        """根据元数据动态创建所有设置卡片。"""
        for section, options_meta in SETTING_METADATA.items():
            card = QGroupBox(section)
            card.setStyleSheet("""
                QGroupBox { font-size: 16px; font-weight: bold; color: #333; background-color: #fcfcfc; border: 1px solid #e0e0e0; border-radius: 8px; margin-top: 10px; }
                QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; left: 10px; background-color: #fcfcfc; }
            """)
            
            # 【核心修改】根据section名，选择不同的布局策略
            if section == "InfoService":
                self._populate_multi_column_layout(card, section, options_meta)
            else:
                form_layout = QFormLayout(card)
                form_layout.setSpacing(12)
                form_layout.setContentsMargins(20, 30, 20, 20)
                self._populate_form_layout(form_layout, section, options_meta)
            
            self.settings_layout.addWidget(card)

    def _populate_multi_column_layout(self, parent_group: QGroupBox, section_name: str, options_meta: dict):
        """为InfoService卡片创建多列布局。"""
        # 主水平布局
        main_hbox = QHBoxLayout(parent_group)
        main_hbox.setSpacing(40)
        main_hbox.setContentsMargins(20, 30, 20, 20)

        # 创建两个垂直的表单布局作为列
        column1_layout = QFormLayout()
        column1_layout.setSpacing(12)
        column2_layout = QFormLayout()
        column2_layout.setSpacing(12)

        # 根据元数据中的 'col' 键，将控件分配到不同的列
        for key, meta in options_meta.items():
            target_layout = column1_layout if meta.get("col", 0) == 0 else column2_layout
            self._add_widget_to_form(target_layout, section_name, key, meta)
        
        main_hbox.addLayout(column1_layout)
        main_hbox.addLayout(column2_layout)

    def _populate_form_layout(self, form_layout: QFormLayout, section_name: str, options_meta: dict):
        """将控件填充到给定的单列QFormLayout中。"""
        for key, meta in options_meta.items():
            self._add_widget_to_form(form_layout, section_name, key, meta)

    def _add_widget_to_form(self, form_layout: QFormLayout, section_name: str, key: str, meta: dict):
        """辅助方法：创建一个控件并将其添加到表单布局中。"""
        if section_name not in self.editors:
            self.editors[section_name] = {}
            
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
            editor_widget.setMaximumWidth(200) # 稍微减小最大宽度

        if editor_widget:
            form_layout.addRow(QLabel(f"{label_text}:"), editor_widget)
            self.editors[section_name][key] = editor_widget

    # ... (其他方法保持不变, 逻辑上不再需要做任何特殊处理)

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
                        display_text = next((text for text, val in meta["map"].items() if val == current_value), meta["items"][0])
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
                            value = meta["map"].get(widget.currentText())
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