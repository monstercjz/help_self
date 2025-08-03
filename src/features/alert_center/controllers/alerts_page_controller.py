# desktop_center/src/features/alert_center/controllers/alerts_page_controller.py
import logging
from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QMessageBox

from src.core.context import ApplicationContext
from ..views.alerts_page_view import AlertsPageView
from ..services.alert_database_service import AlertDatabaseService
from .settings_dialog_controller import SettingsDialogController

class AlertsPageController(QObject):
    def __init__(self, context: ApplicationContext, db_service: AlertDatabaseService, plugin_name: str, parent=None):
        super().__init__(parent)
        self.context = context
        self.db_service = db_service
        self.plugin_name = plugin_name
        self.view = AlertsPageView()
        self._connect_signals()
        
        self._load_history_on_startup()

    def get_view(self) -> AlertsPageView:
        return self.view

    def _connect_signals(self):
        self.view.page_shown.connect(self.on_page_shown)
        self.view.settings_requested.connect(self.show_settings_dialog)
        self.view.toggle_popup_status_requested.connect(self.toggle_popup_status)
        self.view.notification_level_changed.connect(self.set_notification_level)
        self.view.history_dialog_requested.connect(self.show_history_dialog)
        self.view.statistics_dialog_requested.connect(self.show_statistics_dialog)
        self.view.clear_database_requested.connect(self.clear_database)
        self.view.clear_display_requested.connect(self.view.clear_table_display)
        
    def _load_history_on_startup(self):
        try:
            limit_str = self.context.config_service.get_value(self.plugin_name, "load_history_on_startup", "100")
            limit = int(limit_str)
            if limit > 0:
                logging.info(f"正在从数据库加载最近 {limit} 条历史记录到告警中心页面...")
                records = self.db_service.get_recent_alerts(limit)
                for record in reversed(records):
                    self.view.add_alert_to_table(record)
        except (ValueError, TypeError) as e:
            logging.warning(f"无效的 'load_history_on_startup' 配置值: '{limit_str}'. 错误: {e}")

    @Slot(dict)
    def on_new_alert(self, alert_data: dict):
        self.view.add_alert_to_table(alert_data)

    @Slot()
    def on_page_shown(self):
        self.update_toolbar_status()

    def update_toolbar_status(self):
        config = self.context.config_service
        popup_enabled = config.get_value(self.plugin_name, "enable_desktop_popup", "true").lower() == 'true'
        level = config.get_value(self.plugin_name, "notification_level", "WARNING")
        self.view.update_toolbar_labels(popup_enabled, level)

    @Slot()
    def toggle_popup_status(self):
        config = self.context.config_service
        is_enabled = config.get_value(self.plugin_name, "enable_desktop_popup", "true").lower() == 'true'
        new_status = not is_enabled
        config.set_option(self.plugin_name, "enable_desktop_popup", str(new_status).lower())
        config.save_config()
        self.update_toolbar_status()
        logging.info(f"桌面弹窗状态已切换为: {'启用' if new_status else '禁用'}")

    @Slot(str)
    def set_notification_level(self, level: str):
        config = self.context.config_service
        config.set_option(self.plugin_name, "notification_level", level)
        config.save_config()
        self.update_toolbar_status()
        logging.info(f"通知级别已设置为: {level}")

    @Slot()
    def show_settings_dialog(self):
        """显示插件专属的设置对话框。"""
        # 注意：这里我们传递了 self.plugin_name
        controller = SettingsDialogController(self.context, self.plugin_name, self.view)
        # 如果用户点击OK保存了设置，可能需要重新加载某些状态
        if controller.show_dialog():
            logging.info(f"[{self.plugin_name}] 设置已更新，正在刷新工具栏状态。")
            # 例如，通知级别可能已更改，需要更新UI
            self.update_toolbar_status()
            # 如果有其他依赖配置的逻辑，也应在此处触发更新
            # 比如，如果监听端口变了，可能需要提示用户重启插件/应用

    @Slot()
    def show_history_dialog(self):
        from .history_controller import HistoryController
        self.history_controller = HistoryController(self.db_service, self.view)
        self.history_controller.show_dialog()

    @Slot()
    def show_statistics_dialog(self):
        from .statistics_dialog_controller import StatisticsDialogController
        self.statistics_controller = StatisticsDialogController(self.db_service, self.view)
        self.statistics_controller.show_dialog()

    @Slot()
    def clear_database(self):
        reply = QMessageBox.warning(
            self.view, "危险操作确认",
            "您确定要永久删除所有历史告警记录吗？\n此操作无法撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_service.clear_all_alerts():
                QMessageBox.information(self.view, "成功", "所有历史记录已成功清除。")
                self.view.clear_table_display()
            else:
                QMessageBox.critical(self.view, "失败", "清除历史记录时发生错误，请查看日志。")