# desktop_center/src/ui/statistics_dialog.py
import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTabWidget,
                               QWidget, QHBoxLayout, QDateEdit, QPushButton,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QLineEdit, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, QDate, QCoreApplication
from PySide6.QtGui import QColor
from src.services.database_service import DatabaseService
from src.services.config_service import ConfigService
from typing import List, Dict, Any # 确保导入了List, Dict, Any

class StatisticsDialog(QDialog):
    """
    一个独立的对话框，用于统计和分析告警数据。
    包含多个选项卡，每个选项卡提供不同的统计视图。
    """
    def __init__(self, db_service: DatabaseService, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.db_service = db_service
        self.config_service = config_service
        self.setWindowTitle("统计分析")
        self.setMinimumSize(800, 600)
        
        self._init_ui()
        self._load_initial_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # --- 1. 告警类型排行榜选项卡 ---
        self.type_stats_tab = QWidget()
        self.type_stats_tab_layout = QVBoxLayout(self.type_stats_tab)
        self.tab_widget.addTab(self.type_stats_tab, "告警类型排行榜")
        self._setup_type_stats_tab()

        # --- 2. 全局按小时分析选项卡 ---
        self.hour_stats_tab = QWidget()
        self.hour_stats_tab_layout = QVBoxLayout(self.hour_stats_tab)
        self.tab_widget.addTab(self.hour_stats_tab, "全局按小时分析")
        self._setup_hour_stats_tab()

        # --- 3. 按IP活跃度排行榜选项卡 ---
        self.ip_activity_tab = QWidget()
        self.ip_activity_tab_layout = QVBoxLayout(self.ip_activity_tab)
        self.tab_widget.addTab(self.ip_activity_tab, "按IP活跃度排行榜")
        self._setup_ip_activity_tab()

        # --- 4. 按IP按小时统计选项卡 ---
        self.ip_hour_stats_tab = QWidget()
        self.ip_hour_stats_tab_layout = QVBoxLayout(self.ip_hour_stats_tab)
        self.tab_widget.addTab(self.ip_hour_stats_tab, "按IP按小时统计")
        self._setup_ip_hour_stats_tab()

    def _setup_type_stats_tab(self):
        """设置告警类型排行榜选项卡的UI。"""
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("日期范围:"))
        self.type_start_date = QDateEdit(calendarPopup=True)
        self.type_start_date.setDate(QDate.currentDate().addDays(-7))
        self.type_start_date.setMinimumWidth(100)
        filter_layout.addWidget(self.type_start_date)
        filter_layout.addWidget(QLabel("到"))
        self.type_end_date = QDateEdit(calendarPopup=True)
        self.type_end_date.setDate(QDate.currentDate())
        self.type_end_date.setMinimumWidth(100)
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

        self.type_query_button.clicked.connect(self._perform_type_stats_query)

    # 【核心修改】全局按小时分析，支持日期范围
    def _setup_hour_stats_tab(self):
        """设置全局按小时分析选项卡的UI。"""
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("日期范围:"))
        self.hour_start_date = QDateEdit(calendarPopup=True)
        self.hour_start_date.setDate(QDate.currentDate().addDays(-7)) # 默认最近7天
        self.hour_start_date.setMinimumWidth(100)
        filter_layout.addWidget(self.hour_start_date)
        filter_layout.addWidget(QLabel("到"))
        self.hour_end_date = QDateEdit(calendarPopup=True)
        self.hour_end_date.setDate(QDate.currentDate())
        self.hour_end_date.setMinimumWidth(100)
        filter_layout.addWidget(self.hour_end_date)
        
        self.hour_query_button = QPushButton("查询")
        self.hour_query_button.setStyleSheet("background-color: #0078d4; color: white; border-radius: 4px; padding: 4px 10px;")
        filter_layout.addWidget(self.hour_query_button)
        filter_layout.addStretch()
        self.hour_stats_tab_layout.addLayout(filter_layout)

        self.hour_stats_table = QTableWidget()
        self.hour_stats_table.setColumnCount(2)
        self.hour_stats_table.setHorizontalHeaderLabels(["小时", "数量"])
        self.hour_stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.hour_stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.hour_stats_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.hour_stats_tab_layout.addWidget(self.hour_stats_table)

        self.hour_query_button.clicked.connect(self._perform_hour_stats_query)
        
    # 【核心修改】按IP活跃度排行榜，支持日期范围
    def _setup_ip_activity_tab(self):
        """设置按IP活跃度排行榜选项卡的UI。"""
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("日期范围:"))
        self.ip_activity_start_date = QDateEdit(calendarPopup=True)
        self.ip_activity_start_date.setDate(QDate.currentDate().addDays(-7))
        self.ip_activity_start_date.setMinimumWidth(100)
        filter_layout.addWidget(self.ip_activity_start_date)
        filter_layout.addWidget(QLabel("到"))
        self.ip_activity_end_date = QDateEdit(calendarPopup=True)
        self.ip_activity_end_date.setDate(QDate.currentDate())
        self.ip_activity_end_date.setMinimumWidth(100)
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

        self.ip_activity_query_button.clicked.connect(self._perform_ip_activity_query)

    # 【核心修改】按IP按小时统计，支持日期范围
    def _setup_ip_hour_stats_tab(self):
        """设置按IP按小时统计选项卡的UI。"""
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("IP地址:"))
        self.ip_hour_ip_edit = QLineEdit()
        self.ip_hour_ip_edit.setPlaceholderText("例如: 192.168.1.1")
        self.ip_hour_ip_edit.setMinimumWidth(120)
        filter_layout.addWidget(self.ip_hour_ip_edit)

        filter_layout.addWidget(QLabel("日期范围:")) # 更改为日期范围
        self.ip_hour_start_date = QDateEdit(calendarPopup=True)
        self.ip_hour_start_date.setDate(QDate.currentDate())
        self.ip_hour_start_date.setMinimumWidth(100)
        filter_layout.addWidget(self.ip_hour_start_date)
        filter_layout.addWidget(QLabel("到"))
        self.ip_hour_end_date = QDateEdit(calendarPopup=True)
        self.ip_hour_end_date.setDate(QDate.currentDate())
        self.ip_hour_end_date.setMinimumWidth(100)
        filter_layout.addWidget(self.ip_hour_end_date)
        
        self.ip_hour_query_button = QPushButton("查询")
        self.ip_hour_query_button.setStyleSheet("background-color: #0078d4; color: white; border-radius: 4px; padding: 4px 10px;")
        filter_layout.addWidget(self.ip_hour_query_button)
        filter_layout.addStretch()
        self.ip_hour_stats_tab_layout.addLayout(filter_layout)

        self.ip_hour_stats_table = QTableWidget()
        self.ip_hour_stats_table.setColumnCount(2)
        self.ip_hour_stats_table.setHorizontalHeaderLabels(["小时", "数量"])
        self.ip_hour_stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ip_hour_stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.ip_hour_stats_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ip_hour_stats_tab_layout.addWidget(self.ip_hour_stats_table)

        self.ip_hour_query_button.clicked.connect(self._perform_ip_hour_stats_query)


    def _load_initial_data(self):
        """对话框首次打开时加载初始数据。"""
        self._perform_type_stats_query()
        self._perform_hour_stats_query()
        self._perform_ip_activity_query()
        self._perform_ip_hour_stats_query() # 尝试加载IP按小时，如果IP为空，会返回空

    def _perform_type_stats_query(self):
        """执行告警类型统计查询。"""
        start_date = self.type_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.type_end_date.date().toString(Qt.DateFormat.ISODate)
        
        QCoreApplication.processEvents()
        logging.info(f"正在查询告警类型排行榜 (日期: {start_date} - {end_date})...")

        results = self.db_service.get_stats_by_type(start_date, end_date)
        
        self._update_stats_table(self.type_stats_table, results, ["type", "count"])
        logging.info(f"告警类型排行榜查询完成，共 {len(results)} 种类型。")

    # 【核心修改】执行全局按小时统计查询，现在支持日期范围
    def _perform_hour_stats_query(self):
        """执行全局按小时统计查询。"""
        start_date = self.hour_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.hour_end_date.date().toString(Qt.DateFormat.ISODate)
        
        QCoreApplication.processEvents()
        logging.info(f"正在查询 {start_date} 到 {end_date} 的全局按小时统计...")

        results = self.db_service.get_stats_by_hour(start_date, end_date)
        
        self._update_stats_table(self.hour_stats_table, results, ["hour", "count"])
        logging.info(f"按小时统计查询完成，共 {len(results)} 小时数据。")
        
    def _perform_ip_activity_query(self):
        """执行按IP活跃度统计查询。"""
        start_date = self.ip_activity_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.ip_activity_end_date.date().toString(Qt.DateFormat.ISODate)
        
        QCoreApplication.processEvents()
        logging.info(f"正在查询按IP活跃度排行榜 (日期: {start_date} - {end_date})...")

        results = self.db_service.get_stats_by_ip_activity(start_date, end_date)
        
        self._update_stats_table(self.ip_activity_table, results, ["source_ip", "count"])
        logging.info(f"按IP活跃度排行榜查询完成，共 {len(results)} 个活跃IP。")

    # 【核心修改】执行按IP按小时统计查询，现在支持日期范围
    def _perform_ip_hour_stats_query(self):
        """执行按IP按小时统计查询。"""
        ip_address = self.ip_hour_ip_edit.text().strip()
        start_date = self.ip_hour_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.ip_hour_end_date.date().toString(Qt.DateFormat.ISODate)

        if not ip_address:
            QCoreApplication.processEvents()
            self._update_stats_table(self.ip_hour_stats_table, [], ["小时", "数量"])
            logging.warning("IP按小时统计：IP地址为空，请填写IP地址。")
            return

        QCoreApplication.processEvents()
        logging.info(f"正在查询IP {ip_address} 在 {start_date} 到 {end_date} 的按小时统计...")

        results = self.db_service.get_stats_by_ip_and_hour(ip_address, start_date, end_date)
        
        self._update_stats_table(self.ip_hour_stats_table, results, ["hour", "count"])
        logging.info(f"IP按小时统计查询完成，共 {len(results)} 小时数据。")


    def _update_stats_table(self, table: QTableWidget, data: List[Dict[str, Any]], column_keys: List[str]):
        """通用方法：更新统计表格。"""
        table.setRowCount(0)
        if not data:
            return

        table.setColumnCount(len(column_keys))
        table.setHorizontalHeaderLabels([col.capitalize().replace('_', ' ') for col in column_keys])

        for row_idx, record in enumerate(data):
            table.insertRow(row_idx)
            for col_idx, key in enumerate(column_keys):
                item = QTableWidgetItem(str(record.get(key, 'N/A')))
                table.setItem(row_idx, col_idx, item)
        table.resizeColumnsToContents()