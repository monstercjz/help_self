# src/features/alert_center/controllers/statistics_controller.py
from PySide6.QtCore import QObject, Slot
import logging
from collections import defaultdict
from ..views.statistics_dialog_view import StatisticsDialogView

class StatisticsController(QObject):
    def __init__(self, db_service, parent_window):
        super().__init__()
        self.db_service = db_service
        self.parent_window = parent_window
        self.view = None

    def _ensure_view_created(self):
        if not self.view:
            self.view = StatisticsDialogView(self.parent_window)
            self.view.query_requested.connect(self.perform_query)
            self.view.ip_list_requested.connect(self.update_ip_list)

    @Slot()
    def show_dialog(self):
        self._ensure_view_created()
        self.view.exec()

    @Slot(str, dict)
    def perform_query(self, tab_name: str, params: dict):
        if not self.view: return
        logging.info(f"Controller: Received query for tab '{tab_name}' with params {params}")
        
        start_date = params['start_date']
        end_date = params['end_date']
        
        if tab_name == "ip_activity":
            data = self.db_service.get_stats_by_ip_activity(start_date, end_date)
            self.view.update_ip_activity_tab(data)
        elif tab_name == "type":
            data = self.db_service.get_stats_by_type(start_date, end_date)
            self.view.update_type_stats_tab(data)
        elif tab_name == "hourly":
            ip = params.get("ip")
            if not ip: return
            if ip == "【全部IP】":
                data = self.db_service.get_stats_by_hour(start_date, end_date)
            else:
                data = self.db_service.get_stats_by_ip_and_hour(ip, start_date, end_date)
            self.view.update_hourly_stats_tab(data)
        elif tab_name == "multidim":
            ip = params.get("ip")
            if not ip: return
            query_ip = None if ip == "【全部IP】" else ip
            raw_data = self.db_service.get_detailed_hourly_stats(start_date, end_date, query_ip)
            tree_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
            for row in raw_data:
                tree_data[row['hour']][row['severity']][row['type']] = row['count']
            self.view.update_multidim_stats_tab(tree_data)

    @Slot(str, dict)
    def update_ip_list(self, tab_name, params):
        if not self.view: return
        ips = self.db_service.get_distinct_source_ips(params['start_date'], params['end_date'])
        self.view.populate_ip_combo(tab_name, ips)