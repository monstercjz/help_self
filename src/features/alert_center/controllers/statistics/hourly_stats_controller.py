# desktop_center/src/features/alert_center/controllers/statistics/hourly_stats_controller.py
from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QWidget

from src.core.context import ApplicationContext
from ...views.statistics.hourly_stats_view import HourlyStatsView

class HourlyStatsController(QObject):
    def __init__(self, context: ApplicationContext, parent: QWidget):
        super().__init__(parent)
        self.context = context
        self.view = HourlyStatsView(parent)
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
        ips = self.context.db_service.get_distinct_source_ips(start_date, end_date)
        self.view.ip_filter.set_ip_list(ips)

    @Slot()
    def _perform_query(self):
        start_date, end_date = self.view.date_filter.get_date_range()
        ip = self.view.ip_filter.get_ip()
        
        if ip is None:
            data = self.context.db_service.get_stats_by_hour(start_date, end_date)
        else:
            data = self.context.db_service.get_stats_by_ip_and_hour(ip, start_date, end_date)
            
        self.view.update_table(data)