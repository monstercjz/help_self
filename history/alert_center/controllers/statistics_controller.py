# desktop_center/src/features/alert_center/controllers/statistics_controller.py
from PySide6.QtCore import QObject, Slot, QDate
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
        self.hourly_sort_column = 'hour'
        self.hourly_sort_direction = 'ASC'

        self.tab_loaded_flags = {
            "ip_activity_tab": False,
            "hourly_stats_tab": False,
            "multidim_stats_tab": False,
            "type_stats_tab": False
        }
        self._connect_signals()
    
    def show_dialog(self):
        """显示对话框并加载第一个标签页的数据。"""
        self.on_tab_changed(self.view.tab_widget.currentIndex())
        self.view.exec()

    def _connect_signals(self):
        self.view.tab_changed.connect(self.on_tab_changed)
        self.view.query_requested.connect(self._perform_query_for_tab)
        self.view.hourly_ip_changed.connect(self._on_hourly_ip_changed)
        self.view.multidim_ip_changed.connect(self._on_multidim_ip_changed)
        self.view.hourly_sort_requested.connect(self._handle_hourly_sort_request)
        # 【新增】连接快捷日期请求信号
        self.view.date_shortcut_requested.connect(self._handle_date_shortcut)

    @Slot(str, str)
    def _handle_date_shortcut(self, tab_name: str, period: str):
        """[SLOT] 响应快捷日期按钮点击。"""
        start_date_edit = getattr(self.view, f"{tab_name}_start_date")
        end_date_edit = getattr(self.view, f"{tab_name}_end_date")
        
        today = QDate.currentDate()
        if period == "today":
            start_date_edit.setDate(today)
            end_date_edit.setDate(today)
        elif period == "yesterday":
            yesterday = today.addDays(-1)
            start_date_edit.setDate(yesterday)
            end_date_edit.setDate(yesterday)
        elif period == "last7days":
            start_date_edit.setDate(today.addDays(-6))
            end_date_edit.setDate(today)
        
        # 设置完日期后，立即触发查询
        self._perform_query_for_tab(tab_name)


    @Slot()
    def _on_hourly_ip_changed(self):
        """响应“按小时分析”IP变化，触发查询。"""
        self._perform_query_for_tab("hourly_stats_tab")

    @Slot()
    def _on_multidim_ip_changed(self):
        """响应“多维分析”IP变化，触发查询。"""
        self._perform_query_for_tab("multidim_stats_tab")
        
    @Slot(int)
    def _handle_hourly_sort_request(self, column_index: int):
        """响应“按小时分析”的排序请求。"""
        column_map = {0: 'hour', 1: 'count'}
        new_sort_column = column_map.get(column_index, 'hour')
        
        if self.hourly_sort_column == new_sort_column:
            self.hourly_sort_direction = 'ASC' if self.hourly_sort_direction == 'DESC' else 'DESC'
        else:
            self.hourly_sort_column = new_sort_column
            self.hourly_sort_direction = 'DESC' if new_sort_column == 'count' else 'ASC'
        
        self._perform_query_for_tab("hourly_stats_tab")


    @Slot(int)
    def on_tab_changed(self, index: int):
        current_widget = self.view.tab_widget.widget(index)
        if not current_widget: return
        tab_name = current_widget.objectName()
        
        if tab_name in ["hourly_stats_tab", "multidim_stats_tab"]:
            self._update_ip_combo_for_tab(tab_name)
            
        if not self.tab_loaded_flags.get(tab_name, False):
            self._perform_query_for_tab(tab_name)
            self.tab_loaded_flags[tab_name] = True
        
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
            if params.get("ip_address") is None: # 全部IP
                data = db.get_stats_by_hour(params["start_date"], params["end_date"])
            else:
                data = db.get_stats_by_ip_and_hour(params["ip_address"], params["start_date"], params["end_date"])
            
            if data:
                reverse_order = (self.hourly_sort_direction == 'DESC')
                data.sort(key=lambda x: x.get(self.hourly_sort_column, 0), reverse=reverse_order)
            
            self.view.update_hourly_stats_table(data)
            column_map_reverse = {'hour': 0, 'count': 1}
            self.view.update_hourly_sort_indicator(column_map_reverse[self.hourly_sort_column], self.hourly_sort_direction)

        elif tab_name == "multidim_stats_tab":
            data = db.get_detailed_hourly_stats(params["start_date"], params["end_date"], params.get("ip_address"))
            tree_data = self.model.process_detailed_stats_for_tree(data)
            self.view.populate_multidim_tree(tree_data)