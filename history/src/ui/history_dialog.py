# desktop_center/src/ui/history_dialog.py
import logging
import os
import csv # 用于导出CSV
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTableWidget,
                               QTableWidgetItem, QHeaderView, QHBoxLayout,
                               QDateEdit, QLineEdit, QPushButton, QComboBox,
                               # 【核心修正】QCheckBox 替换为 QRadioButton
                               QRadioButton, QButtonGroup, QSpacerItem, QSizePolicy,
                               QMenu, QApplication, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QDate, QCoreApplication, QTimer, QSize
from PySide6.QtGui import QColor, QIcon, QAction
from typing import List, Dict, Any, Tuple
from src.services.database_service import DatabaseService
from src.services.config_service import ConfigService

SEVERITY_COLORS = {
    "CRITICAL": QColor("#FFDDDD"),
    "WARNING": QColor("#FFFFCC"),
    "INFO": QColor("#FFFFFF")
}

# 【修正】移除自定义排序图标常量 (这些常量已在上一轮修正中被移除，此处保留为注释说明)
# ORDER_ASC_ICON = QIcon.fromTheme("go-up") # 上箭头
# ORDER_DESC_ICON = QIcon.fromTheme("go-down") # 下箭头
# ORDER_NONE_ICON = QIcon() # 无图标

