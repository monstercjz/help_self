# src/features/alert_center/controllers/history_controller.py (【已修复】)
from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QMessageBox, QFileDialog
import logging
import csv
import os
from ..views.history_dialog_view import HistoryDialogView

class HistoryController(QObject):
    def __init__(self, db_service, config_service, parent_window):
        super().__init__()
        self.db_service = db_service
        self.config_service = config_service
        self.parent_window = parent_window
        self.view = None

    def _ensure_view_created(self):
        if not self.view:
            self.view = HistoryDialogView(self.config_service, self.parent_window)
            self.view.search_requested.connect(self.perform_search)
            self.view.delete_requested.connect(self.delete_alerts)
            self.view.export_requested.connect(self.export_data)

    @Slot()
    def show_dialog(self):
        self._ensure_view_created()
        self.view.exec()

    @Slot(dict)
    def perform_search(self, params: dict):
        if not self.view: return
        self.view.set_loading(True)
        results, total_count = self.db_service.search_alerts(**params)
        self.view.update_table(results)
        self.view.update_pagination(total_count, params.get('page'), params.get('page_size'))
        self.view.set_loading(False)
    
    @Slot(list)
    def delete_alerts(self, ids: list):
        reply = QMessageBox.warning(
            self.view, "确认删除", f"确定要删除选中的 {len(ids)} 条记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_service.delete_alerts_by_ids(ids):
                QMessageBox.information(self.view, "成功", "记录已删除。")
                self.view.refresh_search()
            else:
                QMessageBox.critical(self.view, "失败", "删除失败。")

    @Slot(dict)
    def export_data(self, params: dict):
        file_path, _ = QFileDialog.getSaveFileName(self.view, "导出历史记录", 
                                                   os.path.expanduser("~/Desktop/alerts_history.csv"), 
                                                   "CSV Files (*.csv)")
        if not file_path: return
        
        # 【修复】确保获取所有数据，而不是仅当前页
        # 复制一份参数，防止修改原始字典
        export_params = params.copy()
        export_params['page'] = 1
        export_params['page_size'] = 9999999 
        all_results, total = self.db_service.search_alerts(**export_params)
        
        if not all_results:
            QMessageBox.information(self.view, "提示", "没有符合当前筛选条件的数据可导出。")
            return
            
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                # 使用视图中定义的表头顺序
                fieldnames = ["id", "timestamp", "severity", "type", "source_ip", "message"]
                writer = csv.writer(f)
                writer.writerow(self.view.table_header_labels) # 写入中文表头
                
                for row_data in all_results:
                    writer.writerow([row_data.get(key, '') for key in fieldnames])

            QMessageBox.information(self.view, "成功", f"共 {len(all_results)} 条数据已导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self.view, "失败", f"导出失败: {e}")
            logging.error(f"导出CSV失败: {e}", exc_info=True)