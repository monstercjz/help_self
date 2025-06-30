# desktop_center/src/features/alert_center/views/history_dialog_view.py
import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QHBoxLayout, QDateEdit, QLineEdit, QPushButton, 
                               QComboBox, QRadioButton, QButtonGroup, QMenu, QApplication, 
                               QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QDate, QCoreApplication, Signal, QPoint, Slot
from PySide6.QtGui import QColor

# UI相关的常量
SEVERITY_COLORS = { "CRITICAL": QColor("#FFDDDD"), "WARNING": QColor("#FFFFCC"), "INFO": QColor("#FFFFFF") }

class HistoryDialogView(QDialog):
    """
    【视图】历史记录浏览器。
    纯UI组件，负责展示数据和发送用户操作信号。
    """
    # --- Signals to Controller ---
    search_requested = Signal(dict)
    export_requested = Signal(dict)
    delete_alerts_requested = Signal(list)
    page_size_changed = Signal(int)
    severity_filter_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("历史记录浏览器")
        self.setMinimumSize(950, 700)
        self._init_ui()

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
        severity_group_layout = QHBoxLayout()
        self.severity_buttons = QButtonGroup(self)
        self.severity_all = QRadioButton("全部")
        self.severity_info = QRadioButton("信息")
        self.severity_warning = QRadioButton("警告")
        self.severity_critical = QRadioButton("危急")
        self.severity_all.setChecked(True)
        for btn in [self.severity_all, self.severity_info, self.severity_warning, self.severity_critical]:
            self.severity_buttons.addButton(btn)
            severity_group_layout.addWidget(btn)
        filter_layout.addLayout(severity_group_layout)

        filter_layout.addWidget(QLabel("关键词:"))
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("请输入关键词...")
        filter_layout.addWidget(self.keyword_edit)
        self.search_field_combo = QComboBox()
        self.search_field_combo.addItems(["所有字段", "消息内容", "来源IP", "信息类型"])
        filter_layout.addWidget(self.search_field_combo)

        self.query_button = QPushButton("查询")
        filter_layout.addWidget(self.query_button)
        self.reset_button = QPushButton("重置")
        filter_layout.addWidget(self.reset_button)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table_header_labels = ["ID", "接收时间", "严重等级", "信息类型", "来源IP", "详细内容"]
        self.table.setHorizontalHeaderLabels(self.table_header_labels)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for i in range(5): header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionsClickable(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        # 【新增】统一选中项样式
        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #cce8ff;
                color: black;
            }
        """)
        main_layout.addWidget(self.table)
        
        pagination_layout = QHBoxLayout()
        self.status_label = QLabel("正在加载...")
        pagination_layout.addWidget(self.status_label)
        self.export_button = QPushButton("导出当前查询")
        pagination_layout.addWidget(self.export_button)
        self.delete_selected_button = QPushButton("删除选中记录")
        self.delete_selected_button.setStyleSheet("background-color: #e04a4a; color: white;")
        pagination_layout.addWidget(self.delete_selected_button)
        pagination_layout.addStretch()
        self.first_page_button = QPushButton("首页")
        self.prev_page_button = QPushButton("上一页")
        self.page_number_edit = QLineEdit("1")
        self.page_number_edit.setFixedWidth(40)
        self.page_number_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_page_button = QPushButton("下一页")
        self.last_page_button = QPushButton("末页")
        for btn in [self.first_page_button, self.prev_page_button, self.page_number_edit, self.next_page_button, self.last_page_button]:
            pagination_layout.addWidget(btn)
        main_layout.addLayout(pagination_layout)

        self.table.doubleClicked.connect(self._show_full_message)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.severity_buttons.buttonClicked.connect(lambda: self.severity_filter_changed.emit())

    @Slot(list)
    def update_table(self, data: list):
        self.table.setRowCount(0)
        for row_idx, record in enumerate(data):
            self.table.insertRow(row_idx)
            items = [
                QTableWidgetItem(str(record.get('id', ''))),
                QTableWidgetItem(record.get('timestamp', 'N/A')),
                QTableWidgetItem(record.get('severity', 'INFO')),
                QTableWidgetItem(record.get('type', 'Unknown')),
                QTableWidgetItem(record.get('source_ip', 'N/A')),
                QTableWidgetItem(record.get('message', 'N/A'))
            ]
            color = SEVERITY_COLORS.get(record.get('severity', 'INFO'), SEVERITY_COLORS["INFO"])
            for col, item in enumerate(items):
                item.setBackground(color)
                self.table.setItem(row_idx, col, item)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

    @Slot(int, int, int)
    def update_pagination_ui(self, current_page: int, total_pages: int, total_records: int):
        self.status_label.setText(f"共找到 {total_records} 条记录，当前显示第 {current_page}/{total_pages} 页")
        self.page_number_edit.setText(str(current_page))
        is_not_first_page = current_page > 1
        is_not_last_page = current_page < total_pages
        has_data = total_records > 0
        
        self.first_page_button.setEnabled(is_not_first_page)
        self.prev_page_button.setEnabled(is_not_first_page)
        self.next_page_button.setEnabled(is_not_last_page)
        self.last_page_button.setEnabled(is_not_last_page)
        self.page_number_edit.setEnabled(has_data)
        self.export_button.setEnabled(has_data)
        self.delete_selected_button.setEnabled(has_data)

    @Slot(str, str)
    def update_sort_indicator(self, column_name: str, direction: str):
        header = self.table.horizontalHeader()
        column_map = {'id': 0, 'timestamp': 1, 'severity': 2, 'type': 3, 'source_ip': 4, 'message': 5}
        logical_index = column_map.get(column_name)
        if logical_index is not None:
            header.setSortIndicatorShown(True)
            sort_order = Qt.SortOrder.AscendingOrder if direction == 'ASC' else Qt.SortOrder.DescendingOrder
            header.setSortIndicator(logical_index, sort_order)
        else:
            header.setSortIndicatorShown(False)

    def get_selected_alert_ids(self) -> list:
        selected_rows = self.table.selectionModel().selectedRows()
        alert_ids = []
        for index in selected_rows:
            item = self.table.item(index.row(), 0)
            if item:
                try:
                    alert_ids.append(int(item.text()))
                except ValueError:
                    logging.warning(f"无法将ID '{item.text()}' 转换为整数，已跳过。")
        return alert_ids

    def get_filter_parameters(self) -> dict:
        severities = []
        if self.severity_info.isChecked(): severities.append("INFO")
        if self.severity_warning.isChecked(): severities.append("WARNING")
        if self.severity_critical.isChecked(): severities.append("CRITICAL")

        search_field_map = {"所有字段": "all", "消息内容": "message", "来源IP": "source_ip", "信息类型": "type"}
        
        return {
            "start_date": self.start_date_edit.date().toString(Qt.DateFormat.ISODate),
            "end_date": self.end_date_edit.date().toString(Qt.DateFormat.ISODate),
            "severities": severities,
            "keyword": self.keyword_edit.text().strip(),
            "search_field": search_field_map.get(self.search_field_combo.currentText(), "all")
        }

    def _show_full_message(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 5)
            if item:
                QMessageBox.information(self, "详细内容", item.text())

    def _show_context_menu(self, pos: QPoint):
        index = self.table.indexAt(pos)
        if not index.isValid(): return

        menu = QMenu(self)
        copy_cell_action = menu.addAction("复制单元格内容")
        copy_row_action = menu.addAction("复制行所有数据")
        menu.addSeparator()
        show_full_message_action = menu.addAction("显示完整消息")

        copy_cell_action.triggered.connect(lambda: QApplication.clipboard().setText(self.table.item(index.row(), index.column()).text()))
        row_data = [self.table.item(index.row(), c).text() for c in range(self.table.columnCount())]
        copy_row_action.triggered.connect(lambda: QApplication.clipboard().setText('\t'.join(row_data)))
        show_full_message_action.triggered.connect(self._show_full_message)
        show_full_message_action.setEnabled(index.column() == 5)
        
        menu.exec(self.table.viewport().mapToGlobal(pos))