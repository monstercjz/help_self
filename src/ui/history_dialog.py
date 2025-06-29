# desktop_center/src/ui/history_dialog.py
import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTableWidget,
                               QTableWidgetItem, QHeaderView, QHBoxLayout,
                               QDateEdit, QLineEdit, QPushButton, QComboBox,
                               QCheckBox, QButtonGroup, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, QDate, QCoreApplication, QTimer
from PySide6.QtGui import QColor
from typing import List, Dict, Any, Tuple
from src.services.database_service import DatabaseService
from src.services.config_service import ConfigService # 导入ConfigService
from datetime import datetime, timedelta

SEVERITY_COLORS = {
    "CRITICAL": QColor("#FFDDDD"),
    "WARNING": QColor("#FFFFCC"),
    "INFO": QColor("#FFFFFF")
}

class HistoryDialog(QDialog):
    """
    一个独立的对话框，用于浏览和查询历史告警记录。
    提供日期范围、严重等级、关键词搜索和分页功能。
    """
    def __init__(self, db_service: DatabaseService, config_service: ConfigService, parent=None): # 【修正】接收config_service
        super().__init__(parent)
        self.db_service = db_service
        self.config_service = config_service # 【新增】保存ConfigService实例
        self.setWindowTitle("历史记录浏览器")
        self.setMinimumSize(950, 700)
        
        self.current_page = 1
        # 【修改】从config_service获取page_size
        self.page_size = int(self.config_service.get_value("HistoryPage", "page_size", "50"))
        self.total_records = 0
        self.total_pages = 0

        self._init_ui()
        self._connect_signals()
        self._load_initial_data()

    def _init_ui(self):
        """初始化对话框的UI布局和控件。"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

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
        self.severity_buttons = QButtonGroup(self)
        
        self.severity_all = QCheckBox("全部")
        self.severity_all.setChecked(True)
        
        self.severity_info = QCheckBox("信息")
        self.severity_warning = QCheckBox("警告")
        self.severity_critical = QCheckBox("危急")

        severity_group_layout.addWidget(self.severity_all)
        severity_group_layout.addWidget(self.severity_info)
        severity_group_layout.addWidget(self.severity_warning)
        severity_group_layout.addWidget(self.severity_critical)
        
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
        self.table.setHorizontalHeaderLabels(["ID", "接收时间", "严重等级", "信息类型", "来源IP", "详细内容"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.table)
        
        pagination_layout = QHBoxLayout()
        self.status_label = QLabel("正在加载...")
        pagination_layout.addWidget(self.status_label)
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
        self.query_button.clicked.connect(self._perform_search)
        self.reset_button.clicked.connect(self._reset_filters)
        
        self.first_page_button.clicked.connect(lambda: self._go_to_page(1))
        self.prev_page_button.clicked.connect(lambda: self._go_to_page(self.current_page - 1))
        self.next_page_button.clicked.connect(lambda: self._go_to_page(self.current_page + 1))
        self.last_page_button.clicked.connect(lambda: self._go_to_page(self.total_pages))
        
        self.page_number_edit.returnPressed.connect(lambda: self._go_to_page(int(self.page_number_edit.text())))
        
        self.severity_info.clicked.connect(self._update_severity_all)
        self.severity_warning.clicked.connect(self._update_severity_all)
        self.severity_critical.clicked.connect(self._update_severity_all)
        self.severity_all.clicked.connect(self._toggle_all_severities)
        
        self.table.doubleClicked.connect(self._show_full_message)

    def _load_initial_data(self):
        """对话框首次打开时加载数据。"""
        self._perform_search()

    def _perform_search(self):
        """根据当前过滤条件执行数据库查询并更新UI。"""
        self.status_label.setText("正在查询...")
        QCoreApplication.processEvents()

        start_date = self.start_date_edit.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date_edit.date().toString(Qt.DateFormat.ISODate)
        
        selected_severities = []
        if not self.severity_all.isChecked():
            if self.severity_info.isChecked(): selected_severities.append("INFO")
            if self.severity_warning.isChecked(): selected_severities.append("WARNING")
            if self.severity_critical.isChecked(): selected_severities.append("CRITICAL")

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
            page_size=self.page_size
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
            
            timestamp = record.get('timestamp', 'N/A')
            severity = record.get('severity', 'INFO')
            alert_type = record.get('type', 'Unknown')
            source_ip = record.get('source_ip', 'N/A')
            message = record.get('message', 'N/A')
            
            items = [
                QTableWidgetItem(str(record.get('id', ''))),
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
        else:
            self.page_number_edit.setEnabled(True)

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
        self.severity_all.setChecked(True)
        self._toggle_all_severities()
        self.keyword_edit.clear()
        self.search_field_combo.setCurrentIndex(0)
        self.current_page = 1
        self._perform_search()

    def _toggle_all_severities(self):
        """处理“全部”复选框的逻辑。"""
        is_all_checked = self.severity_all.isChecked()
        self.severity_info.setChecked(is_all_checked)
        self.severity_warning.setChecked(is_all_checked)
        self.severity_critical.setChecked(is_all_checked)
        
        if not is_all_checked and not (self.severity_info.isChecked() or 
                                       self.severity_warning.isChecked() or 
                                       self.severity_critical.isChecked()):
            self.severity_all.setChecked(True)


    def _update_severity_all(self):
        """当单个严重等级被点击时，更新“全部”的状态。"""
        if self.sender() is not self.severity_all:
            if self.severity_info.isChecked() and self.severity_warning.isChecked() and self.severity_critical.isChecked():
                self.severity_all.setChecked(True)
            else:
                self.severity_all.setChecked(False)
                
    def _show_full_message(self):
        """双击表格行时显示完整消息内容。"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            message_item = self.table.item(current_row, 5)
            if message_item:
                QMessageBox.information(self, "详细内容", message_item.text())