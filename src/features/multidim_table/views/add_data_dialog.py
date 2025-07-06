# src/features/multidim_table/views/add_data_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QDialogButtonBox, QSpinBox
)

class AddDataDialog(QDialog):
    """
    一个用于添加新数据行的对话框。
    """
    def __init__(self, headers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加新数据")
        self.headers = headers
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.line_edits = {}
        for header in self.headers:
            # 为 'VIP等级' 和 '评分' 使用数字输入框
            if header in ["VIP等级", "评分", "编号"]:
                editor = QSpinBox()
                editor.setRange(0, 99999)
            else:
                editor = QLineEdit()
            
            self.line_edits[header] = editor
            form_layout.addRow(f"{header}:", editor)
        
        layout.addLayout(form_layout)

        # --- Dialog Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_data(self) -> dict:
        """从输入框中提取数据。"""
        data = {}
        for header, editor in self.line_edits.items():
            if isinstance(editor, QSpinBox):
                data[header] = editor.value()
            else:
                data[header] = editor.text()
        return data
