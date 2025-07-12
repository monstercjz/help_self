# desktop_center/src/features/alert_center/controllers/statistics/custom_analysis_controller.py
from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QWidget, QMessageBox

from ...services.alert_database_service import AlertDatabaseService
from ...views.statistics.custom_analysis_view import CustomAnalysisView
from ...models.custom_analysis_model import CustomAnalysisModel

class CustomAnalysisController(QObject):
    def __init__(self, db_service: AlertDatabaseService, parent: QWidget):
        super().__init__(parent)
        self.db_service = db_service
        self.model = CustomAnalysisModel()
        self.view = CustomAnalysisView(parent)
        self.is_loaded = False

        self.view.analysis_requested.connect(self._perform_analysis)
        self.view.became_visible.connect(self._on_visibility_change)

    def get_view(self) -> QWidget:
        return self.view

    @Slot()
    def _on_visibility_change(self):
        if not self.is_loaded:
            # First time visible, maybe pre-populate something or just mark as loaded
            self.is_loaded = True
    
    @Slot(list)
    def _perform_analysis(self, dimensions: list):
        if not dimensions:
            QMessageBox.warning(self.view, "提示", "请至少选择一个分析维度。")
            return
            
        start_date, end_date = self.view.date_filter.get_date_range()
        
        data = self.db_service.get_custom_stats(dimensions, start_date, end_date)
        
        tree_data = self.model.build_tree_from_data(data, dimensions)
        
        self.view.update_tree(tree_data, dimensions)