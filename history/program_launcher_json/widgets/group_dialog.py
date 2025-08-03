# desktop_center/src/features/program_launcher/widgets/group_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox, QLabel

class GroupDialog(QDialog):
    """
    一个简单的对话框，用于获取用户输入的分组名称。
    """
    def __init__(self, parent=None, current_name=""):
        super().__init__(parent)
        self.setWindowTitle("分组信息")
        
        layout = QVBoxLayout(self)
        
        self.label = QLabel("分组名称:")
        self.line_edit = QLineEdit()
        if current_name:
            self.line_edit.setText(current_name)
            self.setWindowTitle("重命名分组")

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.button_box)
        
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.line_edit.returnPressed.connect(self.accept)

    def get_group_name(self) -> str:
        """获取用户输入的文本。"""
        return self.line_edit.text().strip()