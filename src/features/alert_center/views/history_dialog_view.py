# desktop_center/src/features/alert_center/views/history_dialog_view.py
import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QHBoxLayout, QLineEdit, QPushButton, 
                               QComboBox, QRadioButton, QButtonGroup, QMenu, QApplication, 
                               QMessageBox)
from PySide6.QtCore import Qt, Signal, QPoint, Slot
from PySide6.QtGui import QColor, QAction
from ..widgets.date_filter_widget import DateFilterWidget

SEVERITY_COLORS = { "CRITICAL": QColor("#FFDDDD"), "WARNING": QColor("#FFFFCC"), "INFO": QColor("#FFFFFF") }

class HistoryDialogView(QDialog):
    query_requested = Signal()
    reset_requested = Signal()
    sort_requested = Signal(int)
    delete_alerts_requested = Signal(list)
    export_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("历史记录浏览器")
        self.setMinimumSize(950, 700)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        self.date_filter_widget = DateFilterWidget()
        main_layout.addWidget(self.date_filter_widget)

        other_filters_layout = QHBoxLayout()
        other_filters_layout.addWidget(QLabel("严重等级:"))
        severity_group_layout = QHBoxLayout()
        self.severity_buttons = QButtonGroup(self)
        self.severity_all = QRadioButton("全部"); self.severity_info = QRadioButton("信息")
        self.severity_warning = QRadioButton("警告"); self.severity_critical = QRadioButton("危急")
        self.severity_all.setChecked(True)
        for btn in [self.severity_all, self.severity_info, self.severity_warning, self.severity_critical]:
            self.severity_buttons.addButton(btn); severity_group_layout.addWidget(btn)
        other_filters_layout.addLayout(severity_group_layout)

        other_filters_layout.addWidget(QLabel("关键词:"))
        self.keyword_edit = QLineEdit(); self.keyword_edit.setPlaceholderText("请输入关键词...")
        other_filters_layout.addWidget(self.keyword_edit)
        self.search_field_combo = QComboBox(); self.search_field_combo.addItems(["所有字段", "消息内容", "来源IP", "信息类型"])
        other_filters_layout.addWidget(self.search_field_combo)
        
        self.query_button = QPushButton("查询"); other_filters_layout.addWidget(self.query_button)
        self.reset_button = QPushButton("重置"); other_filters_layout.addWidget(self.reset_button)
        other_filters_layout.addStretch()
        main_layout.addLayout(other_filters_layout)

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
        self.table.setStyleSheet("QTableWidget::item:selected { background-color: #cce8ff; color: black; }")
        main_layout.addWidget(self.table)
        
        pagination_layout = QHBoxLayout()
        self.status_label = QLabel("正在加载...")
        pagination_layout.addWidget(self.status_label)
        self.export_button = QPushButton("导出当前查询"); pagination_layout.addWidget(self.export_button)
        self.delete_selected_button = QPushButton("删除选中记录"); self.delete_selected_button.setStyleSheet("background-color: #e04a4a; color: white;")
        pagination_layout.addWidget(self.delete_selected_button)
        pagination_layout.addStretch()
        self.first_page_button = QPushButton("首页"); self.prev_page_button = QPushButton("上一页")
        self.page_number_edit = QLineEdit("1"); self.page_number_edit.setFixedWidth(40); self.page_number_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_page_button = QPushButton("下一页"); self.last_page_button = QPushButton("末页")
        for btn in [self.first_page_button, self.prev_page_button, self.page_number_edit, self.next_page_button, self.last_page_button]:
            pagination_layout.addWidget(btn)
        main_layout.addLayout(pagination_layout)
        
        self._connect_signals()

    def _connect_signals(self):
        self.date_filter_widget.filter_changed.connect(lambda: self.query_requested.emit())
        self.severity_buttons.buttonClicked.connect(lambda: self.query_requested.emit())
        self.keyword_edit.returnPressed.connect(self.query_requested.emit)
        self.search_field_combo.currentIndexChanged.connect(lambda: self.query_requested.emit())
        
        self.query_button.clicked.connect(self.query_requested.emit)
        self.reset_button.clicked.connect(self.reset_requested.emit)
        self.table.horizontalHeader().sectionClicked.connect(self.sort_requested.emit)
        self.export_button.clicked.connect(self.export_requested.emit)
        self.delete_selected_button.clicked.connect(lambda: self.delete_alerts_requested.emit(self.get_selected_alert_ids()))
        
        self.table.doubleClicked.connect(self._show_full_message)
        # 【变更】恢复被遗漏的右键菜单信号连接
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
    def get_filter_parameters(self) -> dict:
        start_date, end_date = self.date_filter_widget.get_date_range()
        severities = []
        # 【修正】修复一个逻辑错误，当选中"全部"时，severities应为空列表
        if self.severity_info.isChecked(): severities.append("INFO")
        elif self.severity_warning.isChecked(): severities.append("WARNING")
        elif self.severity_critical.isChecked(): severities.append("CRITICAL")
        
        search_field_map = {"所有字段": "all", "消息内容": "message", "来源IP": "source_ip", "信息类型": "type"}
        
        return {
            "start_date": start_date, "end_date": end_date,
            "severities": severities, "keyword": self.keyword_edit.text().strip(),
            "search_field": search_field_map.get(self.search_field_combo.currentText(), "all")
        }

    @Slot(list)
    def update_table(self, data: list):
        self.table.setRowCount(0)
        for row_idx, record in enumerate(data):
            self.table.insertRow(row_idx)
            items = [QTableWidgetItem(str(record.get(k, ''))) for k in ['id', 'timestamp', 'severity', 'type', 'source_ip', 'message']]
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
        has_data = total_records > 0
        self.first_page_button.setEnabled(current_page > 1)
        self.prev_page_button.setEnabled(current_page > 1)
        self.next_page_button.setEnabled(current_page < total_pages)
        self.last_page_button.setEnabled(current_page < total_pages)
        for w in [self.page_number_edit, self.export_button, self.delete_selected_button]: w.setEnabled(has_data)
        
    @Slot(str, str)
    def update_sort_indicator(self, column_name: str, direction: str):
        header = self.table.horizontalHeader()
        column_map = {'id': 0, 'timestamp': 1, 'severity': 2, 'type': 3, 'source_ip': 4, 'message': 5}
        sort_order = Qt.SortOrder.AscendingOrder if direction == 'ASC' else Qt.SortOrder.DescendingOrder
        header.setSortIndicator(column_map.get(column_name, 0), sort_order)

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
        copy_cell_action = QAction("复制单元格内容", self)
        copy_row_action = QAction("复制行所有数据", self)
        menu.addSeparator()
        show_full_message_action = QAction("显示完整消息", self)
        copy_cell_action.triggered.connect(lambda: QApplication.clipboard().setText(self.table.item(index.row(), index.column()).text()))
        row_data = [self.table.item(index.row(), c).text() for c in range(self.table.columnCount())]
        copy_row_action.triggered.connect(lambda: QApplication.clipboard().setText('\t'.join(row_data)))
        show_full_message_action.triggered.connect(self._show_full_message)
        show_full_message_action.setEnabled(index.column() == 5)
        menu.addAction(copy_cell_action)
        menu.addAction(copy_row_action)
        menu.addSeparator()
        menu.addAction(show_full_message_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))