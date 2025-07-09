# desktop_center/src/features/program_launcher/widgets/add_program_dialog.py
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox, QLabel,
                                 QFormLayout, QComboBox, QPushButton, QHBoxLayout, QFileDialog,
                                 QMessageBox, QCheckBox)
from PySide6.QtCore import Slot, QFileInfo

class AddProgramDialog(QDialog):
    """
    一个专用的对话框，用于添加新程序或编辑现有程序。
    """
    # 【核心修复】增加 default_group_id 参数以支持快捷添加模式
    def __init__(self, groups: list, program_to_edit: dict = None, default_group_id: str = None, parent=None):
        super().__init__(parent)
        self.is_edit_mode = program_to_edit is not None

        title = "编辑程序" if self.is_edit_mode else "添加新程序"
        self.setWindowTitle(title)
        self.setMinimumWidth(450)

        # -- UI 组件 --
        layout = QFormLayout(self)
        layout.setSpacing(10)

        # 分组选择
        self.group_combo = QComboBox()
        for group in groups:
            self.group_combo.addItem(group['name'], group['id'])
        
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

        # 以管理员身份运行
        self.run_as_admin_checkbox = QCheckBox("以管理员身份运行")
        self.run_as_admin_checkbox.setToolTip("如果勾选，程序将尝试以提升的权限启动。")

        # 对话框按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        
        # 【核心修复】重构预设值逻辑
        group_id_to_select = None
        if self.is_edit_mode:
            self.name_edit.setText(program_to_edit.get('name', ''))
            self.path_edit.setText(program_to_edit.get('path', ''))
            self.run_as_admin_checkbox.setChecked(program_to_edit.get('run_as_admin', False))
            group_id_to_select = program_to_edit.get('group_id')
        elif default_group_id:
            group_id_to_select = default_group_id
        
        if group_id_to_select:
            index = self.group_combo.findData(group_id_to_select)
            if index != -1:
                self.group_combo.setCurrentIndex(index)
        
        self.ok_button.setEnabled(False)
        self.validate_input()

        layout.addRow(QLabel("所属分组:"), self.group_combo)
        layout.addRow(QLabel("程序名称:"), self.name_edit)
        layout.addRow(QLabel("文件路径:"), path_layout)
        layout.addRow(self.run_as_admin_checkbox)
        layout.addRow(self.button_box)

        # -- 连接信号 --
        self.browse_btn.clicked.connect(self.browse_file)
        self.name_edit.textChanged.connect(self.validate_input)
        self.path_edit.textChanged.connect(self.validate_input)
        self.button_box.accepted.connect(self.on_accept)
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
            if not self.name_edit.text() and not self.is_edit_mode:
                program_name = os.path.splitext(os.path.basename(file_path))[0]
                self.name_edit.setText(program_name.replace('_', ' ').title())

    @Slot()
    def validate_input(self):
        """验证输入是否有效，以启用/禁用OK按钮。"""
        name_ok = bool(self.name_edit.text().strip())
        path_ok = bool(self.path_edit.text().strip())
        self.ok_button.setEnabled(name_ok and path_ok)

    @Slot()
    def on_accept(self):
        """
        在接受对话框前，验证文件路径的有效性。
        """
        file_path = self.path_edit.text().strip()
        file_info = QFileInfo(file_path)

        if not file_info.exists():
            QMessageBox.warning(self, "路径无效", f"文件路径不存在：\n{file_path}")
            return
        
        if not file_info.isFile():
            QMessageBox.warning(self, "路径无效", f"指定的路径不是一个文件：\n{file_path}")
            return

        # 在Windows上，可以进一步检查是否为.exe，但为了跨平台兼容性，我们只检查isExecutable
        # if sys.platform == "win32" and not file_path.lower().endswith('.exe'):
        #     reply = QMessageBox.question(self, "非标准文件", "这个文件似乎不是一个标准的可执行文件 (.exe)。\n您确定要添加吗？",
        #                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        #                                  QMessageBox.StandardButton.No)
        #     if reply == QMessageBox.StandardButton.No:
        #         return

        if not file_info.isExecutable():
             QMessageBox.warning(self, "文件不可执行", f"系统报告该文件不可执行：\n{file_path}")
             return

        self.accept()

    def get_program_details(self) -> tuple[str, str, str, bool]:
        """获取用户输入的程序详情。"""
        group_id = self.group_combo.currentData()
        program_name = self.name_edit.text().strip()
        file_path = self.path_edit.text().strip()
        run_as_admin = self.run_as_admin_checkbox.isChecked()
        return group_id, program_name, file_path, run_as_admin