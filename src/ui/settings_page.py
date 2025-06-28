# desktop_center/src/ui/settings_page.py
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGroupBox,
                               QLineEdit, QPushButton, QMessageBox, QFormLayout)
from PySide6.QtCore import Qt
import logging
from src.services.config_service import ConfigService

class SettingsPageWidget(QWidget):
    """
    “设置”功能页面。
    动态地从ConfigService加载配置项，并提供UI进行修改和保存。
    """
    def __init__(self, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        self.editors = {}  # 用于存储动态创建的QLineEdit: {section: {key: editor}}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        title_label = QLabel("应用程序设置")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # --- 动态生成配置编辑区域 ---
        sections = self.config_service.get_sections()
        if not sections:
            no_config_label = QLabel("未找到任何配置项。\n请检查 config.ini 文件是否存在且内容正确。")
            no_config_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(no_config_label)
        else:
            for section in sections:
                group_box = QGroupBox(section)
                group_box.setStyleSheet("QGroupBox { font-weight: bold; }")
                form_layout = QFormLayout()
                self.editors[section] = {}
                
                options = self.config_service.get_options(section)
                for key, value in options:
                    editor = QLineEdit(value)
                    form_layout.addRow(QLabel(f"{key}:"), editor)
                    self.editors[section][key] = editor
                    
                group_box.setLayout(form_layout)
                main_layout.addWidget(group_box)
            
        main_layout.addStretch() # 添加一个伸缩空间，将按钮推到底部

        # --- 保存按钮 ---
        self.save_button = QPushButton("保存配置")
        self.save_button.setFixedWidth(120)
        self.save_button.clicked.connect(self.save_settings)
        main_layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignRight)

    def save_settings(self):
        """收集所有编辑器的内容，并通过ConfigService保存到文件。"""
        logging.info("尝试保存配置...")
        try:
            for section, options in self.editors.items():
                for key, editor in options.items():
                    self.config_service.set_option(section, key, editor.text())
            
            if self.config_service.save_config():
                QMessageBox.information(self, "成功", "配置已成功保存！")
            else:
                QMessageBox.warning(self, "失败", "保存配置时发生错误，请查看日志。")
        except Exception as e:
            logging.error(f"保存设置时发生未知错误: {e}")
            QMessageBox.critical(self, "严重错误", f"保存时发生严重错误: {e}")