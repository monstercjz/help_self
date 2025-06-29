# desktop_center/src/features/alert_center/controllers/statistics_controller.py
from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QWidget

from src.core.context import ApplicationContext
from ..views.statistics_dialog_view import StatisticsDialogView
from ..models.statistics_model import StatisticsModel

class StatisticsController(QObject):
    """
    【控制器】统计分析对话框的控制器。
    """
    def __init__(self, context: ApplicationContext, parent: QWidget):
        super().__init__(parent)
        self.context = context
        self.view = StatisticsDialogView(parent)
        self.model = StatisticsModel()
        self.tab_loaded_flags = {
            "ip_activity_tab": False,
            "hourly_stats_tab": False,
            "multidim_stats_tab": False,
            "type_stats_tab": False
        }
        self._connect_signals()
    
    def show_dialog(self):
        """显示对话框并加载第一个标签页的数据。"""
        self.view.exec()

    def _connect_signals(self):
        self.view.tab_changed.connect(self.on_tab_changed)
        self.view.query_requested.connect(self._perform_query_for_tab)

    @Slot(int)
    def on_tab_changed(self, index: int):
        current_widget = self.view.tab_widget.widget(index)
        if not current_widget: return
        tab_name = current_widget.objectName()
        
        # 惰性加载：只有在首次切换到标签页时才加载数据
        if not self.tab_loaded_flags.get(tab_name, False):
            self._perform_query_for_tab(tab_name)
            self.tab_loaded_flags[tab_name] = True
        
        # 对于需要IP列表的标签页，每次切换时都更新IP下拉框
        if tab_name in ["hourly_stats_tab", "multidim_stats_tab"]:
            self._update_ip_combo_for_tab(tab_name)

    def _update_ip_combo_for_tab(self, tab_name: str):
        params = self.view.get_filter_parameters(tab_name)
        ip_list = self.context.db_service.get_distinct_source_ips(params["start_date"], params["end_date"])
        combo = getattr(self.view, f"{tab_name}_ip_combo")
        self.view.update_ip_combo_box(combo, ip_list)

    @Slot(str)
    def _perform_query_for_tab(self, tab_name: str):
        params = self.view.get_filter_parameters(tab_name)
        db = self.context.db_service
        
        if tab_name == "ip_activity_tab":
            data = db.get_stats_by_ip_activity(params["start_date"], params["end_date"])
            self.view.update_ip_activity_table(data)
        elif tab_name == "type_stats_tab":
            data = db.get_stats_by_type(params["start_date"], params["end_date"])
            self.view.update_type_stats_table(data)
        elif tab_name == "hourly_stats_tab":
            if params["ip_address"] is None: # 全部IP
                data = db.get_stats_by_hour(params["start_date"], params["end_date"])
            else:
                data = db.get_stats_by_ip_and_hour(params["ip_address"], params["start_date"], params["end_date"])
            self.view.update_hourly_stats_table(data)
        elif tab_name == "multidim_stats_tab":
            data = db.get_detailed_hourly_stats(params["start_date"], params["end_date"], params.get("ip_address"))
            tree_data = self.model.process_detailed_stats_for_tree(data)
            self.view.populate_multidim_tree(tree_data)