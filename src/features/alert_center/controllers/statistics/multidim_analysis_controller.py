# desktop_center/src/features/alert_center/controllers/statistics/multidim_analysis_controller.py
from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QWidget

from ...services.alert_database_service import AlertDatabaseService
from ...views.statistics.multidim_analysis_view import MultidimAnalysisView
from ...models.statistics_model import StatisticsModel

class MultidimAnalysisController(QObject):
    def __init__(self, db_service: AlertDatabaseService, parent: QWidget):
        super().__init__(parent)
        self.db_service = db_service
        self.model = StatisticsModel()
        self.view = MultidimAnalysisView(parent)
        self.is_loaded = False

        self.view.query_requested.connect(self._perform_query)
        self.view.became_visible.connect(self._on_visibility_change)

    def get_view(self) -> QWidget:
        return self.view

    @Slot()
    def _on_visibility_change(self):
        if not self.is_loaded:
            self._update_ip_list()
            self._perform_query()
            self.is_loaded = True
        else:
            self._update_ip_list()

    def _update_ip_list(self):
        start_date, end_date = self.view.date_filter.get_date_range()
        ips = self.db_service.get_distinct_source_ips(start_date, end_date)
        self.view.ip_filter.set_ip_list(ips)

    @Slot()
    def _perform_query(self):
        start_date, end_date = self.view.date_filter.get_date_range()
        ip = self.view.ip_filter.get_ip()
        
        data = self.db_service.get_detailed_hourly_stats(start_date, end_date, ip)
        tree_data = self.model.process_detailed_stats_for_tree(data)
        self.view.update_tree(tree_data)