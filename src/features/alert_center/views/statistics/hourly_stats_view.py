# desktop_center/src/features/alert_center/views/statistics/hourly_stats_view.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QHeaderView, QTableWidgetItem, QAbstractItemView
from PySide6.QtCore import Signal, Slot, Qt, QEvent
from ...widgets.date_filter_widget import DateFilterWidget
from ...widgets.ip_filter_widget import IPFilterWidget

class HourlyStatsView(QWidget):
    query_requested = Signal()
    became_visible = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.installEventFilter(self)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        filter_layout = QHBoxLayout()
        self.date_filter = DateFilterWidget()
        self.ip_filter = IPFilterWidget()
        filter_layout.addWidget(self.date_filter)
        filter_layout.addWidget(self.ip_filter)
        layout.addLayout(filter_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["小时", "告警数量"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("QTableWidget::item:selected { background-color: #cce8ff; color: black; }")
        self.table.setSortingEnabled(True)
        # 【变更】设置表格的选中行为为SelectRows
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)
        
        self.date_filter.filter_changed.connect(self.query_requested.emit)
        self.ip_filter.filter_changed.connect(self.query_requested.emit)

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
            hour_item = QTableWidgetItem()
            hour_item.setData(Qt.ItemDataRole.DisplayRole, f"{record.get('hour', 0):02d}:00")
            self.table.setItem(row, 0, hour_item)
            count_item = QTableWidgetItem()
            count_item.setData(Qt.ItemDataRole.DisplayRole, record.get('count', 0))
            self.table.setItem(row, 1, count_item)
        self.table.setSortingEnabled(True)