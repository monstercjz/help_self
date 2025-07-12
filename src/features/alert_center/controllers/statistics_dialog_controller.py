# desktop_center/src/features/alert_center/controllers/statistics_dialog_controller.py
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget

from ..services.alert_database_service import AlertDatabaseService
from ..views.statistics_dialog_view import StatisticsDialogView
# 导入所有子控制器
from .statistics.ip_activity_controller import IPActivityController
from .statistics.hourly_stats_controller import HourlyStatsController
from .statistics.multidim_analysis_controller import MultidimAnalysisController
from .statistics.type_stats_controller import TypeStatsController
# 【变更】导入新的自定义分析控制器
from .statistics.custom_analysis_controller import CustomAnalysisController

class StatisticsDialogController(QObject):
    """
    【协调器】统计分析对话框的主控制器。
    负责实例化所有子统计组件，并将它们的视图添加到对话框的选项卡中。
    """
    def __init__(self, db_service: AlertDatabaseService, parent: QWidget):
        super().__init__(parent)
        self.db_service = db_service
        self.view = StatisticsDialogView(parent)
        self._setup_tabs()

    def show_dialog(self):
        self.view.exec()
    
    def _setup_tabs(self):
        # 实例化所有子控制器
        ip_controller = IPActivityController(self.db_service, self.view)
        hourly_controller = HourlyStatsController(self.db_service, self.view)
        multidim_controller = MultidimAnalysisController(self.db_service, self.view)
        type_controller = TypeStatsController(self.db_service, self.view)
        # 【变更】实例化新的自定义分析控制器
        custom_controller = CustomAnalysisController(self.db_service, self.view)
        
        # 将子视图添加到主对话框的TabWidget中
        self.view.add_tab(ip_controller.get_view(), "按IP活跃度排行榜")
        self.view.add_tab(hourly_controller.get_view(), "按小时分析")
        self.view.add_tab(multidim_controller.get_view(), "多维分析")
        self.view.add_tab(type_controller.get_view(), "告警类型排行榜")
        # 【变更】添加新的选项卡
        self.view.add_tab(custom_controller.get_view(), "自定义分析")