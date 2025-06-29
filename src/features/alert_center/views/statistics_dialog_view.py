# src/features/alert_center/views/statistics_dialog_view.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTabWidget,
                               QWidget, QHBoxLayout, QDateEdit, QPushButton,
                               QTreeWidget, QTreeWidgetItem, QHeaderView,
                               QComboBox, QTableWidget, QTableWidgetItem)
from PySide6.QtCore import Qt, QDate, Signal, Slot
from PySide6.QtGui import QFont, QColor

ALL_IPS_OPTION = "【全部IP】"

class StatisticsDialogView(QDialog):
    """【视图】统计分析对话框，纯UI。"""
    query_requested = Signal(str, dict)
    ip_list_requested = Signal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("统计分析")
        self.setMinimumSize(800, 600)
        self.tab_loaded_flags = {}
        self._init_ui()
        self._connect_signals()
        
        self.tab_widget.currentChanged.emit(0)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.ip_activity_tab = self._create_ip_activity_tab()
        self.hourly_stats_tab = self._create_hourly_stats_tab()
        self.multidim_stats_tab = self._create_multidim_stats_tab()
        self.type_stats_tab = self._create_type_stats_tab()
        
        self.tab_widget.addTab(self.ip_activity_tab, "按IP活跃度")
        self.tab_widget.addTab(self.hourly_stats_tab, "按小时分析")
        self.tab_widget.addTab(self.multidim_stats_tab, "多维分析")
        self.tab_widget.addTab(self.type_stats_tab, "告警类型")

    def _connect_signals(self):
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # --- 连接各个Tab的查询按钮 ---
        self.ip_activity_query_button.clicked.connect(lambda: self._emit_query_request("ip_activity"))
        for btn, period in [(self.ip_activity_btn_today, "today"), (self.ip_activity_btn_yesterday, "yesterday"), (self.ip_activity_btn_last_7_days, "last7days")]:
            btn.clicked.connect(lambda p=period: self._set_date_and_query(self.ip_activity_start_date, self.ip_activity_end_date, "ip_activity", p))
            
        self.hourly_query_button.clicked.connect(lambda: self._emit_query_request("hourly"))
        for btn, period in [(self.hourly_btn_today, "today"), (self.hourly_btn_yesterday, "yesterday"), (self.hourly_btn_last_7_days, "last7days")]:
            btn.clicked.connect(lambda p=period: self._set_date_and_query(self.hourly_start_date, self.hourly_end_date, "hourly", p))
        self.hourly_ip_combo.currentIndexChanged.connect(lambda: self._emit_query_request("hourly"))
            
        self.multidim_query_button.clicked.connect(lambda: self._emit_query_request("multidim"))
        for btn, period in [(self.multidim_btn_today, "today"), (self.multidim_btn_yesterday, "yesterday"), (self.multidim_btn_last_7_days, "last7days")]:
            btn.clicked.connect(lambda p=period: self._set_date_and_query(self.multidim_start_date, self.multidim_end_date, "multidim", p))
        self.multidim_ip_combo.currentIndexChanged.connect(lambda: self._emit_query_request("multidim"))
        self.multidim_expand_button.clicked.connect(self.multidim_stats_tree.expandAll)
        self.multidim_collapse_button.clicked.connect(self.multidim_stats_tree.collapseAll)
            
        self.type_query_button.clicked.connect(lambda: self._emit_query_request("type"))
        for btn, period in [(self.type_btn_today, "today"), (self.type_btn_yesterday, "yesterday"), (self.type_btn_last_7_days, "last7days")]:
            btn.clicked.connect(lambda p=period: self._set_date_and_query(self.type_start_date, self.type_end_date, "type", p))

    def _create_date_filter_bar(self, start_date_edit: QDateEdit, end_date_edit: QDateEdit, today_btn: QPushButton, yesterday_btn: QPushButton, last7_btn: QPushButton):
        start_date_edit.setCalendarPopup(True)
        end_date_edit.setCalendarPopup(True)
        start_date_edit.setDate(QDate.currentDate().addDays(-7))
        end_date_edit.setDate(QDate.currentDate())
        
        shortcut_layout = QHBoxLayout()
        shortcut_layout.addWidget(QLabel("快捷:"))
        shortcut_layout.addWidget(today_btn)
        shortcut_layout.addWidget(yesterday_btn)
        shortcut_layout.addWidget(last7_btn)
        shortcut_layout.addStretch()

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("日期:"))
        filter_layout.addWidget(start_date_edit)
        filter_layout.addWidget(QLabel("到"))
        filter_layout.addWidget(end_date_edit)
        return shortcut_layout, filter_layout

    def _create_ip_activity_tab(self):
        tab = QWidget()
        tab.setObjectName("ip_activity_tab")
        layout = QVBoxLayout(tab)
        self.ip_activity_start_date, self.ip_activity_end_date = QDateEdit(), QDateEdit()
        self.ip_activity_btn_today, self.ip_activity_btn_yesterday, self.ip_activity_btn_last_7_days = QPushButton("今天"), QPushButton("昨天"), QPushButton("近7天")
        shortcut, filter_l = self._create_date_filter_bar(self.ip_activity_start_date, self.ip_activity_end_date, self.ip_activity_btn_today, self.ip_activity_btn_yesterday, self.ip_activity_btn_last_7_days)
        self.ip_activity_query_button = QPushButton("查询")
        filter_l.addWidget(self.ip_activity_query_button)
        filter_l.addStretch()
        layout.addLayout(shortcut)
        layout.addLayout(filter_l)
        self.ip_activity_table = QTableWidget(0, 2)
        self.ip_activity_table.setHorizontalHeaderLabels(["来源IP", "数量"])
        self.ip_activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.ip_activity_table)
        return tab

    def _create_hourly_stats_tab(self):
        tab = QWidget()
        tab.setObjectName("hourly_tab")
        layout = QVBoxLayout(tab)
        self.hourly_start_date, self.hourly_end_date = QDateEdit(), QDateEdit()
        self.hourly_btn_today, self.hourly_btn_yesterday, self.hourly_btn_last_7_days = QPushButton("今天"), QPushButton("昨天"), QPushButton("近7天")
        shortcut, filter_l = self._create_date_filter_bar(self.hourly_start_date, self.hourly_end_date, self.hourly_btn_today, self.hourly_btn_yesterday, self.hourly_btn_last_7_days)
        self.hourly_ip_combo = QComboBox(); self.hourly_ip_combo.setMinimumWidth(150)
        filter_l.insertWidget(1, self.hourly_ip_combo)
        filter_l.insertWidget(1, QLabel("IP:"))
        self.hourly_query_button = QPushButton("查询")
        filter_l.addWidget(self.hourly_query_button)
        filter_l.addStretch()
        layout.addLayout(shortcut)
        layout.addLayout(filter_l)
        self.hourly_stats_table = QTableWidget(0, 2)
        self.hourly_stats_table.setHorizontalHeaderLabels(["小时", "数量"])
        self.hourly_stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.hourly_stats_table)
        return tab

    def _create_multidim_stats_tab(self):
        tab = QWidget()
        tab.setObjectName("multidim_tab")
        layout = QVBoxLayout(tab)
        self.multidim_start_date, self.multidim_end_date = QDateEdit(), QDateEdit()
        self.multidim_btn_today, self.multidim_btn_yesterday, self.multidim_btn_last_7_days = QPushButton("今天"), QPushButton("昨天"), QPushButton("近7天")
        shortcut, filter_l = self._create_date_filter_bar(self.multidim_start_date, self.multidim_end_date, self.multidim_btn_today, self.multidim_btn_yesterday, self.multidim_btn_last_7_days)
        self.multidim_ip_combo = QComboBox(); self.multidim_ip_combo.setMinimumWidth(150)
        filter_l.insertWidget(1, self.multidim_ip_combo)
        filter_l.insertWidget(1, QLabel("IP:"))
        self.multidim_query_button = QPushButton("查询")
        filter_l.addWidget(self.multidim_query_button)
        filter_l.addStretch()
        self.multidim_expand_button = QPushButton("展开")
        self.multidim_collapse_button = QPushButton("折叠")
        filter_l.addWidget(self.multidim_expand_button)
        filter_l.addWidget(self.multidim_collapse_button)
        layout.addLayout(shortcut)
        layout.addLayout(filter_l)
        self.multidim_stats_tree = QTreeWidget()
        self.multidim_stats_tree.setHeaderLabels(["分析维度", "告警数量"])
        self.multidim_stats_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.multidim_stats_tree)
        return tab

    def _create_type_stats_tab(self):
        tab = QWidget()
        tab.setObjectName("type_tab")
        layout = QVBoxLayout(tab)
        self.type_start_date, self.type_end_date = QDateEdit(), QDateEdit()
        self.type_btn_today, self.type_btn_yesterday, self.type_btn_last_7_days = QPushButton("今天"), QPushButton("昨天"), QPushButton("近7天")
        shortcut, filter_l = self._create_date_filter_bar(self.type_start_date, self.type_end_date, self.type_btn_today, self.type_btn_yesterday, self.type_btn_last_7_days)
        self.type_query_button = QPushButton("查询")
        filter_l.addWidget(self.type_query_button)
        filter_l.addStretch()
        layout.addLayout(shortcut)
        layout.addLayout(filter_l)
        self.type_stats_table = QTableWidget(0, 2)
        self.type_stats_table.setHorizontalHeaderLabels(["告警类型", "数量"])
        self.type_stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.type_stats_table)
        return tab

    def _on_tab_changed(self, index: int):
        tab_name = self.tab_widget.widget(index).objectName().replace("_tab", "")
        if not self.tab_loaded_flags.get(tab_name):
            if tab_name in ["hourly", "multidim"]:
                self.ip_list_requested.emit(tab_name, self._get_date_params_for_tab(tab_name))
            self._emit_query_request(tab_name)
            self.tab_loaded_flags[tab_name] = True
        
    def _emit_query_request(self, tab_name: str):
        if not self.isVisible(): return
        params = self._get_date_params_for_tab(tab_name)
        if tab_name in ["hourly", "multidim"]:
            params["ip"] = getattr(self, f"{tab_name}_ip_combo").currentText()
        self.query_requested.emit(tab_name, params)
        
    def _get_date_params_for_tab(self, tab_name: str):
        start_date = getattr(self, f"{tab_name}_start_date").date().toString("yyyy-MM-dd")
        end_date = getattr(self, f"{tab_name}_end_date").date().toString("yyyy-MM-dd")
        return {"start_date": start_date, "end_date": end_date}

    def _set_date_and_query(self, start_edit, end_edit, tab_name, period):
        today = QDate.currentDate()
        if period == "today": start_edit.setDate(today); end_edit.setDate(today)
        elif period == "yesterday": start_edit.setDate(today.addDays(-1)); end_edit.setDate(today.addDays(-1))
        elif period == "last7days": start_edit.setDate(today.addDays(-6)); end_edit.setDate(today)
        self._emit_query_request(tab_name)

    @Slot(list)
    def update_ip_activity_tab(self, data):
        table = self.ip_activity_table
        table.setRowCount(0)
        for row, item in enumerate(data):
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(item['source_ip']))
            table.setItem(row, 1, QTableWidgetItem(str(item['count'])))

    @Slot(list)
    def update_hourly_stats_tab(self, data):
        table = self.hourly_stats_table
        table.setRowCount(0)
        for row, item in enumerate(data):
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(f"{item['hour']:02d}:00"))
            table.setItem(row, 1, QTableWidgetItem(str(item['count'])))

    @Slot(dict)
    def update_multidim_stats_tab(self, data):
        tree = self.multidim_stats_tree
        tree.clear()
        bold_font = QFont(); bold_font.setBold(True)
        hour_color = QColor("#003366")
        severity_color = QColor("#8B4513")
        for hour, severities in sorted(data.items()):
            hour_total = sum(sum(types.values()) for types in severities.values())
            hour_item = QTreeWidgetItem(tree, [f"{hour:02d}:00 - {hour:02d}:59", str(hour_total)])
            hour_item.setFont(0, bold_font)
            hour_item.setForeground(0, hour_color)
            for severity, types in sorted(severities.items()):
                severity_total = sum(types.values())
                severity_item = QTreeWidgetItem(hour_item, [f"  - {severity}", str(severity_total)])
                severity_item.setForeground(0, severity_color)
                for type_name, count in sorted(types.items()):
                    QTreeWidgetItem(severity_item, [f"    - {type_name}", str(count)])

    @Slot(list)
    def update_type_stats_tab(self, data):
        table = self.type_stats_table
        table.setRowCount(0)
        for row, item in enumerate(data):
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(item['type']))
            table.setItem(row, 1, QTableWidgetItem(str(item['count'])))
            
    @Slot(str, list)
    def populate_ip_combo(self, tab_name, ips):
        combo = getattr(self, f"{tab_name}_ip_combo")
        current_text = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(ALL_IPS_OPTION)
        combo.addItems(ips)
        if current_text in [ALL_IPS_OPTION] + ips:
            combo.setCurrentText(current_text)
        else:
            combo.setCurrentIndex(0)
        combo.blockSignals(False)