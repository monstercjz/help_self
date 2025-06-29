# desktop_center/src/features/alert_center/controllers/history_controller.py
import logging
import os
import csv
from PySide6.QtCore import QObject, Slot, QDate
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from src.core.context import ApplicationContext
from ..views.history_dialog_view import HistoryDialogView
from ..models.history_model import HistoryModel

class HistoryController(QObject):
    """
    【控制器】历史记录对话框的控制器。
    负责处理所有与历史记录相关的业务逻辑。
    """
    def __init__(self, context: ApplicationContext, parent: QWidget):
        super().__init__(parent)
        self.context = context
        self.model = HistoryModel()
        self.view = HistoryDialogView(parent)
        self._connect_signals()

    def show_dialog(self):
        """显示对话框。"""
        self._perform_search()
        self.view.exec()

    def _connect_signals(self):
        """连接视图信号到控制器槽函数。"""
        self.view.query_button.clicked.connect(self._on_query_button_clicked)
        self.view.reset_button.clicked.connect(self._reset_filters)
        self.view.table.horizontalHeader().sectionClicked.connect(self._sort_table)
        self.view.export_button.clicked.connect(self._export_data)
        self.view.delete_selected_button.clicked.connect(self._delete_selected_alerts)

        # 【新增】连接严重等级筛选变化的信号到查询槽
        self.view.severity_filter_changed.connect(self._on_query_button_clicked)

        # 分页按钮
        self.view.first_page_button.clicked.connect(lambda: self._go_to_page(1))
        self.view.prev_page_button.clicked.connect(lambda: self._go_to_page(self.model.current_page - 1))
        self.view.next_page_button.clicked.connect(lambda: self._go_to_page(self.model.current_page + 1))
        self.view.last_page_button.clicked.connect(lambda: self._go_to_page(self.model.total_pages))
        self.view.page_number_edit.returnPressed.connect(lambda: self._go_to_page(int(self.view.page_number_edit.text())))

        # 日期快捷按钮
        self.view.btn_today.clicked.connect(lambda: self._set_date_range_and_search("today"))
        self.view.btn_yesterday.clicked.connect(lambda: self._set_date_range_and_search("yesterday"))
        self.view.btn_last_7_days.clicked.connect(lambda: self._set_date_range_and_search("last7days"))
        self.view.btn_last_30_days.clicked.connect(lambda: self._set_date_range_and_search("last30days"))
    
    def _set_date_range_and_search(self, period: str):
        today = QDate.currentDate()
        if period == "today":
            self.view.start_date_edit.setDate(today)
            self.view.end_date_edit.setDate(today)
        elif period == "yesterday":
            yesterday = today.addDays(-1)
            self.view.start_date_edit.setDate(yesterday)
            self.view.end_date_edit.setDate(yesterday)
        elif period == "last7days":
            self.view.start_date_edit.setDate(today.addDays(-6))
            self.view.end_date_edit.setDate(today)
        elif period == "last30days":
            self.view.start_date_edit.setDate(today.addDays(-29))
            self.view.end_date_edit.setDate(today)
        self._on_query_button_clicked()

    @Slot()
    def _on_query_button_clicked(self):
        """响应查询按钮或筛选条件变化，重置到第一页并搜索。"""
        self.model.current_page = 1
        self._perform_search()

    def _perform_search(self):
        """根据当前过滤条件执行数据库查询并更新UI。"""
        params = self.view.get_filter_parameters()
        self.model.start_date = params["start_date"]
        self.model.end_date = params["end_date"]
        self.model.severities = params["severities"]
        self.model.keyword = params["keyword"]
        self.model.search_field = params["search_field"]

        results, total_count = self.context.db_service.search_alerts(
            start_date=self.model.start_date,
            end_date=self.model.end_date,
            severities=self.model.severities,
            keyword=self.model.keyword,
            search_field=self.model.search_field,
            page=self.model.current_page,
            page_size=self.model.page_size,
            order_by=self.model.sort_column,
            order_direction=self.model.sort_direction
        )
        
        self.model.update_pagination(total_count)
        self.view.update_table(results)
        self.view.update_pagination_ui(self.model.current_page, self.model.total_pages, self.model.total_records)
        self.view.update_sort_indicator(self.model.sort_column, self.model.sort_direction)

    @Slot(int)
    def _sort_table(self, logical_index: int):
        column_map = {0: 'id', 1: 'timestamp', 2: 'severity', 3: 'type', 4: 'source_ip', 5: 'message'}
        new_sort_column = column_map.get(logical_index, 'timestamp')

        if self.model.sort_column == new_sort_column:
            self.model.sort_direction = 'ASC' if self.model.sort_direction == 'DESC' else 'DESC'
        else:
            self.model.sort_column = new_sort_column
            self.model.sort_direction = 'DESC'
        
        self.model.current_page = 1
        self._perform_search()

    def _go_to_page(self, page_num: int):
        if 1 <= page_num <= self.model.total_pages or (page_num == 1 and self.model.total_pages == 0):
            self.model.current_page = page_num
            self._perform_search()
        else:
            self.view.page_number_edit.setText(str(self.model.current_page))

    @Slot()
    def _reset_filters(self):
        self.view.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.view.end_date_edit.setDate(QDate.currentDate())
        self.view.severity_all.setChecked(True)
        self.view.keyword_edit.clear()
        self.view.search_field_combo.setCurrentIndex(0)
        self.model.current_page = 1
        self.model.sort_column = 'timestamp'
        self.model.sort_direction = 'DESC'
        self._perform_search()

    @Slot()
    def _delete_selected_alerts(self):
        ids = self.view.get_selected_alert_ids()
        if not ids:
            QMessageBox.information(self.view, "没有选中", "请选择要删除的记录。")
            return
        
        reply = QMessageBox.warning(
            self.view, "确认删除", f"您确定要删除选中的 {len(ids)} 条记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.context.db_service.delete_alerts_by_ids(ids):
                QMessageBox.information(self.view, "成功", "选中的记录已删除。")
                self._perform_search() # 刷新
            else:
                QMessageBox.critical(self.view, "失败", "删除记录时发生错误。")

    @Slot()
    def _export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self.view, "导出历史记录", os.path.expanduser("~/Desktop/alerts_history.csv"), "CSV Files (*.csv)")
        if not file_path: return

        all_results, _ = self.context.db_service.search_alerts(
            start_date=self.model.start_date, end_date=self.model.end_date, severities=self.model.severities,
            keyword=self.model.keyword, search_field=self.model.search_field, page=1,
            page_size=self.model.total_records if self.model.total_records > 0 else 9999999,
            order_by=self.model.sort_column, order_direction=self.model.sort_direction
        )

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "接收时间", "严重等级", "信息类型", "来源IP", "详细内容"])
                for row in all_results:
                    writer.writerow([
                        row.get('id'), row.get('timestamp'), row.get('severity'),
                        row.get('type'), row.get('source_ip'), row.get('message')
                    ])
            QMessageBox.information(self.view, "导出成功", f"数据已导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self.view, "导出失败", f"导出时发生错误:\n{e}")