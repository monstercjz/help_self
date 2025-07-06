# src/features/multidim_table/views/edit_column_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QComboBox, 
    QDialogButtonBox, QFormLayout
)

class EditColumnDialog(QDialog):
    """
    一个用于编辑字段名称和类型的对话框。
    """
    def __init__(self, old_name, old_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改字段")
        
        self.layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit(old_name)
        form_layout.addRow("字段名称:", self.name_input)

        self.type_combo = QComboBox()
        # SQLite常见数据类型
        self.type_combo.addItems(["TEXT", "INTEGER", "REAL", "BLOB", "NUMERIC"])
        self.type_combo.setCurrentText(old_type)
        form_layout.addRow("数据类型:", self.type_combo)
        
        self.layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.layout.addWidget(self.button_box)

    def get_values(self):
        """获取用户输入的新名称和新类型。"""
        return self.name_input.text(), self.type_combo.currentText()