# desktop_center/src/ui/statistics_dialog.py
import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTabWidget,
                               QWidget, QHBoxLayout, QDateEdit, QPushButton,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QLineEdit, QSpacerItem, QSizePolicy,
                               QComboBox)
from PySide6.QtCore import Qt, QDate, QCoreApplication, QTimer
from PySide6.QtGui import QColor
from src.services.database_service import DatabaseService
from src.services.config_service import ConfigService
from typing import List, Dict, Any

# 【新增】定义一个常量，用于表示IP选择器中的“全部IP”选项
ALL_IPS_OPTION = "【全部IP】"

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
            "ip_activity_tab": False,
            "hourly_stats_tab": False,
            "type_stats_tab": False
        }

        # 【新增】为“按小时分析”Tab添加排序状态变量
        self.hourly_sort_column = 'hour'  # 'hour' or 'count'
        self.hourly_sort_direction = 'ASC' # 'ASC' or 'DESC'

        self._init_ui()
        self._connect_signals() # 连接信号放在初始化UI之后

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

        # --- 2. 按小时分析选项卡 (合并后的新Tab) ---
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
        # 选项卡切换信号
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # 按IP活跃度排行榜选项卡信号
        self.ip_activity_query_button.clicked.connect(self._perform_ip_activity_query)
        self.ip_activity_btn_today.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_activity_start_date, self.ip_activity_end_date, "today"))
        self.ip_activity_btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_activity_start_date, self.ip_activity_end_date, "yesterday"))
        self.ip_activity_btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut(self.ip_activity_start_date, self.ip_activity_end_date, "last7days"))

        # 按小时分析选项卡信号
        self.hourly_query_button.clicked.connect(self._perform_hourly_stats_query)
        self.hourly_btn_today.clicked.connect(lambda: self._set_date_range_shortcut(self.hourly_start_date, self.hourly_end_date, "today"))
        self.hourly_btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut(self.hourly_start_date, self.hourly_end_date, "yesterday"))
        self.hourly_btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut(self.hourly_start_date, self.hourly_end_date, "last7days"))
        self.hourly_ip_combo.currentIndexChanged.connect(self._on_ip_combo_changed)
        # 【新增】为“按小时分析”表格连接排序信号
        self.hourly_stats_table.horizontalHeader().sectionClicked.connect(self._sort_hourly_table)

        # 告警类型排行榜选项卡信号
        self.type_query_button.clicked.connect(self._perform_type_stats_query)
        self.type_btn_today.clicked.connect(lambda: self._set_date_range_shortcut(self.type_start_date, self.type_end_date, "today"))
        self.type_btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut(self.type_start_date, self.type_end_date, "yesterday"))
        self.type_btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut(self.type_start_date, self.type_end_date, "last7days"))

        # 初始加载第一个选项卡的数据
        QTimer.singleShot(0, lambda: self._on_tab_changed(self.tab_widget.currentIndex()))

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
        if start_date_edit is self.ip_activity_start_date:
            self._perform_ip_activity_query()
        elif start_date_edit is self.hourly_start_date:
            self._perform_hourly_stats_query()
        elif start_date_edit is self.type_start_date:
            self._perform_type_stats_query()

    # --- UI 设置方法 ---

    def _setup_ip_activity_tab(self):
        """设置按IP活跃度排行榜选项卡的UI。"""
        # (代码无变化，保持原样)
        # 日期筛选快捷按钮
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

        # 主筛选器
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

        # 表格
        self.ip_activity_table = QTableWidget()
        self.ip_activity_table.setColumnCount(2)
        self.ip_activity_table.setHorizontalHeaderLabels(["来源IP", "数量"])
        self.ip_activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ip_activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.ip_activity_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ip_activity_tab_layout.addWidget(self.ip_activity_table)


    def _setup_hourly_stats_tab(self):
        """设置合并后的“按小时分析”选项卡的UI。"""
        # (代码无变化，保持原样)
        # 日期筛选快捷按钮
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

        # 主筛选器
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("IP地址:"))
        self.hourly_ip_combo = QComboBox() # 重命名
        self.hourly_ip_combo.setEditable(True)
        self.hourly_ip_combo.setPlaceholderText("请选择或输入IP地址")
        self.hourly_ip_combo.setMinimumWidth(150)
        filter_layout.addWidget(self.hourly_ip_combo)

        filter_layout.addWidget(QLabel("日期范围:"))
        self.hourly_start_date = QDateEdit(calendarPopup=True) # 重命名
        self.hourly_start_date.setDate(QDate.currentDate())
        self.hourly_start_date.setMinimumWidth(100)
        filter_layout.addWidget(self.hourly_start_date)
        filter_layout.addWidget(QLabel("到"))
        self.hourly_end_date = QDateEdit(calendarPopup=True) # 重命名
        self.hourly_end_date.setDate(QDate.currentDate())
        self.hourly_end_date.setMinimumWidth(100)
        filter_layout.addWidget(self.hourly_end_date)
        
        self.hourly_query_button = QPushButton("查询") # 重命名
        self.hourly_query_button.setStyleSheet("background-color: #0078d4; color: white; border-radius: 4px; padding: 4px 10px;")
        filter_layout.addWidget(self.hourly_query_button)
        filter_layout.addStretch()
        self.hourly_stats_tab_layout.addLayout(filter_layout)

        # 表格
        self.hourly_stats_table = QTableWidget() # 重命名
        self.hourly_stats_table.setColumnCount(2)
        self.hourly_stats_table.setHorizontalHeaderLabels(["小时", "数量"])
        self.hourly_stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.hourly_stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.hourly_stats_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # 【新增】为“按小时分析”表格启用列头点击
        self.hourly_stats_table.horizontalHeader().setSectionsClickable(True)
        self.hourly_stats_tab_layout.addWidget(self.hourly_stats_table)


    def _setup_type_stats_tab(self):
        """设置告警类型排行榜选项卡的UI。"""
        # (代码无变化，保持原样)
        # 日期筛选快捷按钮
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

        # 主筛选器
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

        # 表格
        self.type_stats_table = QTableWidget()
        self.type_stats_table.setColumnCount(2)
        self.type_stats_table.setHorizontalHeaderLabels(["告警类型", "数量"])
        self.type_stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.type_stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.type_stats_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.type_stats_tab_layout.addWidget(self.type_stats_table)


    # --- 数据加载和查询方法 ---

    def _on_tab_changed(self, index: int):
        """当选项卡切换时触发，实现惰性加载。"""
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
            self._update_hourly_sort_indicator() # 【新增】切换回来时也要更新排序指示器

    def _perform_ip_activity_query(self):
        """执行按IP活跃度统计查询。"""
        start_date = self.ip_activity_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.ip_activity_end_date.date().toString(Qt.DateFormat.ISODate)
        
        self._set_loading_state(self.ip_activity_table, "来源IP", "数量")
        
        logging.info(f"正在查询按IP活跃度排行榜 (日期: {start_date} - {end_date})...")
        results = self.db_service.get_stats_by_ip_activity(start_date, end_date)
        
        self._update_stats_table(self.ip_activity_table, results, ["source_ip", "count"])
        logging.info(f"按IP活跃度排行榜查询完成，共 {len(results)} 个活跃IP。")

    def _perform_hourly_stats_query(self):
        """
        执行按小时统计查询，并根据当前排序状态在内存中排序结果。
        """
        ip_address = self.hourly_ip_combo.currentText().strip()
        start_date = self.hourly_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.hourly_end_date.date().toString(Qt.DateFormat.ISODate)

        self._set_loading_state(self.hourly_stats_table, "小时", "数量")

        if not ip_address:
            logging.warning("按小时分析：IP地址为空，请选择或填写IP地址。")
            self._update_stats_table(self.hourly_stats_table, [], ["hour", "count"])
            return
        
        # 1. 从数据库获取数据
        if ip_address == ALL_IPS_OPTION:
            logging.info(f"正在查询 {start_date} 到 {end_date} 的全局按小时统计...")
            results = self.db_service.get_stats_by_hour(start_date, end_date)
        else:
            logging.info(f"正在查询IP {ip_address} 在 {start_date} 到 {end_date} 的按小时统计...")
            results = self.db_service.get_stats_by_ip_and_hour(ip_address, start_date, end_date)
        
        # 2. 【新增】在内存中对结果进行排序
        if results:
            reverse_order = (self.hourly_sort_direction == 'DESC')
            results.sort(key=lambda x: x[self.hourly_sort_column], reverse=reverse_order)

        # 3. 更新UI
        self._update_stats_table(self.hourly_stats_table, results, ["hour", "count"])
        self._update_hourly_sort_indicator() # 确保排序指示器正确显示
        logging.info(f"按小时统计查询完成，共 {len(results)} 小时数据。")

    def _perform_type_stats_query(self):
        """执行告警类型统计查询。"""
        start_date = self.type_start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.type_end_date.date().toString(Qt.DateFormat.ISODate)
        
        self._set_loading_state(self.type_stats_table, "告警类型", "数量")
        
        logging.info(f"正在查询告警类型排行榜 (日期: {start_date} - {end_date})...")
        results = self.db_service.get_stats_by_type(start_date, end_date)
        
        self._update_stats_table(self.type_stats_table, results, ["type", "count"])
        logging.info(f"告警类型排行榜查询完成，共 {len(results)} 种类型。")


    # --- 辅助方法 ---
    # 【新增】处理“按小时分析”表格排序
    def _sort_hourly_table(self, logical_index: int):
        """
        处理“按小时分析”表格列头点击事件，进行排序。
        Args:
            logical_index (int): 被点击的列的逻辑索引。
        """
        column_map = {0: 'hour', 1: 'count'}
        new_sort_column = column_map.get(logical_index, 'hour')

        if self.hourly_sort_column == new_sort_column:
            self.hourly_sort_direction = 'ASC' if self.hourly_sort_direction == 'DESC' else 'DESC'
        else:
            self.hourly_sort_column = new_sort_column
            self.hourly_sort_direction = 'DESC' if new_sort_column == 'count' else 'ASC' # 默认数量降序，小时升序

        # 重新执行查询和排序
        self._perform_hourly_stats_query()

    # 【新增】更新“按小时分析”表格的排序指示器
    def _update_hourly_sort_indicator(self):
        """
        根据当前排序状态更新“按小时分析”表格列头的Qt自带排序指示器。
        """
        header = self.hourly_stats_table.horizontalHeader()
        column_map_reverse = {'hour': 0, 'count': 1}
        
        logical_index = column_map_reverse.get(self.hourly_sort_column)
        if logical_index is not None:
            header.setSortIndicatorShown(True)
            sort_order = Qt.SortOrder.AscendingOrder if self.hourly_sort_direction == 'ASC' else Qt.SortOrder.DescendingOrder
            header.setSortIndicator(logical_index, sort_order)
        else:
            header.setSortIndicatorShown(False)

    def _populate_ip_combo_box(self):
        """
        填充“按小时分析”Tab中的IP地址下拉框，并添加“全部IP”选项。
        """
        # (代码无变化，保持原样)
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
        """当IP地址下拉框选择变化时，如果当前选项卡已加载，则触发查询。"""
        if self.tab_loaded_flags["hourly_stats_tab"]:
            self._perform_hourly_stats_query()

    def _set_loading_state(self, table: QTableWidget, col1_text: str, col2_text: str):
        """设置表格为加载中状态。"""
        table.setRowCount(0)
        table.setHorizontalHeaderLabels([col1_text, f"{col2_text} (加载中...)"])
        QCoreApplication.processEvents()

    def _update_stats_table(self, table: QTableWidget, data: List[Dict[str, Any]], column_keys: List[str]):
        """通用方法：用查询结果更新统计表格。"""
        # (代码无变化，保持原样)
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