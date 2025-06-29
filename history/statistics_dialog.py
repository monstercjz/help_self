# desktop_center/src/ui/statistics_dialog.py
import logging
from collections import defaultdict
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTabWidget,
                               QWidget, QHBoxLayout, QDateEdit, QPushButton,
                               QTreeWidget, QTreeWidgetItem, QHeaderView,
                               QLineEdit, QSpacerItem, QSizePolicy,
                               QComboBox, QTableWidget, QTableWidgetItem)
from PySide6.QtCore import Qt, QDate, QCoreApplication, QTimer
from PySide6.QtGui import QColor, QFont
from src.services.database_service import DatabaseService
from src.services.config_service import ConfigService
from typing import List, Dict, Any

# 定义一个常量，用于表示IP选择器中的“全部IP”选项
ALL_IPS_OPTION = "【全部IP】"

class StatisticsDialog(QDialog):
    """
    一个独立的对话框，用于统计和分析告警数据。
    “按小时分析”使用树状视图提供多级钻取分析。
    """
    def __init__(self, db_service: DatabaseService, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.db_service = db_service
        self.config_service = config_service
        self.setWindowTitle("统计分析")
        self.setMinimumSize(800, 600)
        
        # 用于惰性加载的标志
        self.tab_loaded_flags = {
            "ip_activity_tab": False,
            "hourly_stats_tab": False,
            "type_stats_tab": False
        }

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # --- 1. 按IP活跃度排行榜选项卡 ---
        self.ip_activity_tab = QWidget()
        self.ip_activity_tab.setObjectName("ip_activity_tab")
        self.ip_activity_tab_layout = QVBoxLayout(self.ip_activity_tab)
        self.tab_widget.addTab(self.ip_activity_tab, "按IP活跃度排行榜")
        self._setup_ip_activity_tab()

        # --- 2. 按小时分析选项卡 (使用树状视图) ---
        self.hourly_stats_tab = QWidget()
        self.hourly_stats_tab.setObjectName("hourly_stats_tab")
        self.hourly_stats_tab_layout = QVBoxLayout(self.hourly_stats_tab)
        self.tab_widget.addTab(self.hourly_stats_tab, "按小时分析")
        self._setup_hourly_stats_tab()

        # --- 3. 告警类型排行榜选项卡 ---
        self.type_stats_tab = QWidget()
        self.type_stats_tab.setObjectName("type_stats_tab")
        self.type_stats_tab_layout = QVBoxLayout(self.type_stats_tab)
        self.tab_widget.addTab(self.type_stats_tab, "告警类型排行榜")
        self._setup_type_stats_tab()
        
    def _connect_signals(self):
        """连接所有UI控件的信号到槽函数。"""
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # IP活跃度 Tab
        self.ip_activity_query_button.clicked.connect(self._perform_ip_activity_query)
        self.ip_activity_btn_today.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_activity_start_date, self.ip_activity_end_date, "today"))
        self.ip_activity_btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_activity_start_date, self.ip_activity_end_date, "yesterday"))
        self.ip_activity_btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_activity_start_date, self.ip_activity_end_date, "last7days"))

        # 按小时分析 Tab
        self.hourly_query_button.clicked.connect(self._perform_hourly_stats_query)
        self.hourly_btn_today.clicked.connect(lambda: self._set_date_range_shortcut(self.hourly_start_date, self.hourly_end_date, "today"))
        self.hourly_btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut(self.hourly_start_date, self.hourly_end_date, "yesterday"))
        self.hourly_btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut(self.hourly_start_date, self.hourly_end_date, "last7days"))
        self.hourly_ip_combo.currentIndexChanged.connect(self._on_ip_combo_changed)

        # 告警类型 Tab
        self.type_query_button.clicked.connect(self._perform_type_stats_query)
        self.type_btn_today.clicked.connect(lambda: self._set_date_range_shortcut(self.type_start_date, self.type_end_date, "today"))
        self.type_btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut(self.type_start_date, self.type_end_date, "yesterday"))
        self.type_btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut(self.type_start_date, self.type_end_date, "last7days"))
        
        QTimer.singleShot(0, lambda: self._on_tab_changed(self.tab_widget.currentIndex()))

    def _set_date_range_shortcut(self, start_date_edit: QDateEdit, end_date_edit: QDateEdit, period: str):
        today = QDate.currentDate()
        if period == "today":
            start_date_edit.setDate(today)
            end_date_edit.setDate(today)
        elif period == "yesterday":
            yesterday = today.addDays(-1)
            start_date_edit.setDate(yesterday)
            end_date_edit.setDate(yesterday)
        elif period == "last7days":
            start_date_edit.setDate(today.addDays(-6))
            end_date_edit.setDate(today)

        if start_date_edit is self.ip_activity_start_date:
            self._perform_ip_activity_query()
        elif start_date_edit is self.hourly_start_date:
            self._perform_hourly_stats_query()
        elif start_date_edit is self.type_start_date:
            self._perform_type_stats_query()

    # --- UI 设置方法 ---

    def _setup_ip_activity_tab(self):
        date_shortcut_layout = QHBoxLayout()
        date_shortcut_layout.addWidget(QLabel("快捷日期:"))
        self.ip_activity_btn_today = QPushButton("今天")
        self.ip_activity_btn_yesterday = QPushButton("昨天")
        self.ip_activity_btn_last_7_days = QPushButton("近7天")
        date_shortcut_layout.addWidget(self.ip_activity_btn_today)
        date_shortcut_layout.addWidget(self.ip_activity_btn_yesterday)
        date_shortcut_layout.addWidget(self.ip_activity_btn_last_7_days)
        date_shortcut_layout.addStretch()
        self.ip_activity_tab_layout.addLayout(date_shortcut_layout)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("日期范围:"))
        self.ip_activity_start_date = QDateEdit(calendarPopup=True)
        self.ip_activity_start_date.setDate(QDate.currentDate().addDays(-7))
        filter_layout.addWidget(self.ip_activity_start_date)
        filter_layout.addWidget(QLabel("到"))
        self.ip_activity_end_date = QDateEdit(calendarPopup=True)
        self.ip_activity_end_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.ip_activity_end_date)
        self.ip_activity_query_button = QPushButton("查询")
        self.ip_activity_query_button.setStyleSheet("background-color: #0078d4; color: white; border-radius: 4px; padding: 4px 10px;")
        filter_layout.addWidget(self.ip_activity_query_button)
        filter_layout.addStretch()
        self.ip_activity_tab_layout.addLayout(filter_layout)

        self.ip_activity_table = QTableWidget()
        self.ip_activity_table.setColumnCount(2)
        self.ip_activity_table.setHorizontalHeaderLabels(["来源IP", "数量"])
        self.ip_activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ip_activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.ip_activity_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ip_activity_tab_layout.addWidget(self.ip_activity_table)

    def _setup_hourly_stats_tab(self):
        date_shortcut_layout = QHBoxLayout()
        date_shortcut_layout.addWidget(QLabel("快捷日期:"))
        self.hourly_btn_today = QPushButton("今天")
        self.hourly_btn_yesterday = QPushButton("昨天")
        self.hourly_btn_last_7_days = QPushButton("近7天")
        date_shortcut_layout.addWidget(self.hourly_btn_today)
        date_shortcut_layout.addWidget(self.hourly_btn_yesterday)
        date_shortcut_layout.addWidget(self.hourly_btn_last_7_days)
        date_shortcut_layout.addStretch()
        self.hourly_stats_tab_layout.addLayout(date_shortcut_layout)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("IP地址:"))
        self.hourly_ip_combo = QComboBox()
        self.hourly_ip_combo.setEditable(True)
        self.hourly_ip_combo.setPlaceholderText("请选择或输入IP地址")
        self.hourly_ip_combo.setMinimumWidth(150)
        filter_layout.addWidget(self.hourly_ip_combo)
        filter_layout.addWidget(QLabel("日期范围:"))
        self.hourly_start_date = QDateEdit(calendarPopup=True)
        self.hourly_start_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.hourly_start_date)
        filter_layout.addWidget(QLabel("到"))
        self.hourly_end_date = QDateEdit(calendarPopup=True)
        self.hourly_end_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.hourly_end_date)
        self.hourly_query_button = QPushButton("查询")
        self.hourly_query_button.setStyleSheet("background-color: #0078d4; color: white; border-radius: 4px; padding: 4px 10px;")
        filter_layout.addWidget(self.hourly_query_button)
        filter_layout.addStretch()
        self.hourly_stats_tab_layout.addLayout(filter_layout)

        self.hourly_stats_tree = QTreeWidget()
        self.hourly_stats_tree.setColumnCount(2)
        self.hourly_stats_tree.setHeaderLabels(["分析维度", "告警数量"])
        self.hourly_stats_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.hourly_stats_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.hourly_stats_tree.setSortingEnabled(True)
        self.hourly_stats_tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.hourly_stats_tab_layout.addWidget(self.hourly_stats_tree)

    def _setup_type_stats_tab(self):
        date_shortcut_layout = QHBoxLayout()
        date_shortcut_layout.addWidget(QLabel("快捷日期:"))
        self.type_btn_today = QPushButton("今天")
        self.type_btn_yesterday = QPushButton("昨天")
        self.type_btn_last_7_days = QPushButton("近7天")
        date_shortcut_layout.addWidget(self.type_btn_today)
        date_shortcut_layout.addWidget(self.type_btn_yesterday)
        date_shortcut_layout.addWidget(self.type_btn_last_7_days)
        date_shortcut_layout.addStretch()
        self.type_stats_tab_layout.addLayout(date_shortcut_layout)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("日期范围:"))
        self.type_start_date = QDateEdit(calendarPopup=True)
        self.type_start_date.setDate(QDate.currentDate().addDays(-7))
        filter_layout.addWidget(self.type_start_date)
        filter_layout.addWidget(QLabel("到"))
        self.type_end_date = QDateEdit(calendarPopup=True)
        self.type_end_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.type_end_date)
        self.type_query_button = QPushButton("查询")
        self.type_query_button.setStyleSheet("background-color: #0078d4; color: white; border-radius: 4px; padding: 4px 10px;")
        filter_layout.addWidget(self.type_query_button)
        filter_layout.addStretch()
        self.type_stats_tab_layout.addLayout(filter_layout)

        self.type_stats_table = QTableWidget()
        self.type_stats_table.setColumnCount(2)
        self.type_stats_table.setHorizontalHeaderLabels(["告警类型", "数量"])
        self.type_stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.type_stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.type_stats_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.type_stats_tab_layout.addWidget(self.type_stats_table)

    # --- 数据加载和查询方法 ---

    def _on_tab_changed(self, index: int):
        current_widget = self.tab_widget.widget(index)
        if not current_widget: return
        current_tab_name = current_widget.objectName()
        
        if not self.tab_loaded_flags.get(current_tab_name, False):
            logging.info(f"第一次加载选项卡: {current_tab_name}")
            if current_tab_name == "ip_activity_tab":
                self._perform_ip_activity_query()
            elif current_tab_name == "hourly_stats_tab":
                self._populate_ip_combo_box()
                self._perform_hourly_stats_query()
            elif current_tab_name == "type_stats_tab":
                self._perform_type_stats_query()
            self.tab_loaded_flags[current_tab_name] = True
        
        if current_tab_name == "hourly_stats_tab":
            self._populate_ip_combo_box()

    def _perform_ip_activity_query(self):
        start_date = self.ip_activity_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.ip_activity_end_date.date().toString(Qt.DateFormat.ISODate)
        self._set_loading_state(self.ip_activity_table, "来源IP", "数量")
        logging.info(f"正在查询按IP活跃度排行榜 (日期: {start_date} - {end_date})...")
        results = self.db_service.get_stats_by_ip_activity(start_date, end_date)
        self._update_stats_table(self.ip_activity_table, results, ["source_ip", "count"])
        logging.info(f"按IP活跃度排行榜查询完成，共 {len(results)} 个活跃IP。")

    def _perform_hourly_stats_query(self):
        ip_address = self.hourly_ip_combo.currentText().strip()
        start_date = self.hourly_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.hourly_end_date.date().toString(Qt.DateFormat.ISODate)

        self.hourly_stats_tree.clear()
        self.hourly_stats_tree.setHeaderLabels(["分析维度 (加载中...)", "告警数量"])
        QCoreApplication.processEvents()

        if not ip_address:
            logging.warning("按小时分析：IP地址为空，请选择或填写IP地址。")
            self.hourly_stats_tree.setHeaderLabels(["分析维度 (无数据)", "告警数量"])
            return
            
        query_ip = None if ip_address == ALL_IPS_OPTION else ip_address
        
        logging.info(f"正在查询详细按小时统计 (IP: {ip_address}, 日期: {start_date} - {end_date})...")
        results = self.db_service.get_detailed_hourly_stats(start_date, end_date, query_ip)
        
        self._populate_hourly_tree(results)
        self.hourly_stats_tree.setHeaderLabels(["分析维度", "告警数量"])
        logging.info(f"详细按小时统计查询完成。")

    def _perform_type_stats_query(self):
        start_date = self.type_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.type_end_date.date().toString(Qt.DateFormat.ISODate)
        self._set_loading_state(self.type_stats_table, "告警类型", "数量")
        logging.info(f"正在查询告警类型排行榜 (日期: {start_date} - {end_date})...")
        results = self.db_service.get_stats_by_type(start_date, end_date)
        self._update_stats_table(self.type_stats_table, results, ["type", "count"])
        logging.info(f"告警类型排行榜查询完成，共 {len(results)} 种类型。")

    # --- 辅助方法 ---
    
    def _populate_hourly_tree(self, data: List[Dict[str, Any]]):
        self.hourly_stats_tree.clear()
        if not data:
            return

        tree_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for row in data:
            tree_data[row['hour']][row['severity']][row['type']] = row['count']

        bold_font = QFont()
        bold_font.setBold(True)
        
        # 禁用排序以提高填充性能，填充完毕后重新启用
        self.hourly_stats_tree.setSortingEnabled(False)

        for hour, severities in sorted(tree_data.items()):
            hour_total = sum(sum(types.values()) for types in severities.values())
            hour_text = f"{hour:02d}:00 - {hour:02d}:59"
            
            hour_item = QTreeWidgetItem(self.hourly_stats_tree)
            hour_item.setFont(0, bold_font)
            hour_item.setFont(1, bold_font)
            hour_item.setText(0, hour_text)
            hour_item.setText(1, str(hour_total))
            # 为了让QTreeWidget能够按数字排序，我们将数字存储在UserRole中
            hour_item.setData(0, Qt.ItemDataRole.UserRole, hour)
            hour_item.setData(1, Qt.ItemDataRole.UserRole, hour_total)
            
            for severity, types in sorted(severities.items()):
                severity_total = sum(types.values())
                severity_item = QTreeWidgetItem(hour_item)
                severity_item.setText(0, f"  - {severity}")
                severity_item.setText(1, str(severity_total))
                severity_item.setData(1, Qt.ItemDataRole.UserRole, severity_total)
                
                for type_name, count in sorted(types.items()):
                    type_item = QTreeWidgetItem(severity_item)
                    type_item.setText(0, f"    - {type_name}")
                    type_item.setText(1, str(count))
                    type_item.setData(1, Qt.ItemDataRole.UserRole, count)
        
        self.hourly_stats_tree.expandAll()
        self.hourly_stats_tree.setSortingEnabled(True)

    def _populate_ip_combo_box(self):
        start_date = self.hourly_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.hourly_end_date.date().toString(Qt.DateFormat.ISODate)
        distinct_ips = self.db_service.get_distinct_source_ips(start_date, end_date)
        
        current_text = self.hourly_ip_combo.currentText()
        
        self.hourly_ip_combo.clear()
        self.hourly_ip_combo.addItem(ALL_IPS_OPTION)
        
        if distinct_ips:
            self.hourly_ip_combo.addItems(distinct_ips)
            logging.info(f"IP地址下拉框已更新，共 {len(distinct_ips)} 个不重复IP。")
        
        if current_text in [ALL_IPS_OPTION] + distinct_ips:
            self.hourly_ip_combo.setCurrentText(current_text)
        elif current_text:
            self.hourly_ip_combo.setEditText(current_text)
        else:
            self.hourly_ip_combo.setCurrentIndex(0)

    def _on_ip_combo_changed(self, index: int):
        if self.tab_loaded_flags.get("hourly_stats_tab", False):
            self._perform_hourly_stats_query()

    def _set_loading_state(self, table: QTableWidget, col1_text: str, col2_text: str):
        table.setRowCount(0)
        table.setHorizontalHeaderLabels([col1_text, f"{col2_text} (加载中...)"])
        QCoreApplication.processEvents()

    def _update_stats_table(self, table: QTableWidget, data: List[Dict[str, Any]], column_keys: List[str]):
        table.setRowCount(0)
        col1_text = column_keys[0].capitalize().replace('_', ' ')
        col2_text = column_keys[1].capitalize().replace('_', ' ')
        if not data:
            table.setHorizontalHeaderLabels([f"{col1_text} (无数据)", col2_text])
            return
        table.setHorizontalHeaderLabels([col1_text, col2_text])
        table.setColumnCount(len(column_keys))
        for row_idx, record in enumerate(data):
            table.insertRow(row_idx)
            for col_idx, key in enumerate(column_keys):
                item = QTableWidgetItem(str(record.get(key, 'N/A')))
                table.setItem(row_idx, col_idx, item)
        table.resizeColumnsToContents()