# desktop_center/src/features/alert_center/widgets/ip_filter_widget.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox
from PySide6.QtCore import Signal, Slot
from typing import List

ALL_IPS_OPTION = "【全部IP】"

class IPFilterWidget(QWidget):
    """
    一个可复用的IP筛选组件。
    """
    filter_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.combo_box.currentIndexChanged.connect(self.filter_changed.emit)

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("IP地址:"))
        self.combo_box = QComboBox()
        self.combo_box.setEditable(True)
        self.combo_box.setPlaceholderText("请选择或输入IP地址")
        self.combo_box.setMinimumWidth(150)
        layout.addWidget(self.combo_box)
        layout.addStretch()
        
    def get_ip(self) -> str | None:
        ip = self.combo_box.currentText().strip()
        return None if ip == ALL_IPS_OPTION or not ip else ip

    @Slot(list)
    def set_ip_list(self, ip_list: List[str]):
        current_text = self.get_ip() or ALL_IPS_OPTION
        self.combo_box.blockSignals(True)
        self.combo_box.clear()
        self.combo_box.addItem(ALL_IPS_OPTION)
        if ip_list:
            self.combo_box.addItems(ip_list)
        
        # Restore selection
        if current_text in [ALL_IPS_OPTION] + ip_list:
            self.combo_box.setCurrentText(current_text)
        elif current_text:
            self.combo_box.setEditText(current_text)
        else:
            self.combo_box.setCurrentIndex(0)
        self.combo_box.blockSignals(False)