# desktop_center/src/features/alert_center/widgets/date_filter_widget.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QDateEdit
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
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        shortcut_layout = QHBoxLayout()
        shortcut_layout.addWidget(QLabel("快捷日期:"))
        self.btn_today = QPushButton("今天")
        self.btn_yesterday = QPushButton("昨天")
        self.btn_last_7_days = QPushButton("近7天")
        shortcut_layout.addWidget(self.btn_today)
        shortcut_layout.addWidget(self.btn_yesterday)
        shortcut_layout.addWidget(self.btn_last_7_days)
        layout.addLayout(shortcut_layout)

        layout.addWidget(QLabel("日期范围:"))
        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        layout.addWidget(self.start_date_edit)
        layout.addWidget(QLabel("到"))
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit.setDate(QDate.currentDate())
        layout.addWidget(self.end_date_edit)
        
        layout.addStretch()

    def _connect_signals(self):
        # 【变更】为所有带参数的内置信号添加lambda适配器
        self.btn_today.clicked.connect(lambda: self._set_date_for_shortcut("today"))
        self.btn_yesterday.clicked.connect(lambda: self._set_date_for_shortcut("yesterday"))
        self.btn_last_7_days.clicked.connect(lambda: self._set_date_for_shortcut("last7days"))
        self.start_date_edit.dateChanged.connect(lambda: self.filter_changed.emit())
        self.end_date_edit.dateChanged.connect(lambda: self.filter_changed.emit())

    def _set_date_for_shortcut(self, period: str):
        """响应快捷按钮，设置日期并手动发射信号。"""
        today = QDate.currentDate()
        # 阻止在设置日期时，dateChanged信号自动触发filter_changed
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
        # 在快捷方式设置完日期后，手动、显式地发射一次信号
        self.filter_changed.emit()

    def get_date_range(self) -> tuple[str, str]:
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        return start_date, end_date

    @Slot(QDate, QDate)
    def set_date_range(self, start_date: QDate, end_date: QDate):
        """
        程序化地设置日期范围。
        此方法不应发射filter_changed信号，调用者负责后续操作。
        """
        self.start_date_edit.blockSignals(True)
        self.end_date_edit.blockSignals(True)
        self.start_date_edit.setDate(start_date)
        self.end_date_edit.setDate(end_date)
        self.start_date_edit.blockSignals(False)
        self.end_date_edit.blockSignals(False)