# desktop_center/src/features/program_launcher/widgets/empty_state_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, Signal

class EmptyStateWidget(QWidget):
    """
    一个用于显示空状态的占位符控件，引导用户进行初始操作。
    """
    add_group_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # 图标
        icon_label = QLabel()
        # 使用一个通用的、友好的图标
        pixmap = QIcon.fromTheme("document-new").pixmap(64, 64)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 标题
        title_label = QLabel("欢迎使用程序启动器")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        # 描述
        description_label = QLabel("这里还没有任何内容。\n点击下方的按钮，从创建第一个分组开始吧！")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setStyleSheet("font-size: 14px; color: #888;")

        # 动作按钮
        self.add_group_btn = QPushButton(QIcon.fromTheme("list-add"), " 创建第一个分组")
        self.add_group_btn.setStyleSheet("padding: 10px 20px; font-size: 16px;")
        self.add_group_btn.clicked.connect(self.add_group_requested)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addWidget(self.add_group_btn)