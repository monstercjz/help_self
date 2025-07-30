# src/features/multidim_table/views/edit_column_dialog.py
import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QFormLayout, QLabel
)

class EditColumnDialog(QDialog):
    """
    一个用于编辑字段名称和类型的对话框，支持ENUM类型。
    """
    def __init__(self, old_name, old_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改字段")

        self.layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit(old_name)
        form_layout.addRow("字段名称:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["TEXT", "INTEGER", "REAL", "DATETIME", "BOOLEAN", "ENUM", "ENUM_MULTI", "BLOB", "NUMERIC"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        form_layout.addRow("数据类型:", self.type_combo)

        # 用于ENUM类型的额外输入
        self.enum_label = QLabel("预设选项 (用逗号分隔):")
        self.enum_input = QLineEdit()
        self.enum_label.setVisible(False)
        self.enum_input.setVisible(False)
        form_layout.addRow(self.enum_label, self.enum_input)

        self.layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self._set_initial_state(old_type)

    def _set_initial_state(self, old_type):
        """根据旧类型设置对话框的初始状态。"""
        if old_type.upper().startswith("ENUM"):
            if "ENUM_MULTI" in old_type.upper():
                self.type_combo.setCurrentText("ENUM_MULTI")
                match = re.match(r"ENUM_MULTI\((.*)\)", old_type, re.IGNORECASE)
            else:
                self.type_combo.setCurrentText("ENUM")
                match = re.match(r"ENUM\((.*)\)", old_type, re.IGNORECASE)
            
            if match:
                self.enum_input.setText(match.group(1))
        else:
            self.type_combo.setCurrentText(old_type)

    def get_values(self):
        """获取用户输入的新名称和（可能被编码的）新类型。"""
        name = self.name_input.text()
        col_type = self.type_combo.currentText()
        if col_type == "ENUM":
            options = self.enum_input.text().strip()
            if options:
                return name, f"ENUM({options})"
            else:
                return name, "TEXT"
        elif col_type == "ENUM_MULTI":
            options = self.enum_input.text().strip()
            if options:
                return name, f"ENUM_MULTI({options})"
            else:
                return name, "TEXT"
        return name, col_type

    def _on_type_changed(self, text):
        """当类型下拉框变化时，控制ENUM输入框的可见性。"""
        is_enum = (text == "ENUM" or text == "ENUM_MULTI")
        self.enum_label.setVisible(is_enum)
        self.enum_input.setVisible(is_enum)