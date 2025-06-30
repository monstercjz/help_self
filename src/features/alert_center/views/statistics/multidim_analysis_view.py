# desktop_center/src/features/alert_center/views/statistics/multidim_analysis_view.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QHeaderView, QTreeWidgetItem, QPushButton
from PySide6.QtCore import Signal, Slot, Qt, QEvent
from PySide6.QtGui import QFont, QColor
from ...widgets.date_filter_widget import DateFilterWidget
from ...widgets.ip_filter_widget import IPFilterWidget

class MultidimAnalysisView(QWidget):
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

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["分析维度", "告警数量"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.setSortingEnabled(True)
        self.tree.setStyleSheet("QTreeView::item:selected { background-color: #cce8ff; color: black; }")
        
        button_layout = QHBoxLayout()
        expand_button = QPushButton("展开全部")
        collapse_button = QPushButton("折叠全部")
        button_layout.addStretch()
        button_layout.addWidget(expand_button)
        button_layout.addWidget(collapse_button)
        
        layout.addWidget(self.tree)
        layout.addLayout(button_layout)
        
        self.date_filter.filter_changed.connect(self.query_requested.emit)
        self.ip_filter.filter_changed.connect(self.query_requested.emit)
        expand_button.clicked.connect(self.tree.expandAll)
        collapse_button.clicked.connect(self.tree.collapseAll)

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj is self and event.type() == QEvent.Type.Show:
            self.became_visible.emit()
        return super().eventFilter(obj, event)

    @Slot(dict)
    def update_tree(self, tree_data: dict):
        self.tree.setSortingEnabled(False)
        self.tree.clear()
        bold_font = QFont(); bold_font.setBold(True)
        hour_color = QColor("#003366"); severity_color = QColor("#8B4513")
        
        for hour, severities in tree_data.items():
            hour_total = sum(sum(types.values()) for types in severities.values())
            hour_item = QTreeWidgetItem(self.tree, [f"{hour:02d}:00 - {hour:02d}:59", str(hour_total)])
            hour_item.setFont(0, bold_font); hour_item.setFont(1, bold_font)
            hour_item.setForeground(0, hour_color); hour_item.setForeground(1, hour_color)
            for severity, types in severities.items():
                severity_total = sum(types.values())
                severity_item = QTreeWidgetItem(hour_item, [f"  - {severity}", str(severity_total)])
                severity_item.setForeground(0, severity_color)
                for type_name, count in types.items():
                    QTreeWidgetItem(severity_item, [f"    - {type_name}", str(count)])
        self.tree.setSortingEnabled(True)