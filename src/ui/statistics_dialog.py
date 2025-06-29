# desktop_center/src/ui/statistics_dialog.py
import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTabWidget,
                               QWidget, QHBoxLayout, QDateEdit, QPushButton,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QLineEdit, QSpacerItem, QSizePolicy,
                               QComboBox) # 【修改】新增QComboBox
from PySide6.QtCore import Qt, QDate, QCoreApplication, QTimer # 【修改】新增QTimer
from PySide6.QtGui import QColor # 【确保QColor已导入】
from src.services.database_service import DatabaseService
from src.services.config_service import ConfigService
from typing import List, Dict, Any

class StatisticsDialog(QDialog):
    """
    一个独立的对话框，用于统计和分析告警数据。
    包含多个选项卡，每个选项卡提供不同的统计视图。
    增加了日期快捷筛选、IP地址选择器和选项卡惰性加载功能。
    """
    def __init__(self, db_service: DatabaseService, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.db_service = db_service
        self.config_service = config_service
        self.setWindowTitle("统计分析")
        self.setMinimumSize(800, 600)
        
        # 【新增】用于惰性加载的标志
        self.tab_loaded_flags = {
            "type_stats_tab": False,
            "hour_stats_tab": False,
            "ip_activity_tab": False,
            "ip_hour_stats_tab": False
        }

        self._init_ui()
        self._connect_signals() # 连接信号放在初始化UI之后

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

    def _connect_signals(self):
        """连接所有UI控件的信号到槽函数。"""
        # 【新增】选项卡切换信号
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # 告警类型排行榜选项卡信号
        self.type_query_button.clicked.connect(self._perform_type_stats_query)
        self.type_btn_today.clicked.connect(lambda: self._set_date_range_shortcut(self.type_start_date, self.type_end_date, "today"))
        self.type_btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut(self.type_start_date, self.type_end_date, "yesterday"))
        self.type_btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut(self.type_start_date, self.type_end_date, "last7days"))
        
        # 全局按小时分析选项卡信号
        self.hour_query_button.clicked.connect(self._perform_hour_stats_query)
        self.hour_btn_today.clicked.connect(lambda: self._set_date_range_shortcut(self.hour_start_date, self.hour_end_date, "today"))
        self.hour_btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut(self.hour_start_date, self.hour_end_date, "yesterday"))
        self.hour_btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut(self.hour_start_date, self.hour_end_date, "last7days"))

        # 按IP活跃度排行榜选项卡信号
        self.ip_activity_query_button.clicked.connect(self._perform_ip_activity_query)
        self.ip_activity_btn_today.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_activity_start_date, self.ip_activity_end_date, "today"))
        self.ip_activity_btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_activity_start_date, self.ip_activity_end_date, "yesterday"))
        self.ip_activity_btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_activity_start_date, self.ip_activity_end_date, "last7days"))

        # 按IP按小时统计选项卡信号
        self.ip_hour_query_button.clicked.connect(self._perform_ip_hour_stats_query)
        self.ip_hour_btn_today.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_hour_start_date, self.ip_hour_end_date, "today"))
        self.ip_hour_btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_hour_start_date, self.ip_hour_end_date, "yesterday"))
        self.ip_hour_btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_hour_start_date, self.ip_hour_end_date, "last7days"))
        # 【新增】IP地址下拉框选中变化时触发查询（如果已加载）
        self.ip_hour_ip_combo.currentIndexChanged.connect(self._on_ip_combo_changed)


        # 初始加载第一个选项卡的数据
        self._on_tab_changed(self.tab_widget.currentIndex())

    # 【新增】日期范围快捷设置通用方法
    def _set_date_range_shortcut(self, start_date_edit: QDateEdit, end_date_edit: QDateEdit, period: str):
        """
        根据预设周期设置指定QDateEdit的日期范围。
        Args:
            start_date_edit (QDateEdit): 起始日期编辑框。
            end_date_edit (QDateEdit): 结束日期编辑框。
            period (str): 'today', 'yesterday', 'last7days'
        """
        today = QDate.currentDate()
        if period == "today":
            start_date_edit.setDate(today)
            end_date_edit.setDate(today)
        elif period == "yesterday":
            yesterday = today.addDays(-1)
            start_date_edit.setDate(yesterday)
            end_date_edit.setDate(yesterday)
        elif period == "last7days":
            start_date_edit.setDate(today.addDays(-6)) # 今天算在内
            end_date_edit.setDate(today)
        
        # 触发相应选项卡的查询（通过连接信号）
        if start_date_edit is self.type_start_date:
            self._perform_type_stats_query()
        elif start_date_edit is self.hour_start_date:
            self._perform_hour_stats_query()
        elif start_date_edit is self.ip_activity_start_date:
            self._perform_ip_activity_query()
        elif start_date_edit is self.ip_hour_start_date:
            self._perform_ip_hour_stats_query()


    def _setup_type_stats_tab(self):
        """设置告警类型排行榜选项卡的UI。"""
        # 【新增】日期筛选快捷按钮
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


    # 【核心修改】全局按小时分析，支持日期范围
    def _setup_hour_stats_tab(self):
        """设置全局按小时分析选项卡的UI。"""
        # 【新增】日期筛选快捷按钮
        date_shortcut_layout = QHBoxLayout()
        date_shortcut_layout.addWidget(QLabel("快捷日期:"))
        self.hour_btn_today = QPushButton("今天")
        self.hour_btn_yesterday = QPushButton("昨天")
        self.hour_btn_last_7_days = QPushButton("近7天")
        date_shortcut_layout.addWidget(self.hour_btn_today)
        date_shortcut_layout.addWidget(self.hour_btn_yesterday)
        date_shortcut_layout.addWidget(self.hour_btn_last_7_days)
        date_shortcut_layout.addStretch()
        self.hour_stats_tab_layout.addLayout(date_shortcut_layout)

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
        
    # 【核心修改】按IP活跃度排行榜，支持日期范围
    def _setup_ip_activity_tab(self):
        """设置按IP活跃度排行榜选项卡的UI。"""
        # 【新增】日期筛选快捷按钮
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


    # 【核心修改】按IP按小时统计，支持日期范围和IP选择器
    def _setup_ip_hour_stats_tab(self):
        """设置按IP按小时统计选项卡的UI。"""
        # 【新增】日期筛选快捷按钮
        date_shortcut_layout = QHBoxLayout()
        date_shortcut_layout.addWidget(QLabel("快捷日期:"))
        self.ip_hour_btn_today = QPushButton("今天")
        self.ip_hour_btn_yesterday = QPushButton("昨天")
        self.ip_hour_btn_last_7_days = QPushButton("近7天")
        date_shortcut_layout.addWidget(self.ip_hour_btn_today)
        date_shortcut_layout.addWidget(self.ip_hour_btn_yesterday)
        date_shortcut_layout.addWidget(self.ip_hour_btn_last_7_days)
        date_shortcut_layout.addStretch()
        self.ip_hour_stats_tab_layout.addLayout(date_shortcut_layout)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("IP地址:"))
        # 【修改】使用QComboBox替换QLineEdit，用于IP选择
        self.ip_hour_ip_combo = QComboBox()
        self.ip_hour_ip_combo.setEditable(True) # 允许用户手动输入或粘贴
        self.ip_hour_ip_combo.setPlaceholderText("请选择或输入IP地址")
        self.ip_hour_ip_combo.setMinimumWidth(150)
        filter_layout.addWidget(self.ip_hour_ip_combo)

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
        
    # 【新增】选项卡切换时的惰性加载
    def _on_tab_changed(self, index: int):
        """
        当选项卡切换时触发，根据选项卡索引加载数据，实现惰性加载。
        Args:
            index (int): 当前选中选项卡的索引。
        """
        current_tab_name = self.tab_widget.widget(index).objectName()
        if not self.tab_loaded_flags.get(current_tab_name, False):
            logging.info(f"第一次加载选项卡: {current_tab_name}")
            if current_tab_name == self.type_stats_tab.objectName():
                self._perform_type_stats_query()
            elif current_tab_name == self.hour_stats_tab.objectName():
                self._perform_hour_stats_query()
            elif current_tab_name == self.ip_activity_tab.objectName():
                self._perform_ip_activity_query()
            elif current_tab_name == self.ip_hour_stats_tab.objectName():
                # 对于IP按小时统计，需要先填充IP地址下拉框
                self._populate_ip_combo_box()
                self._perform_ip_hour_stats_query() # 首次加载时可能IP为空
            self.tab_loaded_flags[current_tab_name] = True
        
        # 即使不是第一次加载，如果当前是IP按小时统计，也需要确保IP列表是最新的
        if current_tab_name == self.ip_hour_stats_tab.objectName():
            self._populate_ip_combo_box()


    # 【修改】_load_initial_data 不再直接调用查询，而是依赖_on_tab_changed
    def _load_initial_data(self):
        """对话框首次打开时，此函数不直接加载所有数据，而是依赖 _on_tab_changed 实现惰性加载。"""
        # _on_tab_changed 会在连接信号后被自动调用，加载初始选中的Tab
        pass

    def _perform_type_stats_query(self):
        """执行告警类型统计查询。"""
        start_date = self.type_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.type_end_date.date().toString(Qt.DateFormat.ISODate)
        
        # 【新增】显示加载状态
        self.type_stats_table.setRowCount(0) # 清空旧数据
        self.type_stats_table.setHorizontalHeaderLabels(["告警类型", "数量 (加载中...)"])
        QCoreApplication.processEvents() # 确保UI更新

        logging.info(f"正在查询告警类型排行榜 (日期: {start_date} - {end_date})...")

        results = self.db_service.get_stats_by_type(start_date, end_date)
        
        self._update_stats_table(self.type_stats_table, results, ["type", "count"])
        self.type_stats_table.setHorizontalHeaderLabels(["告警类型", "数量"]) # 恢复表头
        logging.info(f"告警类型排行榜查询完成，共 {len(results)} 种类型。")

    # 【核心修改】执行全局按小时统计查询，现在支持日期范围
    def _perform_hour_stats_query(self):
        """执行全局按小时统计查询。"""
        start_date = self.hour_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.hour_end_date.date().toString(Qt.DateFormat.ISODate)
        
        # 【新增】显示加载状态
        self.hour_stats_table.setRowCount(0) # 清空旧数据
        self.hour_stats_table.setHorizontalHeaderLabels(["小时", "数量 (加载中...)"])
        QCoreApplication.processEvents()

        logging.info(f"正在查询 {start_date} 到 {end_date} 的全局按小时统计...")

        results = self.db_service.get_stats_by_hour(start_date, end_date)
        
        self._update_stats_table(self.hour_stats_table, results, ["hour", "count"])
        self.hour_stats_table.setHorizontalHeaderLabels(["小时", "数量"]) # 恢复表头
        logging.info(f"按小时统计查询完成，共 {len(results)} 小时数据。")
        
    def _perform_ip_activity_query(self):
        """执行按IP活跃度统计查询。"""
        start_date = self.ip_activity_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.ip_activity_end_date.date().toString(Qt.DateFormat.ISODate)
        
        # 【新增】显示加载状态
        self.ip_activity_table.setRowCount(0) # 清空旧数据
        self.ip_activity_table.setHorizontalHeaderLabels(["来源IP", "数量 (加载中...)"])
        QCoreApplication.processEvents()

        logging.info(f"正在查询按IP活跃度排行榜 (日期: {start_date} - {end_date})...")

        results = self.db_service.get_stats_by_ip_activity(start_date, end_date)
        
        self._update_stats_table(self.ip_activity_table, results, ["source_ip", "count"])
        self.ip_activity_table.setHorizontalHeaderLabels(["来源IP", "数量"]) # 恢复表头
        logging.info(f"按IP活跃度排行榜查询完成，共 {len(results)} 个活跃IP。")

    # 【核心修改】执行按IP按小时统计查询，现在支持日期范围
    def _perform_ip_hour_stats_query(self):
        """执行按IP按小时统计查询。"""
        # 【修改】从QComboBox获取IP地址
        ip_address = self.ip_hour_ip_combo.currentText().strip()
        start_date = self.ip_hour_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.ip_hour_end_date.date().toString(Qt.DateFormat.ISODate)

        # 【新增】显示加载状态
        self.ip_hour_stats_table.setRowCount(0) # 清空旧数据
        self.ip_hour_stats_table.setHorizontalHeaderLabels(["小时", "数量 (加载中...)"])
        QCoreApplication.processEvents()

        if not ip_address:
            # QMessageBox.information(self, "提示", "IP按小时统计：请选择或输入IP地址。") # 不弹窗，直接在日志和UI反馈
            self.ip_hour_stats_table.setHorizontalHeaderLabels(["小时", "数量"]) # 恢复表头
            logging.warning("IP按小时统计：IP地址为空，请选择或填写IP地址。")
            return

        logging.info(f"正在查询IP {ip_address} 在 {start_date} 到 {end_date} 的按小时统计...")

        results = self.db_service.get_stats_by_ip_and_hour(ip_address, start_date, end_date)
        
        self._update_stats_table(self.ip_hour_stats_table, results, ["hour", "count"])
        self.ip_hour_stats_table.setHorizontalHeaderLabels(["小时", "数量"]) # 恢复表头
        logging.info(f"IP按小时统计查询完成，共 {len(results)} 小时数据。")

    # 【新增】填充IP地址下拉框
    def _populate_ip_combo_box(self):
        """
        填充IP地址下拉框，包含数据库中所有不重复的来源IP。
        每次显示IP按小时统计Tab时更新，确保列表最新。
        """
        # 获取当前日期范围，用于筛选IP列表
        start_date = self.ip_hour_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.ip_hour_end_date.date().toString(Qt.DateFormat.ISODate)

        distinct_ips = self.db_service.get_distinct_source_ips(start_date, end_date)
        
        # 保存当前用户输入的IP，以便刷新后恢复
        current_text = self.ip_hour_ip_combo.currentText()
        
        self.ip_hour_ip_combo.clear()
        if distinct_ips:
            self.ip_hour_ip_combo.addItems(distinct_ips)
            logging.info(f"IP地址下拉框已更新，共 {len(distinct_ips)} 个不重复IP。")
            # 尝试恢复之前输入的IP，如果它仍在列表中
            if current_text in distinct_ips:
                self.ip_hour_ip_combo.setCurrentText(current_text)
            elif current_text: # 如果之前有输入但不在新列表中，也尝试恢复
                self.ip_hour_ip_combo.setEditText(current_text)
            else: # 否则默认选择第一个
                self.ip_hour_ip_combo.setCurrentIndex(0)
        else:
            self.ip_hour_ip_combo.setPlaceholderText("无可用IP，请检查数据或日期范围")
            logging.info("IP地址下拉框为空。")

    # 【新增】IP地址下拉框变化时的处理
    def _on_ip_combo_changed(self, index: int):
        """
        当IP地址下拉框选择变化时，如果当前选项卡是IP按小时统计，则触发查询。
        Args:
            index (int): 选中项的索引。
        """
        # 只有当这是“按IP按小时统计”选项卡并且已经完成首次加载时才自动查询
        if self.tab_widget.currentIndex() == self.tab_widget.indexOf(self.ip_hour_stats_tab):
            self._perform_ip_hour_stats_query()


    def _update_stats_table(self, table: QTableWidget, data: List[Dict[str, Any]], column_keys: List[str]):
        """通用方法：用查询结果更新统计表格。"""
        table.setRowCount(0)
        if not data:
            # 【新增】显示无数据提示
            table.setHorizontalHeaderLabels([f"{col.capitalize().replace('_', ' ')} (无数据)" for col in column_keys])
            return

        table.setColumnCount(len(column_keys))
        table.setHorizontalHeaderLabels([col.capitalize().replace('_', ' ') for col in column_keys])

        for row_idx, record in enumerate(data):
            table.insertRow(row_idx)
            for col_idx, key in enumerate(column_keys):
                item = QTableWidgetItem(str(record.get(key, 'N/A')))
                table.setItem(row_idx, col_idx, item)
        table.resizeColumnsToContents()