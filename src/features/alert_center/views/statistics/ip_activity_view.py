# desktop_center/src/features/alert_center/views/statistics/ip_activity_view.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QHeaderView, QTableWidgetItem
# 【变更】添加 Qt 的导入
from PySide6.QtCore import Signal, Slot, QEvent, Qt
from ...widgets.date_filter_widget import DateFilterWidget

class IPActivityView(QWidget):
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
        self.table.setHorizontalHeaderLabels(["来源IP", "告警数量"])
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
            self.table.setItem(row, 0, QTableWidgetItem(record.get('source_ip', 'N/A')))
            count_item = QTableWidgetItem()
            # 使用 setData 以确保数值排序正确
            count_item.setData(Qt.ItemDataRole.DisplayRole, record.get('count', 0))
            self.table.setItem(row, 1, count_item)
        self.table.setSortingEnabled(True)