class HistoryDialog(QDialog):
    """
    一个独立的对话框，用于浏览和查询历史告警记录。
    提供日期范围、严重等级、关键词搜索、分页、排序、导出和删除功能。
    """
    def __init__(self, db_service: DatabaseService, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.db_service = db_service
        self.config_service = config_service
        self.setWindowTitle("历史记录浏览器")
        self.setMinimumSize(950, 700)
        
        self.current_page = 1
        # 【修改】从config_service获取page_size
        self.page_size = int(self.config_service.get_value("HistoryPage", "page_size", "50"))
        self.total_records = 0
        self.total_pages = 0

        # 【新增】排序状态变量
        self.current_sort_column_db = 'timestamp' # 数据库字段名
        self.current_sort_direction = 'DESC' # 排序方向 'ASC' 或 'DESC'
        
        self._init_ui()
        self._connect_signals()
        self._load_initial_data()

    def _init_ui(self):
        """初始化对话框的UI布局和控件。"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # 【新增】日期筛选快捷按钮布局
        date_shortcut_layout = QHBoxLayout()
        date_shortcut_layout.addWidget(QLabel("快捷日期:"))
        self.btn_today = QPushButton("今天")
        self.btn_yesterday = QPushButton("昨天")
        self.btn_last_7_days = QPushButton("近7天")
        self.btn_last_30_days = QPushButton("近30天")
        date_shortcut_layout.addWidget(self.btn_today)
        date_shortcut_layout.addWidget(self.btn_yesterday)
        date_shortcut_layout.addWidget(self.btn_last_7_days)
        date_shortcut_layout.addWidget(self.btn_last_30_days)
        date_shortcut_layout.addStretch()
        main_layout.addLayout(date_shortcut_layout)

        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("日期范围:"))
        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.start_date_edit.setMinimumWidth(100)
        filter_layout.addWidget(self.start_date_edit)
        filter_layout.addWidget(QLabel("到"))
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setMinimumWidth(100)
        filter_layout.addWidget(self.end_date_edit)

        filter_layout.addWidget(QLabel("严重等级:"))
        severity_group_layout = QHBoxLayout()
        # 【核心修正】将所有严重等级选项都使用 QRadioButton，并加入到排他性的 QButtonGroup 中
        self.severity_buttons = QButtonGroup(self)
        self.severity_buttons.setExclusive(True) # 确保只有其中一个被选中
        
        self.severity_all = QRadioButton("全部")
        self.severity_info = QRadioButton("信息")
        self.severity_warning = QRadioButton("警告")
        self.severity_critical = QRadioButton("危急")

        # 默认选中“全部”
        self.severity_all.setChecked(True)

        severity_group_layout.addWidget(self.severity_all)
        severity_group_layout.addWidget(self.severity_info)
        severity_group_layout.addWidget(self.severity_warning)
        severity_group_layout.addWidget(self.severity_critical)
        
        # 将所有 RadioButton 添加到 QButtonGroup
        self.severity_buttons.addButton(self.severity_all)
        self.severity_buttons.addButton(self.severity_info)
        self.severity_buttons.addButton(self.severity_warning)
        self.severity_buttons.addButton(self.severity_critical)
        
        filter_layout.addLayout(severity_group_layout)

        filter_layout.addWidget(QLabel("关键词:"))
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("请输入关键词...")
        self.keyword_edit.setMinimumWidth(150)
        filter_layout.addWidget(self.keyword_edit)

        self.search_field_combo = QComboBox()
        self.search_field_combo.addItems(["所有字段", "消息内容", "来源IP", "信息类型"])
        filter_layout.addWidget(self.search_field_combo)

        self.query_button = QPushButton("查询")
        self.query_button.setStyleSheet("background-color: #0078d4; color: white; border-radius: 4px; padding: 4px 10px;")
        filter_layout.addWidget(self.query_button)

        self.reset_button = QPushButton("重置")
        self.reset_button.setStyleSheet("background-color: #f0f0f0; border-radius: 4px; padding: 4px 10px;")
        filter_layout.addWidget(self.reset_button)
        
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        # 【修改】更新列标签，添加ID列
        self.table_header_labels = ["ID", "接收时间", "严重等级", "信息类型", "来源IP", "详细内容"]
        self.table.setHorizontalHeaderLabels(self.table_header_labels)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # ID列
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # 接收时间
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # 严重等级
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # 信息类型
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # 来源IP

        # 【新增】允许点击列头进行排序
        header.setSectionsClickable(True)
        # 【新增】设置右键菜单策略
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # 整行选中
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection) # 允许Ctrl/Shift多选
        main_layout.addWidget(self.table)
        
        pagination_layout = QHBoxLayout()
        self.status_label = QLabel("正在加载...")
        pagination_layout.addWidget(self.status_label)
        
        # 【新增】导出按钮
        self.export_button = QPushButton("导出当前查询")
        self.export_button.setStyleSheet("background-color: #f0f0f0; border-radius: 4px; padding: 4px 10px;")
        pagination_layout.addWidget(self.export_button)

        # 【新增】删除选中按钮
        self.delete_selected_button = QPushButton("删除选中记录")
        self.delete_selected_button.setStyleSheet("background-color: #e04a4a; color: white; border-radius: 4px; padding: 4px 10px;")
        pagination_layout.addWidget(self.delete_selected_button)

        pagination_layout.addStretch()

        self.first_page_button = QPushButton("首页")
        self.prev_page_button = QPushButton("上一页")
        self.page_number_edit = QLineEdit("1")
        self.page_number_edit.setFixedWidth(40)
        self.page_number_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_page_button = QPushButton("下一页")
        self.last_page_button = QPushButton("末页")

        pagination_layout.addWidget(self.first_page_button)
        pagination_layout.addWidget(self.prev_page_button)
        pagination_layout.addWidget(self.page_number_edit)
        pagination_layout.addWidget(self.next_page_button)
        pagination_layout.addWidget(self.last_page_button)
        
        main_layout.addLayout(pagination_layout)

    def _connect_signals(self):
        """连接UI控件的信号到槽函数。"""
        # 【新增】日期快捷按钮
        self.btn_today.clicked.connect(lambda: self._set_date_range_shortcut("today"))
        self.btn_yesterday.clicked.connect(lambda: self._set_date_range_shortcut("yesterday"))
        self.btn_last_7_days.clicked.connect(lambda: self._set_date_range_shortcut("last7days"))
        self.btn_last_30_days.clicked.connect(lambda: self._set_date_range_shortcut("last30days"))

        self.query_button.clicked.connect(self._perform_search)
        self.reset_button.clicked.connect(self._reset_filters)
        
        self.first_page_button.clicked.connect(lambda: self._go_to_page(1))
        self.prev_page_button.clicked.connect(lambda: self._go_to_page(self.current_page - 1))
        self.next_page_button.clicked.connect(lambda: self._go_to_page(self.current_page + 1))
        self.last_page_button.clicked.connect(lambda: self._go_to_page(self.total_pages))
        
        self.page_number_edit.returnPressed.connect(lambda: self._go_to_page(int(self.page_number_edit.text())))
        
        # 【核心修正】严重等级选择现在由 QRadioButton 和排他性 QButtonGroup 自动处理
        # 当任意严重等级 RadioButton 被点击时，触发查询
        self.severity_buttons.buttonClicked.connect(lambda: self._perform_search())
        
        self.table.doubleClicked.connect(self._show_full_message)

        # 【新增】列头排序信号
        self.table.horizontalHeader().sectionClicked.connect(self._sort_table)
        # 【新增】右键菜单信号
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        # 【新增】导出和删除按钮信号
        self.export_button.clicked.connect(self._export_data)
        self.delete_selected_button.clicked.connect(self._delete_selected_alerts)

    def _load_initial_data(self):
        """对话框首次打开时加载数据。"""
        self._perform_search()
        self._update_sort_indicator() # 【新增】初始化时更新排序指示器

    # 【新增】设置日期范围快捷方法
    def _set_date_range_shortcut(self, period: str):
        """
        根据预设周期设置日期范围。
        Args:
            period (str): 'today', 'yesterday', 'last7days', 'last30days'
        """
        today = QDate.currentDate()
        if period == "today":
            self.start_date_edit.setDate(today)
            self.end_date_edit.setDate(today)
        elif period == "yesterday":
            yesterday = today.addDays(-1)
            self.start_date_edit.setDate(yesterday)
            self.end_date_edit.setDate(yesterday)
        elif period == "last7days":
            self.start_date_edit.setDate(today.addDays(-6)) # 今天算在内
            self.end_date_edit.setDate(today)
        elif period == "last30days":
            self.start_date_edit.setDate(today.addDays(-29)) # 今天算在内
            self.end_date_edit.setDate(today)
        
        self.current_page = 1 # 日期范围变化后回到第一页
        self._perform_search()

    # 【新增】处理表格排序
    def _sort_table(self, logical_index: int):
        """
        处理表格列头点击事件，进行排序。
        Args:
            logical_index (int): 被点击的列的逻辑索引。
        """
        # 定义列索引到数据库字段的映射
        column_map = {
            0: 'id',
            1: 'timestamp',
            2: 'severity',
            3: 'type',
            4: 'source_ip',
            5: 'message'
        }
        
        new_sort_column_db = column_map.get(logical_index, 'timestamp')

        if self.current_sort_column_db == new_sort_column_db:
            # 如果是同一列，切换排序方向
            self.current_sort_direction = 'ASC' if self.current_sort_direction == 'DESC' else 'DESC'
        else:
            # 如果是不同列，则以新列的默认降序开始
            self.current_sort_column_db = new_sort_column_db
            self.current_sort_direction = 'DESC' # 默认降序

        self.current_page = 1 # 排序变化后回到第一页
        self._perform_search()
        self._update_sort_indicator() # 更新列头排序指示器

    # 【修正】更新列头排序指示器，使用Qt内置API
    def _update_sort_indicator(self):
        """
        根据当前排序状态更新表格列头的Qt自带排序指示器。
        """
        header = self.table.horizontalHeader()
        column_map_reverse = {
            'id': 0, 'timestamp': 1, 'severity': 2, 'type': 3,
            'source_ip': 4, 'message': 5
        }
        
        logical_index = column_map_reverse.get(self.current_sort_column_db)
        if logical_index is not None:
            header.setSortIndicatorShown(True) # 确保显示排序指示器
            # 将自定义的 'ASC'/'DESC' 映射到 Qt.AscendingOrder / Qt.DescendingOrder
            sort_order = Qt.SortOrder.AscendingOrder if self.current_sort_direction == 'ASC' else Qt.SortOrder.DescendingOrder
            header.setSortIndicator(logical_index, sort_order)
        else:
            # 如果没有有效的排序列（例如，初始加载时可能还未点击），则隐藏指示器
            header.setSortIndicatorShown(False)


    def _perform_search(self):
        """根据当前过滤条件执行数据库查询并更新UI。"""
        self.status_label.setText("正在查询...")
        QCoreApplication.processEvents() # 确保UI更新

        start_date = self.start_date_edit.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date_edit.date().toString(Qt.DateFormat.ISODate)
        
        selected_severities = []
        # 【核心修正】根据当前选中 RadioButton 的文本来确定过滤条件
        if self.severity_all.isChecked():
            # 如果选中“全部”，则severities列表为空，数据库查询将返回所有等级
            pass 
        elif self.severity_info.isChecked():
            selected_severities.append("INFO")
        elif self.severity_warning.isChecked():
            selected_severities.append("WARNING")
        elif self.severity_critical.isChecked():
            selected_severities.append("CRITICAL")

        keyword = self.keyword_edit.text().strip()
        search_field_map = {
            "所有字段": "all",
            "消息内容": "message",
            "来源IP": "source_ip",
            "信息类型": "type"
        }
        search_field = search_field_map.get(self.search_field_combo.currentText(), "all")

        results, total_count = self.db_service.search_alerts(
            start_date=start_date,
            end_date=end_date,
            severities=selected_severities,
            keyword=keyword,
            search_field=search_field,
            page=self.current_page,
            page_size=self.page_size,
            order_by=self.current_sort_column_db,     # 【修改】传递排序字段
            order_direction=self.current_sort_direction # 【修改】传递排序方向
        )
        
        self.total_records = total_count
        self.total_pages = (total_count + self.page_size - 1) // self.page_size if self.page_size > 0 else 0
        
        self._update_table(results)
        self._update_pagination_ui()
        self.status_label.setText(f"共找到 {self.total_records} 条记录，当前显示第 {self.current_page}/{self.total_pages} 页")
        logging.info(f"历史查询完成: {self.total_records} 条记录, 当前第 {self.current_page}/{self.total_pages} 页")

    def _update_table(self, data: List[Dict[str, Any]]):
        """用查询结果更新表格。"""
        self.table.setRowCount(0)
        for row_idx, record in enumerate(data):
            self.table.insertRow(row_idx)
            
            # 【修改】ID列现在是第一列
            alert_id = str(record.get('id', ''))
            timestamp = record.get('timestamp', 'N/A')
            severity = record.get('severity', 'INFO')
            alert_type = record.get('type', 'Unknown')
            source_ip = record.get('source_ip', 'N/A')
            message = record.get('message', 'N/A')
            
            items = [
                QTableWidgetItem(alert_id),
                QTableWidgetItem(timestamp),
                QTableWidgetItem(severity),
                QTableWidgetItem(alert_type),
                QTableWidgetItem(source_ip),
                QTableWidgetItem(message)
            ]
            
            color = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["INFO"])
            
            for col, item in enumerate(items):
                item.setBackground(color)
                self.table.setItem(row_idx, col, item)
        self.table.resizeColumnsToContents()
        # 确保ID和时间等列自适应内容
        for i in range(5):
             self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)


    def _update_pagination_ui(self):
        """更新分页按钮和状态标签的启用/禁用状态。"""
        self.page_number_edit.setText(str(self.current_page))
        self.first_page_button.setEnabled(self.current_page > 1)
        self.prev_page_button.setEnabled(self.current_page > 1)
        self.next_page_button.setEnabled(self.current_page < self.total_pages)
        self.last_page_button.setEnabled(self.current_page < self.total_pages)
        
        if self.total_pages == 0:
            self.first_page_button.setEnabled(False)
            self.prev_page_button.setEnabled(False)
            self.next_page_button.setEnabled(False)
            self.last_page_button.setEnabled(False)
            self.page_number_edit.setEnabled(False)
            # 【新增】如果没数据，导出和删除按钮也禁用
            self.export_button.setEnabled(False)
            self.delete_selected_button.setEnabled(False)
        else:
            self.page_number_edit.setEnabled(True)
            self.export_button.setEnabled(True)
            # 只有当有选中行时才启用删除按钮（通过槽函数动态控制）
            # 这里先设置为True，具体由槽函数判断是否有选中行
            self.delete_selected_button.setEnabled(True) 

    def _go_to_page(self, page_num: int):
        """跳转到指定页码并执行查询。"""
        if self.total_pages == 0:
            if page_num == 1:
                self.current_page = 1
                self._perform_search()
            return

        if 1 <= page_num <= self.total_pages:
            self.current_page = page_num
            self._perform_search()
        else:
            logging.warning(f"尝试跳转到无效页码: {page_num}, 总页数: {self.total_pages}")
            self.page_number_edit.setText(str(self.current_page))

    def _reset_filters(self):
        """重置所有过滤条件到默认值。"""
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.end_date_edit.setDate(QDate.currentDate())
        
        # 【核心修正】重置时只设置“全部” RadioButton 为选中
        self.severity_all.setChecked(True) 
        
        self.keyword_edit.clear()
        self.search_field_combo.setCurrentIndex(0)
        self.current_page = 1
        
        # 【新增】重置排序状态
        self.current_sort_column_db = 'timestamp'
        self.current_sort_direction = 'DESC'
        self._update_sort_indicator()

        self._perform_search()

    # 【核心修正】_toggle_all_severities 和 _update_severity_all 方法不再需要，因为 QRadioButton 和排他性 QButtonGroup 自动处理了互斥逻辑。
    # 这里将它们移除，确保代码的简洁和正确性。
    # def _toggle_all_severities(self):
    #     """处理“全部”复选框的逻辑。"""
    #     is_all_checked = self.severity_all.isChecked()
    #     self.severity_info.setChecked(is_all_checked)
    #     self.severity_warning.setChecked(is_all_checked)
    #     self.severity_critical.setChecked(is_all_checked)
    #     if not is_all_checked and not (self.severity_info.isChecked() or 
    #                                    self.severity_warning.isChecked() or 
    #                                    self.severity_critical.isChecked()):
    #         self.severity_all.setChecked(True)

    # def _update_severity_all(self):
    #     """当单个严重等级被点击时，更新“全部”的状态。"""
    #     if self.sender() is not self.severity_all:
    #         if self.severity_info.isChecked() and self.severity_warning.isChecked() and self.severity_critical.isChecked():
    #             self.severity_all.setChecked(True)
    #         else:
    #             self.severity_all.setChecked(False)
                
    def _show_full_message(self):
        """双击表格行时显示完整消息内容。"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            message_item = self.table.item(current_row, 5) # 详细内容在第5列（索引从0开始）
            if message_item:
                QMessageBox.information(self, "详细内容", message_item.text())

    # 【新增】表格右键菜单
    def _show_context_menu(self, pos):
        """
        显示表格右键上下文菜单。
        Args:
            pos (QPoint): 鼠标位置，用于定位菜单。
        """
        index = self.table.indexAt(pos)
        if not index.isValid():
            return

        menu = QMenu(self)

        # 复制单元格内容
        copy_cell_action = QAction("复制单元格内容", self)
        copy_cell_action.triggered.connect(lambda: QApplication.clipboard().setText(self.table.item(index.row(), index.column()).text()))
        menu.addAction(copy_cell_action)

        # 复制行所有数据
        copy_row_action = QAction("复制行所有数据", self)
        # 获取当前行所有数据并格式化
        row_data = [self.table.item(index.row(), col).text() for col in range(self.table.columnCount())]
        copy_row_action.triggered.connect(lambda: QApplication.clipboard().setText('\t'.join(row_data))) # 以制表符分隔
        menu.addAction(copy_row_action)

        menu.addSeparator()

        # 显示完整消息 (如果不是消息列，则禁用)
        show_full_message_action = QAction("显示完整消息", self)
        if index.column() == 5: # 详细内容列
            show_full_message_action.triggered.connect(self._show_full_message)
        else:
            show_full_message_action.setEnabled(False)
        menu.addAction(show_full_message_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    # 【新增】导出数据到CSV
    def _export_data(self):
        """将当前筛选条件下的所有数据导出为CSV文件。"""
        # 获取用户选择的文件路径
        file_path, _ = QFileDialog.getSaveFileName(self, "导出历史记录", 
                                                   os.path.expanduser("~/Desktop/alerts_history.csv"), 
                                                   "CSV Files (*.csv);;All Files (*)")
        if not file_path:
            return

        # 重新获取所有符合当前筛选条件的数据，不分页
        start_date = self.start_date_edit.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date_edit.date().toString(Qt.DateFormat.ISODate)
        selected_severities = []
        # 【核心修正】导出数据时，同样根据当前选中 RadioButton 获取过滤条件
        if self.severity_all.isChecked():
            pass # 空列表表示所有等级
        elif self.severity_info.isChecked():
            selected_severities.append("INFO")
        elif self.severity_warning.isChecked():
            selected_severities.append("WARNING")
        elif self.severity_critical.isChecked():
            selected_severities.append("CRITICAL")

        keyword = self.keyword_edit.text().strip()
        search_field_map = {
            "所有字段": "all", "消息内容": "message", "来源IP": "source_ip", "信息类型": "type"
        }
        search_field = search_field_map.get(self.search_field_combo.currentText(), "all")

        # 调用数据库服务获取所有数据 (page_size设置为一个大数，或在db_service中提供一个不分页的获取方法)
        # 这里我们直接传入一个足够大的pageSize来获取所有数据
        all_results, _ = self.db_service.search_alerts(
            start_date=start_date,
            end_date=end_date,
            severities=selected_severities,
            keyword=keyword,
            search_field=search_field,
            page=1,
            page_size=self.total_records if self.total_records > 0 else 9999999, # 确保获取所有记录
            order_by=self.current_sort_column_db,
            order_direction=self.current_sort_direction
        )

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["ID", "接收时间", "严重等级", "信息类型", "来源IP", "详细内容"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in all_results:
                    # 重新映射数据库字段到CSV表头
                    writer.writerow({
                        "ID": row.get('id', ''),
                        "接收时间": row.get('timestamp', 'N/A'),
                        "严重等级": row.get('severity', 'INFO'),
                        "信息类型": row.get('type', 'Unknown'),
                        "来源IP": row.get('source_ip', 'N/A'),
                        "详细内容": row.get('message', '无内容')
                    })
            QMessageBox.information(self, "导出成功", f"数据已成功导出到:\n{file_path}")
            logging.info(f"历史记录已导出到: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出数据时发生错误:\n{e}")
            logging.error(f"导出历史记录失败: {e}", exc_info=True)

    # 【新增】删除选中记录
    def _delete_selected_alerts(self):
        """删除表格中选中的告警记录。"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "没有选中", "请选择要删除的记录。")
            return

        # 获取所有选中行的ID
        alert_ids_to_delete = []
        for index in selected_rows:
            # ID在表格的第0列
            item = self.table.item(index.row(), 0)
            if item:
                try:
                    alert_ids_to_delete.append(int(item.text()))
                except ValueError:
                    logging.error(f"无法将ID '{item.text()}' 转换为整数，跳过。")
                    continue
        
        if not alert_ids_to_delete:
            QMessageBox.information(self, "没有有效ID", "没有找到有效的记录ID进行删除。")
            return

        reply = QMessageBox.warning(
            self,
            "确认删除",
            f"您确定要删除选中的 {len(alert_ids_to_delete)} 条历史告警记录吗？\n此操作无法撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db_service.delete_alerts_by_ids(alert_ids_to_delete):
                QMessageBox.information(self, "删除成功", "选中的记录已成功删除。")
                self._perform_search() # 刷新表格显示
            else:
                QMessageBox.critical(self, "删除失败", "删除记录时发生错误，请查看日志。")