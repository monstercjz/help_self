# src/ui/settings_page.py
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGroupBox, 
                               QLineEdit, QPushButton, QMessageBox, QFormLayout)
import logging

class SettingsPageWidget(QWidget):
    """设置功能页面，可在线编辑配置"""
    def __init__(self, config_service):
        super().__init__()
        self.config_service = config_service
        self.editors = {}

        main_layout = QVBoxLayout(self)
        
        sections = self.config_service.get_sections()
        for section in sections:
            group_box = QGroupBox(section)
            form_layout = QFormLayout()
            self.editors[section] = {}
            
            options = self.config_service.get_options(section)
            for key, value in options:
                editor = QLineEdit(value)
                form_layout.addRow(QLabel(key), editor)
                self.editors[section][key] = editor
                
            group_box.setLayout(form_layout)
            main_layout.addWidget(group_box)
            
        main_layout.addStretch()

        self.save_button = QPushButton("保存配置")
        self.save_button.setFixedWidth(120)
        self.save_button.clicked.connect(self.save_settings)
        main_layout.addWidget(self.save_button)

    def save_settings(self):
        logging.info("尝试保存配置...")
        for section, options in self.editors.items():
            for key, editor in options.items():
                self.config_service.set_option(section, key, editor.text())
        
        if self.config_service.save_config():
            QMessageBox.information(self, "成功", "配置已成功保存！")
        else:
            QMessageBox.warning(self, "失败", "保存配置时发生错误，请查看日志。")