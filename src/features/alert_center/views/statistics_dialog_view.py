# desktop_center/src/features/alert_center/views/statistics_dialog_view.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTabWidget, QWidget, 
                               QHBoxLayout, QDateEdit, QPushButton, QTreeWidget, 
                               QTreeWidgetItem, QHeaderView, QComboBox, QTableWidget, 
                               QTableWidgetItem)
from PySide6.QtCore import Qt, QDate, QCoreApplication, Signal, Slot
from PySide6.QtGui import QColor, QFont

ALL_IPS_OPTION = "【全部IP】" # UI常量

class StatisticsDialogView(QDialog):
    """
    【视图】统计分析对话框。
    纯UI组件，负责展示数据和发送用户操作信号。
    """
    # --- Signals to Controller ---
    tab_changed = Signal(int)
    query_requested = Signal(str)
    hourly_ip_changed = Signal()
    multidim_ip_changed = Signal()
    hourly_sort_requested = Signal(int)
    date_shortcut_requested = Signal(str, str)


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("统计分析")
        self.setMinimumSize(800, 600)
        self._init_ui()
        self.tab_widget.currentChanged.connect(self.tab_changed.emit)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.ip_activity_tab_content = self._create_ip_activity_table()
        self.hourly_stats_tab_content = self._create_hourly_stats_table()
        self.multidim_stats_tab_content = self._create_multidim_stats_tree()
        self.type_stats_tab_content = self._create_type_stats_table()

        self.ip_activity_tab = self._setup_tab("ip_activity_tab", self.ip_activity_tab_content)
        self.hourly_stats_tab = self._setup_tab("hourly_stats_tab", self.hourly_stats_tab_content, has_ip_combo=True)
        self.multidim_stats_tab = self._setup_tab("multidim_stats_tab", self.multidim_stats_tab_content, has_ip_combo=True, has_expand_buttons=True)
        self.type_stats_tab = self._setup_tab("type_stats_tab", self.type_stats_tab_content)

        self.tab_widget.addTab(self.ip_activity_tab, "按IP活跃度排行榜")
        self.tab_widget.addTab(self.hourly_stats_tab, "按小时分析")
        self.tab_widget.addTab(self.multidim_stats_tab, "多维分析")
        self.tab_widget.addTab(self.type_stats_tab, "告警类型排行榜")

    def _setup_tab(self, name: str, content_widget: QWidget, has_ip_combo=False, has_expand_buttons=False) -> QWidget:
        tab = QWidget()
        tab.setObjectName(name)
        layout = QVBoxLayout(tab)
        
        date_shortcut_layout = QHBoxLayout()
        date_shortcut_layout.addWidget(QLabel("快捷日期:"))
        btn_today = QPushButton("今天")
        btn_yesterday = QPushButton("昨天")
        btn_last_7_days = QPushButton("近7天")
        date_shortcut_layout.addWidget(btn_today)
        date_shortcut_layout.addWidget(btn_yesterday)
        date_shortcut_layout.addWidget(btn_last_7_days)
        date_shortcut_layout.addStretch()
        
        btn_today.clicked.connect(lambda: self.date_shortcut_requested.emit(name, "today"))
        btn_yesterday.clicked.connect(lambda: self.date_shortcut_requested.emit(name, "yesterday"))
        btn_last_7_days.clicked.connect(lambda: self.date_shortcut_requested.emit(name, "last7days"))

        layout.addLayout(date_shortcut_layout)
        
        filter_layout = QHBoxLayout()
        if has_ip_combo:
            filter_layout.addWidget(QLabel("IP地址:"))
            combo = QComboBox()
            combo.setEditable(True)
            combo.setPlaceholderText("请选择或输入IP地址")
            combo.setMinimumWidth(150)
            filter_layout.addWidget(combo)
            setattr(self, f"{name}_ip_combo", combo)
            if name == "hourly_stats_tab":
                combo.currentIndexChanged.connect(lambda: self.hourly_ip_changed.emit())
            elif name == "multidim_stats_tab":
                combo.currentIndexChanged.connect(lambda: self.multidim_ip_changed.emit())

        filter_layout.addWidget(QLabel("日期范围:"))
        start_date = QDateEdit(calendarPopup=True)
        start_date.setDate(QDate.currentDate().addDays(-7))
        filter_layout.addWidget(start_date)
        setattr(self, f"{name}_start_date", start_date)

        filter_layout.addWidget(QLabel("到"))
        end_date = QDateEdit(calendarPopup=True)
        end_date.setDate(QDate.currentDate())
        filter_layout.addWidget(end_date)
        setattr(self, f"{name}_end_date", end_date)

        query_button = QPushButton("查询")
        query_button.clicked.connect(lambda: self.query_requested.emit(name))
        filter_layout.addWidget(query_button)

        if has_expand_buttons:
            filter_layout.addStretch()
            expand_button = QPushButton("展开全部")
            collapse_button = QPushButton("折叠全部")
            expand_button.clicked.connect(content_widget.expandAll)
            collapse_button.clicked.connect(content_widget.collapseAll)
            filter_layout.addWidget(expand_button)
            filter_layout.addWidget(collapse_button)
        else:
             filter_layout.addStretch()

        layout.addLayout(filter_layout)
        layout.addWidget(content_widget)
        return tab

    def _create_ip_activity_table(self):
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["来源IP", "数量"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # 【新增】统一选中项样式
        table.setStyleSheet("QTableWidget::item:selected { background-color: #cce8ff; color: black; }")
        return table

    def _create_hourly_stats_table(self):
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["小时", "数量"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header = table.horizontalHeader()
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.hourly_sort_requested.emit)
        # 【新增】统一选中项样式
        table.setStyleSheet("QTableWidget::item:selected { background-color: #cce8ff; color: black; }")
        return table

    def _create_multidim_stats_tree(self):
        tree = QTreeWidget()
        tree.setColumnCount(2)
        tree.setHeaderLabels(["分析维度", "告警数量"])
        tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tree.setSortingEnabled(True)
        tree.setStyleSheet("QTreeView::item:selected { background-color: #cce8ff; color: black; }")
        return tree

    def _create_type_stats_table(self):
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["告警类型", "数量"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # 【新增】统一选中项样式
        table.setStyleSheet("QTableWidget::item:selected { background-color: #cce8ff; color: black; }")
        return table

    @Slot(list)
    def update_ip_activity_table(self, data: list):
        self._update_simple_table(self.ip_activity_tab_content, data, ["source_ip", "count"])

    @Slot(list)
    def update_hourly_stats_table(self, data: list):
        self._update_simple_table(self.hourly_stats_tab_content, data, ["hour", "count"])

    @Slot(list)
    def update_type_stats_table(self, data: list):
        self._update_simple_table(self.type_stats_tab_content, data, ["type", "count"])

    def _update_simple_table(self, table: QTableWidget, data: list, keys: list):
        table.setRowCount(0)
        table.setSortingEnabled(False)
        for row_idx, record in enumerate(data):
            table.insertRow(row_idx)
            for col_idx, key in enumerate(keys):
                item = QTableWidgetItem(str(record.get(key, 'N/A')))
                if isinstance(record.get(key), (int, float)):
                     item.setData(Qt.ItemDataRole.UserRole, record.get(key))
                table.setItem(row_idx, col_idx, item)
        table.setSortingEnabled(True) 
        table.resizeColumnsToContents()

    @Slot(dict)
    def populate_multidim_tree(self, tree_data: dict):
        tree: QTreeWidget = self.multidim_stats_tab_content
        tree.clear()
        tree.setSortingEnabled(False)
        bold_font = QFont()
        bold_font.setBold(True)
        hour_color = QColor("#003366")
        severity_color = QColor("#8B4513")
        
        for hour, severities in tree_data.items():
            hour_total = sum(sum(types.values()) for types in severities.values())
            hour_item = QTreeWidgetItem(tree, [f"{hour:02d}:00 - {hour:02d}:59", str(hour_total)])
            hour_item.setFont(0, bold_font)
            hour_item.setFont(1, bold_font)
            hour_item.setForeground(0, hour_color)
            hour_item.setForeground(1, hour_color)
            for severity, types in severities.items():
                severity_total = sum(types.values())
                severity_item = QTreeWidgetItem(hour_item, [f"  - {severity}", str(severity_total)])
                severity_item.setForeground(0, severity_color)
                for type_name, count in types.items():
                    QTreeWidgetItem(severity_item, [f"    - {type_name}", str(count)])
        tree.setSortingEnabled(True)

    @Slot(list)
    def update_ip_combo_box(self, combo: QComboBox, ip_list: list):
        current_text = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(ALL_IPS_OPTION)
        if ip_list:
            combo.addItems(ip_list)
        if current_text in [ALL_IPS_OPTION] + ip_list:
            combo.setCurrentText(current_text)
        elif current_text: 
            combo.setEditText(current_text)
        else:
            combo.setCurrentIndex(0)
        combo.blockSignals(False)
            
    def get_filter_parameters(self, name: str) -> dict:
        start_date_edit = getattr(self, f"{name}_start_date")
        end_date_edit = getattr(self, f"{name}_end_date")
        params = {
            "start_date": start_date_edit.date().toString(Qt.DateFormat.ISODate),
            "end_date": end_date_edit.date().toString(Qt.DateFormat.ISODate),
        }
        if hasattr(self, f"{name}_ip_combo"):
            combo = getattr(self, f"{name}_ip_combo")
            ip_address = combo.currentText().strip()
            params["ip_address"] = None if ip_address == ALL_IPS_OPTION or not ip_address else ip_address
        return params

    @Slot(int, str)
    def update_hourly_sort_indicator(self, column_index: int, direction: str):
        """[SLOT] 更新小时分析表格的排序指示器。"""
        header = self.hourly_stats_tab_content.horizontalHeader()
        sort_order = Qt.SortOrder.AscendingOrder if direction == 'ASC' else Qt.SortOrder.DescendingOrder
        header.setSortIndicator(column_index, sort_order)