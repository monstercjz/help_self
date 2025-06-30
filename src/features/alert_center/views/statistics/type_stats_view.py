# desktop_center/src/features/alert_center/views/statistics/type_stats_view.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QHeaderView, QTableWidgetItem
from PySide6.QtCore import Signal, Slot, Qt, QEvent
from ...widgets.date_filter_widget import DateFilterWidget

class TypeStatsView(QWidget):
    query_requested = Signal()
    became_visible = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.installEventFilter(self)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.date_filter = DateFilterWidget()
        layout.addWidget(self.date_filter)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["告警类型", "告警数量"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("QTableWidget::item:selected { background-color: #cce8ff; color: black; }")
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)
        
        self.date_filter.filter_changed.connect(self.query_requested.emit)
        
    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj is self and event.type() == QEvent.Type.Show:
            self.became_visible.emit()
        return super().eventFilter(obj, event)

    @Slot(list)
    def update_table(self, data: list):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for row, record in enumerate(data):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(record.get('type', 'N/A')))
            count_item = QTableWidgetItem()
            count_item.setData(Qt.ItemDataRole.DisplayRole, record.get('count', 0))
            self.table.setItem(row, 1, count_item)
        self.table.setSortingEnabled(True)