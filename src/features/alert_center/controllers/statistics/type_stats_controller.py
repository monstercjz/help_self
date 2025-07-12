# desktop_center/src/features/alert_center/controllers/statistics/type_stats_controller.py
from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QWidget

from ...services.alert_database_service import AlertDatabaseService
from ...views.statistics.type_stats_view import TypeStatsView

class TypeStatsController(QObject):
    def __init__(self, db_service: AlertDatabaseService, parent: QWidget):
        super().__init__(parent)
        self.db_service = db_service
        self.view = TypeStatsView(parent)
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
        data = self.db_service.get_stats_by_type(start_date, end_date)
        self.view.update_table(data)