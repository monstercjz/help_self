# desktop_center/src/features/alert_center/views/settings_dialog_view.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QSpinBox, QComboBox, QDialogButtonBox, QGroupBox)

class SettingsDialogView(QDialog):
    """
    告警中心插件的专属设置对话框。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("告警中心设置")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        
        # 网络设置
        network_group = QGroupBox("网络监听设置")
        network_layout = QFormLayout(network_group)
        self.host_input = QLineEdit()
        self.port_input = QSpinBox()
        self.port_input.setRange(1024, 65535)
        network_layout.addRow("监听地址 (host):", self.host_input)
        network_layout.addRow("监听端口 (port):", self.port_input)
        layout.addWidget(network_group)

        # 功能设置
        features_group = QGroupBox("功能与通知设置")
        features_layout = QFormLayout(features_group)
        
        self.enable_popup_input = QComboBox()
        self.enable_popup_input.addItems(["启用", "禁用"])
        self.enable_popup_map = {"启用": "true", "禁用": "false"}
        
        self.popup_timeout_input = QSpinBox()
        self.popup_timeout_input.setRange(1, 300)
        self.popup_timeout_input.setSuffix(" 秒")

        self.notification_level_input = QComboBox()
        self.notification_level_input.addItems(["INFO", "WARNING", "CRITICAL"])
        
        self.load_history_input = QComboBox()
        self.load_history_input.addItems(["不加载", "加载最近50条", "加载最近100条", "加载最近500条"])
        self.load_history_map = {"不加载": "0", "加载最近50条": "50", "加载最近100条": "100", "加载最近500条": "500"}

        features_layout.addRow("桌面弹窗通知:", self.enable_popup_input)
        features_layout.addRow("弹窗显示时长:", self.popup_timeout_input)
        features_layout.addRow("通知级别阈值:", self.notification_level_input)
        features_layout.addRow("启动时加载历史:", self.load_history_input)
        layout.addWidget(features_group)

        # 按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_settings(self) -> dict:
        """从UI控件中获取设置值。"""
        return {
            "host": self.host_input.text(),
            "port": self.port_input.value(),
            "enable_desktop_popup": self.enable_popup_map[self.enable_popup_input.currentText()],
            "popup_timeout": self.popup_timeout_input.value(),
            "notification_level": self.notification_level_input.currentText(),
            "load_history_on_startup": self.load_history_map[self.load_history_input.currentText()]
        }

    def set_settings(self, settings: dict):
        """将设置值加载到UI控件中。"""
        self.host_input.setText(settings.get("host", "0.0.0.0"))
        self.port_input.setValue(int(settings.get("port", 9527)))
        
        # 处理弹窗启用/禁用
        enable_popup_value = settings.get("enable_desktop_popup", "true")
        rev_enable_map = {v: k for k, v in self.enable_popup_map.items()}
        self.enable_popup_input.setCurrentText(rev_enable_map.get(str(enable_popup_value).lower(), "启用"))

        self.popup_timeout_input.setValue(int(settings.get("popup_timeout", 10)))
        self.notification_level_input.setCurrentText(settings.get("notification_level", "WARNING"))
        
        # 反向映射加载历史记录的设置
        rev_load_map = {v: k for k, v in self.load_history_map.items()}
        load_history_value = settings.get("load_history_on_startup", "100")
        self.load_history_input.setCurrentText(rev_load_map.get(str(load_history_value), "加载最近100条"))