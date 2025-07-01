# desktop_center/src/features/program_launcher/widgets/add_program_dialog.py
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox, QLabel,
                               QFormLayout, QComboBox, QPushButton, QHBoxLayout, QFileDialog)
from PySide6.QtCore import Slot

class AddProgramDialog(QDialog):
    """
    一个专用的对话框，用于添加新程序。
    """
    def __init__(self, groups: list, default_group_id: str = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加新程序")
        self.setMinimumWidth(450)

        # -- UI 组件 --
        layout = QFormLayout(self)
        layout.setSpacing(10)

        # 分组选择
        self.group_combo = QComboBox()
        for group in groups:
            self.group_combo.addItem(group['name'], group['id'])
        
        if default_group_id:
            index = self.group_combo.findData(default_group_id)
            if index != -1:
                self.group_combo.setCurrentIndex(index)
        
        # 程序名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如：谷歌浏览器")

        # 文件路径
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("请选择可执行文件...")
        self.browse_btn = QPushButton("浏览...")
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_btn)

        # 对话框按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False) # 默认禁用OK按钮

        layout.addRow(QLabel("所属分组:"), self.group_combo)
        layout.addRow(QLabel("程序名称:"), self.name_edit)
        layout.addRow(QLabel("文件路径:"), path_layout)
        layout.addRow(self.button_box)

        # -- 连接信号 --
        self.browse_btn.clicked.connect(self.browse_file)
        self.name_edit.textChanged.connect(self.validate_input)
        self.path_edit.textChanged.connect(self.validate_input)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    @Slot()
    def browse_file(self):
        """打开文件对话框以选择文件。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择一个可执行文件",
            "",
            "可执行文件 (*.exe);;所有文件 (*)"
        )
        if file_path:
            self.path_edit.setText(file_path)
            # 自动填充程序名称 (如果名称为空)
            if not self.name_edit.text():
                program_name = os.path.splitext(os.path.basename(file_path))[0]
                self.name_edit.setText(program_name.replace('_', ' ').title())

    @Slot()
    def validate_input(self):
        """验证输入是否有效，以启用/禁用OK按钮。"""
        name_ok = bool(self.name_edit.text().strip())
        path_ok = bool(self.path_edit.text().strip())
        self.ok_button.setEnabled(name_ok and path_ok)

    def get_program_details(self) -> tuple[str, str, str]:
        """
        【修改】获取用户输入的程序详情。
        此方法假定在对话框被接受(Accepted)后调用。
        """
        group_id = self.group_combo.currentData()
        program_name = self.name_edit.text().strip()
        file_path = self.path_edit.text().strip()
        return group_id, program_name, file_path