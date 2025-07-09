# src/features/multidim_table/views/add_data_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QDateTimeEdit, QComboBox
)
from PySide6.QtCore import QDateTime

class AddDataDialog(QDialog):
    """
    一个智能的对话框，用于添加新数据行。
    它会根据字段的数据类型，动态生成最合适的输入控件。
    """
    def __init__(self, schema, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加新数据")
        self.schema = schema
        self.editors = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        for field in self.schema:
            field_name = field['name']
            field_type = field['type'].upper()
            editor = None

            if field_type == 'DATETIME':
                editor = QDateTimeEdit(self)
                editor.setCalendarPopup(True)
                editor.setDateTime(QDateTime.currentDateTime())
                editor.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            elif field_type == 'BOOLEAN':
                editor = QComboBox(self)
                editor.addItems(["True", "False"])
            elif field_type in ['INTEGER', 'REAL', 'NUMERIC']:
                editor = QLineEdit(self) # 简单起见，数字也用行编辑器，可根据需求改为QSpinBox
            else: # TEXT, BLOB, etc.
                editor = QLineEdit(self)

            self.editors[field_name] = editor
            form_layout.addRow(f"{field_name}:", editor)

        layout.addLayout(form_layout)

        # --- Dialog Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_data(self) -> dict:
        """从不同类型的编辑器中提取数据。"""
        data = {}
        for field_name, editor in self.editors.items():
            if isinstance(editor, QDateTimeEdit):
                data[field_name] = editor.text()
            elif isinstance(editor, QComboBox):
                data[field_name] = editor.currentText()
            else: # QLineEdit
                data[field_name] = editor.text()
        return data
