# desktop_center/src/features/alert_center/controllers/alerts_page_controller.py
import logging
from PySide6.QtCore import QObject, Slot, Signal
from PySide6.QtWidgets import QMessageBox

from src.core.context import ApplicationContext
from ..views.alerts_page_view import AlertsPageView
from .history_controller import HistoryController
from .statistics_controller import StatisticsController

class AlertsPageController(QObject):
    """
    【控制器】告警中心主页面的控制器。
    负责处理UI事件、与后台服务和模型交互，并管理子对话框的控制器。
    """
    def __init__(self, context: ApplicationContext, parent=None):
        super().__init__(parent)
        self.context = context
        self.view = AlertsPageView()
        self._connect_signals()
        
        # 加载启动时历史记录
        self._load_history_on_startup()

    def get_view(self) -> AlertsPageView:
        """返回此控制器管理的视图实例。"""
        return self.view

    def _connect_signals(self):
        """连接视图的信号到本控制器的槽。"""
        self.view.page_shown.connect(self.on_page_shown)
        self.view.toggle_popup_status_requested.connect(self.toggle_popup_status)
        self.view.notification_level_changed.connect(self.set_notification_level)
        self.view.history_dialog_requested.connect(self.show_history_dialog)
        self.view.statistics_dialog_requested.connect(self.show_statistics_dialog)
        self.view.clear_database_requested.connect(self.clear_database)
        self.view.clear_display_requested.connect(self.view.clear_table_display)
        
    def _load_history_on_startup(self):
        """在启动时根据配置加载历史告警。"""
        try:
            limit_str = self.context.config_service.get_value("InfoService", "load_history_on_startup", "100")
            limit = int(limit_str)
            if limit > 0:
                logging.info(f"正在从数据库加载最近 {limit} 条历史记录到告警中心页面...")
                records = self.context.db_service.get_recent_alerts(limit)
                # 倒序添加，让最新记录在表格顶部
                for record in reversed(records):
                    self.view.add_alert_to_table(record)
        except (ValueError, TypeError) as e:
            logging.warning(f"无效的 'load_history_on_startup' 配置值: '{limit_str}'. 错误: {e}")

    @Slot(dict)
    def on_new_alert(self, alert_data: dict):
        """[SLOT] 接收到新告警时的处理逻辑。"""
        self.view.add_alert_to_table(alert_data)

    @Slot()
    def on_page_shown(self):
        """[SLOT] 当页面显示时，更新工具栏状态。"""
        self.update_toolbar_status()

    def update_toolbar_status(self):
        """从配置服务获取状态并更新视图。"""
        config = self.context.config_service
        popup_enabled = config.get_value("InfoService", "enable_desktop_popup", "true").lower() == 'true'
        level = config.get_value("InfoService", "notification_level", "WARNING")
        self.view.update_toolbar_labels(popup_enabled, level)

    @Slot()
    def toggle_popup_status(self):
        """[SLOT] 切换桌面弹窗启用状态。"""
        config = self.context.config_service
        is_enabled = config.get_value("InfoService", "enable_desktop_popup", "true").lower() == 'true'
        new_status = not is_enabled
        config.set_option("InfoService", "enable_desktop_popup", str(new_status).lower())
        config.save_config()
        self.update_toolbar_status()
        logging.info(f"桌面弹窗状态已切换为: {'启用' if new_status else '禁用'}")

    @Slot(str)
    def set_notification_level(self, level: str):
        """[SLOT] 设置新的通知级别阈值。"""
        config = self.context.config_service
        config.set_option("InfoService", "notification_level", level)
        config.save_config()
        self.update_toolbar_status()
        logging.info(f"通知级别已设置为: {level}")

    @Slot()
    def show_history_dialog(self):
        """[SLOT] 创建并显示历史记录对话框。"""
        # 控制器持有对话框的控制器，确保其生命周期
        self.history_controller = HistoryController(self.context, self.view)
        self.history_controller.show_dialog()

    @Slot()
    def show_statistics_dialog(self):
        """[SLOT] 创建并显示统计分析对话框。"""
        self.statistics_controller = StatisticsController(self.context, self.view)
        self.statistics_controller.show_dialog()

    @Slot()
    def clear_database(self):
        """[SLOT] 清空数据库中的所有告警记录。"""
        reply = QMessageBox.warning(
            self.view, "危险操作确认",
            "您确定要永久删除所有历史告警记录吗？\n此操作无法撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.context.db_service.clear_all_alerts():
                QMessageBox.information(self.view, "成功", "所有历史记录已成功清除。")
                self.view.clear_table_display()
            else:
                QMessageBox.critical(self.view, "失败", "清除历史记录时发生错误，请查看日志。")