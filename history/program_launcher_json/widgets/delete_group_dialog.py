# desktop_center/src/features/program_launcher/widgets/delete_group_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QRadioButton,
                               QComboBox, QDialogButtonBox, QWidget, QHBoxLayout)

class DeleteGroupDialog(QDialog):
    """
    一个自定义对话框，用于处理删除非空分组时的用户选择。
    """
    def __init__(self, group_name: str, other_groups: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("删除分组")
        self.setMinimumWidth(350)

        self.other_groups = other_groups
        self.result = (None, None)

        layout = QVBoxLayout(self)
        
        main_label = QLabel(f"分组 '{group_name}' 不为空。请选择如何处理其中的程序：")
        layout.addWidget(main_label)

        # 选项1: 移动到其他分组
        self.move_radio = QRadioButton("将所有程序移动到另一个分组:")
        layout.addWidget(self.move_radio)
        
        move_widget = QWidget()
        move_layout = QHBoxLayout(move_widget)
        move_layout.setContentsMargins(20, 0, 0, 0)
        self.group_combo = QComboBox()
        for group in self.other_groups:
            self.group_combo.addItem(group['name'], group['id'])
        move_layout.addWidget(self.group_combo)
        layout.addWidget(move_widget)
        
        # 选项2: 删除所有程序
        self.delete_all_radio = QRadioButton("删除此分组及其中的所有程序")
        layout.addWidget(self.delete_all_radio)

        # 根据是否有其他分组来设置默认状态
        if self.other_groups:
            self.move_radio.setChecked(True)
        else:
            self.move_radio.setText("将所有程序移动到一个新的'默认分组'")
            self.move_radio.setChecked(True)
            self.group_combo.setVisible(False)
        
        self.move_radio.toggled.connect(self.group_combo.setEnabled)

        # 按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def accept(self):
        """当用户点击OK时，保存结果。"""
        if self.move_radio.isChecked():
            target_group_id = self.group_combo.currentData() if self.other_groups else None
            self.result = ('move', target_group_id)
        elif self.delete_all_radio.isChecked():
            self.result = ('delete_all', None)
        super().accept()

    def get_result(self) -> tuple:
        """获取用户的选择结果。"""
        return self.result