# desktop_center/src/features/alert_center/widgets/date_filter_widget.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QDateEdit, QVBoxLayout
from PySide6.QtCore import Signal, QDate, Slot

class DateFilterWidget(QWidget):
    """
    一个可复用的日期筛选组件。
    封装了快捷日期按钮和日期范围选择器，并提供统一的信号和接口。
    """
    filter_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        # 【变更】外部依然是QHBoxLayout（为了父布局的兼容性，如果有必要）
        # 但内部现在包含一个QVBoxLayout来排列日期组件
        main_h_layout = QHBoxLayout(self)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        
        # 【新增】一个垂直布局来容纳日期选择的所有元素
        internal_v_layout = QVBoxLayout()
        internal_v_layout.setContentsMargins(0, 0, 0, 0) # 内部布局无边距
        internal_v_layout.setSpacing(5) # 调整内部间距
        
        # 快捷日期部分 (水平布局)
        shortcut_layout = QHBoxLayout()
        shortcut_layout.setContentsMargins(0, 0, 0, 0)
        shortcut_layout.addWidget(QLabel("快捷日期:"))
        self.btn_today = QPushButton("今天")
        self.btn_yesterday = QPushButton("昨天")
        self.btn_last_7_days = QPushButton("近7天")
        shortcut_layout.addWidget(self.btn_today)
        shortcut_layout.addWidget(self.btn_yesterday)
        shortcut_layout.addWidget(self.btn_last_7_days)
        shortcut_layout.addStretch() # 保持右侧对齐
        internal_v_layout.addLayout(shortcut_layout)

        # 日期范围选择器部分 (水平布局)
        date_range_layout = QHBoxLayout()
        date_range_layout.setContentsMargins(0, 0, 0, 0)
        date_range_layout.addWidget(QLabel("日期范围:"))
        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        date_range_layout.addWidget(self.start_date_edit)
        date_range_layout.addWidget(QLabel("到"))
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_range_layout.addWidget(self.end_date_edit)
        date_range_layout.addStretch() # 保持右侧对齐
        internal_v_layout.addLayout(date_range_layout)
        
        # 将内部垂直布局添加到外部主水平布局中
        main_h_layout.addLayout(internal_v_layout)
        main_h_layout.addStretch() # 确保整个widget不会水平拉伸过大

    def _connect_signals(self):
        self.btn_today.clicked.connect(lambda: self._set_date_for_shortcut("today"))
        self.btn_yesterday.clicked.connect(lambda: self._set_date_for_shortcut("yesterday"))
        self.btn_last_7_days.clicked.connect(lambda: self._set_date_for_shortcut("last7days"))
        self.start_date_edit.dateChanged.connect(lambda: self.filter_changed.emit())
        self.end_date_edit.dateChanged.connect(lambda: self.filter_changed.emit())

    def _set_date_for_shortcut(self, period: str):
        today = QDate.currentDate()
        self.start_date_edit.blockSignals(True)
        self.end_date_edit.blockSignals(True)
        
        if period == "today":
            self.start_date_edit.setDate(today)
            self.end_date_edit.setDate(today)
        elif period == "yesterday":
            yesterday = today.addDays(-1)
            self.start_date_edit.setDate(yesterday)
            self.end_date_edit.setDate(yesterday)
        elif period == "last7days":
            self.start_date_edit.setDate(today.addDays(-6))
            self.end_date_edit.setDate(today)
            
        self.start_date_edit.blockSignals(False)
        self.end_date_edit.blockSignals(False)
        self.filter_changed.emit()

    def get_date_range(self) -> tuple[str, str]:
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        return start_date, end_date

    @Slot(QDate, QDate)
    def set_date_range(self, start_date: QDate, end_date: QDate):
        self.start_date_edit.blockSignals(True)
        self.end_date_edit.blockSignals(True)
        self.start_date_edit.setDate(start_date)
        self.end_date_edit.setDate(end_date)
        self.start_date_edit.blockSignals(False)
        self.end_date_edit.blockSignals(False)