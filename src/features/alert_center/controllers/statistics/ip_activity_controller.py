# desktop_center/src/features/alert_center/controllers/statistics/ip_activity_controller.py
from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QWidget

from ...services.alert_database_service import AlertDatabaseService
from ...views.statistics.ip_activity_view import IPActivityView

class IPActivityController(QObject):
    def __init__(self, db_service: AlertDatabaseService, parent: QWidget):
        super().__init__(parent)
        self.db_service = db_service
        self.view = IPActivityView(parent)
        self.is_loaded = False
        
        self.view.query_requested.connect(self._perform_query)
        self.view.became_visible.connect(self._on_visibility_change)

    def get_view(self) -> QWidget:
        return self.view

    @Slot()
    def _on_visibility_change(self):
        if not self.is_loaded:
            self._perform_query()
            self.is_loaded = True

    @Slot()
    def _perform_query(self):
        start_date, end_date = self.view.date_filter.get_date_range()
        data = self.db_service.get_stats_by_ip_activity(start_date, end_date)
        self.view.update_table(data)