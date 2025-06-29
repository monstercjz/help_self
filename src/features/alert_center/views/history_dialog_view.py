# src/features/alert_center/views/history_dialog_view.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTableWidget,
                               QTableWidgetItem, QHeaderView, QHBoxLayout,
                               QDateEdit, QLineEdit, QPushButton, QComboBox,
                               QRadioButton, QButtonGroup, QMessageBox, QMenu,
                               QApplication)
from PySide6.QtCore import Qt, QDate, Signal, Slot
from PySide6.QtGui import QColor, QAction
from src.services.config_service import ConfigService

SEVERITY_COLORS = {"CRITICAL": QColor("#FFDDDD"), "WARNING": QColor("#FFFFCC"), "INFO": QColor("#FFFFFF")}

class HistoryDialogView(QDialog):
    """【视图】历史记录浏览器，纯UI，通过信号与Controller交互。"""
    search_requested = Signal(dict)
    delete_requested = Signal(list)
    export_requested = Signal(dict)

    def __init__(self, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        self.setWindowTitle("历史记录浏览器")
        self.setMinimumSize(950, 700)
        
        self.current_page = 1
        self.page_size = int(self.config_service.get_value("HistoryPage", "page_size", "50"))
        self.total_pages = 0
        self.current_sort_column_db = 'timestamp'
        self.current_sort_direction = 'DESC'
        
        self._init_ui()
        self._connect_signals()
        
        self.refresh_search() # 首次打开时触发一次搜索

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

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
        filter_layout.addWidget(self.start_date_edit)
        filter_layout.addWidget(QLabel("到"))
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit.setDate(QDate.currentDate())
        filter_layout.addWidget(self.end_date_edit)

        filter_layout.addWidget(QLabel("严重等级:"))
        self.severity_buttons = QButtonGroup(self)
        self.severity_all = QRadioButton("全部"); self.severity_all.setChecked(True)
        self.severity_info = QRadioButton("信息")
        self.severity_warning = QRadioButton("警告")
        self.severity_critical = QRadioButton("危急")
        for btn in [self.severity_all, self.severity_info, self.severity_warning, self.severity_critical]:
            self.severity_buttons.addButton(btn)
            filter_layout.addWidget(btn)

        filter_layout.addWidget(QLabel("关键词:"))
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("请输入关键词...")
        filter_layout.addWidget(self.keyword_edit)
        self.search_field_combo = QComboBox()
        self.search_field_combo.addItems(["所有字段", "消息内容", "来源IP", "信息类型"])
        filter_layout.addWidget(self.search_field_combo)
        self.query_button = QPushButton("查询")
        self.reset_button = QPushButton("重置")
        filter_layout.addWidget(self.query_button)
        filter_layout.addWidget(self.reset_button)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "接收时间", "严重等级", "信息类型", "来源IP", "详细内容"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for i in range(5): header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionsClickable(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        main_layout.addWidget(self.table)

        pagination_layout = QHBoxLayout()
        self.status_label = QLabel("正在加载...")
        pagination_layout.addWidget(self.status_label)
        self.export_button = QPushButton("导出当前查询")
        self.delete_selected_button = QPushButton("删除选中记录")
        pagination_layout.addWidget(self.export_button)
        pagination_layout.addWidget(self.delete_selected_button)
        pagination_layout.addStretch()
        self.first_page_button = QPushButton("首页")
        self.prev_page_button = QPushButton("上一页")
        self.page_number_edit = QLineEdit("1"); self.page_number_edit.setFixedWidth(40)
        self.next_page_button = QPushButton("下一页")
        self.last_page_button = QPushButton("末页")
        for btn in [self.first_page_button, self.prev_page_button, self.page_number_edit, self.next_page_button, self.last_page_button]:
            pagination_layout.addWidget(btn)
        main_layout.addLayout(pagination_layout)

    def _connect_signals(self):
        self.btn_today.clicked.connect(lambda: self._set_date_range_and_search("today"))
        self.btn_yesterday.clicked.connect(lambda: self._set_date_range_and_search("yesterday"))
        self.btn_last_7_days.clicked.connect(lambda: self._set_date_range_and_search("last7days"))
        self.btn_last_30_days.clicked.connect(lambda: self._set_date_range_and_search("last30days"))
        self.query_button.clicked.connect(self.refresh_search)
        self.reset_button.clicked.connect(self._reset_filters)
        self.severity_buttons.buttonClicked.connect(self.refresh_search)
        
        self.first_page_button.clicked.connect(lambda: self._go_to_page(1))
        self.prev_page_button.clicked.connect(lambda: self._go_to_page(self.current_page - 1))
        self.next_page_button.clicked.connect(lambda: self._go_to_page(self.current_page + 1))
        self.last_page_button.clicked.connect(lambda: self._go_to_page(self.total_pages))
        self.page_number_edit.returnPressed.connect(lambda: self._go_to_page(int(self.page_number_edit.text())))
        
        self.table.horizontalHeader().sectionClicked.connect(self._on_sort_changed)
        self.table.doubleClicked.connect(self._show_full_message)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        self.export_button.clicked.connect(lambda: self.export_requested.emit(self._get_current_search_params()))
        self.delete_selected_button.clicked.connect(self._on_delete_triggered)

    def _get_current_search_params(self) -> dict:
        severities = []
        if self.severity_info.isChecked(): severities.append("INFO")
        elif self.severity_warning.isChecked(): severities.append("WARNING")
        elif self.severity_critical.isChecked(): severities.append("CRITICAL")

        search_field_map = {"所有字段": "all", "消息内容": "message", "来源IP": "source_ip", "信息类型": "type"}
        return {
            "start_date": self.start_date_edit.date().toString("yyyy-MM-dd"),
            "end_date": self.end_date_edit.date().toString("yyyy-MM-dd"),
            "severities": severities,
            "keyword": self.keyword_edit.text().strip(),
            "search_field": search_field_map.get(self.search_field_combo.currentText(), "all"),
            "page": self.current_page,
            "page_size": self.page_size,
            "order_by": self.current_sort_column_db,
            "order_direction": self.current_sort_direction
        }
    
    @Slot()
    def refresh_search(self):
        self.current_page = 1
        self.search_requested.emit(self._get_current_search_params())

    def _go_to_page(self, page_num):
        if self.total_pages > 0 and 1 <= page_num <= self.total_pages:
            self.current_page = page_num
            self.search_requested.emit(self._get_current_search_params())
        elif self.total_pages == 0 and page_num == 1:
            self.current_page = 1
            self.search_requested.emit(self._get_current_search_params())

    def _on_sort_changed(self, logical_index):
        column_map = {0: 'id', 1: 'timestamp', 2: 'severity', 3: 'type', 4: 'source_ip', 5: 'message'}
        new_sort_column = column_map.get(logical_index, 'timestamp')
        if self.current_sort_column_db == new_sort_column:
            self.current_sort_direction = 'ASC' if self.current_sort_direction == 'DESC' else 'DESC'
        else:
            self.current_sort_column_db = new_sort_column
            self.current_sort_direction = 'DESC'
        self.refresh_search()

    def _on_delete_triggered(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "提示", "请选择要删除的记录。")
            return
        ids_to_delete = [int(self.table.item(index.row(), 0).text()) for index in selected_rows]
        self.delete_requested.emit(ids_to_delete)

    @Slot(bool)
    def set_loading(self, is_loading: bool):
        self.status_label.setText("正在查询..." if is_loading else "")
        self.query_button.setEnabled(not is_loading)

    @Slot(list)
    def update_table(self, data: list):
        self.table.setRowCount(0)
        for row_idx, record in enumerate(data):
            self.table.insertRow(row_idx)
            items = [
                QTableWidgetItem(str(record.get('id'))),
                QTableWidgetItem(record.get('timestamp')),
                QTableWidgetItem(record.get('severity')),
                QTableWidgetItem(record.get('type')),
                QTableWidgetItem(record.get('source_ip')),
                QTableWidgetItem(record.get('message'))
            ]
            color = SEVERITY_COLORS.get(record.get('severity'), SEVERITY_COLORS["INFO"])
            for col, item in enumerate(items):
                item.setBackground(color)
                self.table.setItem(row_idx, col, item)
        self._update_sort_indicator()
    
    @Slot(int, int, int)
    def update_pagination(self, total_records: int, current_page: int, page_size: int):
        self.total_pages = (total_records + page_size - 1) // page_size if page_size > 0 else 0
        self.current_page = current_page
        self.status_label.setText(f"共 {total_records} 条, 第 {current_page}/{self.total_pages} 页")
        self.page_number_edit.setText(str(current_page))
        self.first_page_button.setEnabled(current_page > 1)
        self.prev_page_button.setEnabled(current_page > 1)
        self.next_page_button.setEnabled(current_page < self.total_pages)
        self.last_page_button.setEnabled(current_page < self.total_pages)

    def _set_date_range_and_search(self, period: str):
        today = QDate.currentDate()
        if period == "today": self.start_date_edit.setDate(today); self.end_date_edit.setDate(today)
        elif period == "yesterday": self.start_date_edit.setDate(today.addDays(-1)); self.end_date_edit.setDate(today.addDays(-1))
        elif period == "last7days": self.start_date_edit.setDate(today.addDays(-6)); self.end_date_edit.setDate(today)
        elif period == "last30days": self.start_date_edit.setDate(today.addDays(-29)); self.end_date_edit.setDate(today)
        self.refresh_search()

    def _reset_filters(self):
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.end_date_edit.setDate(QDate.currentDate())
        self.severity_all.setChecked(True)
        self.keyword_edit.clear()
        self.search_field_combo.setCurrentIndex(0)
        self.current_sort_column_db = 'timestamp'
        self.current_sort_direction = 'DESC'
        self.refresh_search()
        
    def _update_sort_indicator(self):
        header = self.table.horizontalHeader()
        column_map_rev = {'id': 0, 'timestamp': 1, 'severity': 2, 'type': 3, 'source_ip': 4, 'message': 5}
        idx = column_map_rev.get(self.current_sort_column_db)
        if idx is not None:
            order = Qt.SortOrder.AscendingOrder if self.current_sort_direction == 'ASC' else Qt.SortOrder.DescendingOrder
            header.setSortIndicator(idx, order)
            header.setSortIndicatorShown(True)
        else:
            header.setSortIndicatorShown(False)
            
    def _show_full_message(self, index):
        row = index.row()
        if row >= 0:
            QMessageBox.information(self, "详细内容", self.table.item(row, 5).text())

    def _show_context_menu(self, pos):
        index = self.table.indexAt(pos)
        if not index.isValid(): return
        menu = QMenu(self)
        copy_cell_action = QAction("复制单元格内容", self)
        copy_cell_action.triggered.connect(lambda: QApplication.clipboard().setText(self.table.item(index.row(), index.column()).text()))
        menu.addAction(copy_cell_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))