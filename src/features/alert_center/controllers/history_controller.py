# desktop_center/src/features/alert_center/controllers/history_controller.py
import logging, os, csv
from PySide6.QtCore import QObject, Slot, QDate
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from src.core.context import ApplicationContext
from ..views.history_dialog_view import HistoryDialogView
from ..models.history_model import HistoryModel

class HistoryController(QObject):
    def __init__(self, context: ApplicationContext, parent: QWidget):
        super().__init__(parent)
        self.context = context
        self.model = HistoryModel()
        self.view = HistoryDialogView(parent)
        self._connect_signals()

    def show_dialog(self):
        self._on_query_requested()
        self.view.exec()

    def _connect_signals(self):
        self.view.query_requested.connect(self._on_query_requested)
        self.view.reset_requested.connect(self._reset_filters)
        self.view.sort_requested.connect(self._sort_table)
        self.view.delete_alerts_requested.connect(self._delete_selected_alerts)
        self.view.export_requested.connect(self._export_data)

        self.view.first_page_button.clicked.connect(lambda: self._go_to_page(1))
        self.view.prev_page_button.clicked.connect(lambda: self._go_to_page(self.model.current_page - 1))
        self.view.next_page_button.clicked.connect(lambda: self._go_to_page(self.model.current_page + 1))
        self.view.last_page_button.clicked.connect(lambda: self._go_to_page(self.model.total_pages))
        self.view.page_number_edit.returnPressed.connect(lambda: self._go_to_page(int(self.view.page_number_edit.text())))

    @Slot()
    def _on_query_requested(self):
        # 任何筛选条件变化都应重置到第一页
        self.model.current_page = 1
        self._perform_search()

    def _perform_search(self):
        params = self.view.get_filter_parameters()
        self.model.start_date = params["start_date"]
        self.model.end_date = params["end_date"]
        self.model.severities = params["severities"]
        self.model.keyword = params["keyword"]
        self.model.search_field = params["search_field"]

        results, total_count = self.context.db_service.search_alerts(
            start_date=self.model.start_date, end_date=self.model.end_date,
            severities=self.model.severities, keyword=self.model.keyword,
            search_field=self.model.search_field, page=self.model.current_page,
            page_size=self.model.page_size, order_by=self.model.sort_column,
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
        """【变更】重置逻辑更加明确和健壮。"""
        # 1. 程序化地设置UI控件到默认状态
        self.view.date_filter_widget.set_date_range(QDate.currentDate().addDays(-7), QDate.currentDate())
        self.view.severity_all.setChecked(True)
        self.view.keyword_edit.clear()
        self.view.search_field_combo.setCurrentIndex(0)
        
        # 2. 重置模型状态
        self.model.current_page = 1
        self.model.sort_column = 'timestamp'
        self.model.sort_direction = 'DESC'
        
        # 3. 显式地触发一次查询，而不是依赖信号
        self._perform_search()

    @Slot(list)
    def _delete_selected_alerts(self, ids: list):
        if not ids:
            QMessageBox.information(self.view, "没有选中", "请选择要删除的记录。")
            return
        reply = QMessageBox.warning(self.view, "确认删除", f"您确定要删除选中的 {len(ids)} 条记录吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.context.db_service.delete_alerts_by_ids(ids):
                QMessageBox.information(self.view, "成功", "选中的记录已删除。")
                self._perform_search()
            else:
                QMessageBox.critical(self.view, "失败", "删除记录时发生错误。")

    @Slot()
    def _export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self.view, "导出历史记录", os.path.expanduser("~/Desktop/alerts_history.csv"), "CSV Files (*.csv)")
        if not file_path: return
        
        params = self.view.get_filter_parameters()
        all_results, _ = self.context.db_service.search_alerts(
            start_date=params["start_date"], end_date=params["end_date"],
            severities=params["severities"], keyword=params["keyword"],
            search_field=params["search_field"], page=1,
            page_size=self.model.total_records if self.model.total_records > 0 else 9999999,
            order_by=self.model.sort_column, order_direction=self.model.sort_direction
        )
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "接收时间", "严重等级", "信息类型", "来源IP", "详细内容"])
                for row in all_results:
                    writer.writerow([row.get(k) for k in ['id', 'timestamp', 'severity', 'type', 'source_ip', 'message']])
            QMessageBox.information(self.view, "导出成功", f"数据已导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self.view, "导出失败", f"导出时发生错误:\n{e}")