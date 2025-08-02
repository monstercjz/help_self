# src/features/memo_pad/widgets/note_card_widget.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt
from src.features.memo_pad.models.memo_model import Memo

class NoteCardWidget(QWidget):
    """
    一个自定义控件，用于在列表中以“卡片”形式显示单条备忘录的摘要信息。
    """
    def __init__(self, memo: Memo, parent=None):
        super().__init__(parent)
        self.memo = memo
        self._init_ui()
        self.update_content(memo)

    def _init_ui(self):
        """初始化UI布局和组件。"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

        self.title_label = QLabel()
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        self.summary_label = QLabel()
        self.summary_label.setObjectName("summaryLabel")
        self.summary_label.setWordWrap(True)
        self.summary_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        self.date_label = QLabel()
        self.date_label.setObjectName("dateLabel")
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.summary_label)
        self.layout.addStretch()
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0,0,0,0)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.date_label)
        self.layout.addLayout(bottom_layout)

        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
            #titleLabel, #summaryLabel, #dateLabel {
                background-color: transparent;
                border: none;
            }
            #titleLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333333;
            }
            #summaryLabel {
                font-size: 12px;
                color: #666666;
            }
            #dateLabel {
                font-size: 10px;
                color: #999999;
            }
        """)

    def update_content(self, memo: Memo):
        """用新的备忘录数据更新卡片内容。"""
        self.memo = memo
        self.title_label.setText(memo.title or "新笔记")
        
        # 生成内容摘要
        summary = memo.content.strip().split('\n')[0]
        if len(summary) > 50:
            summary = summary[:50] + "..."
        self.summary_label.setText(summary)
        
        self.date_label.setText(memo.updated_at.strftime("%Y-%m-%d %H:%M"))
