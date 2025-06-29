# src/features/alert_center/controllers/alerts_page_controller.py
import logging
from datetime import datetime
from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QMessageBox

class AlertsPageController(QObject):
    def __init__(self, view, config_service, db_service, parent_window):
        super().__init__()
        self.view = view
        self.config_service = config_service
        self.db_service = db_service
        self.parent_window = parent_window
        self._connect_view_signals()
        
    def _connect_view_signals(self):
        self.view.clear_display_requested.connect(self.clear_table_display)
        self.view.clear_database_requested.connect(self.clear_database)
        self.view.load_history_requested.connect(self.load_history_on_startup)
        self.view.page_shown.connect(self.sync_toolbar_status)
        self.view.popup_status_toggled.connect(self.toggle_popup_status)
        self.view.notification_level_changed.connect(self.set_notification_level)

    @Slot(dict)
    def add_alert_from_thread(self, alert_data: dict):
        alert_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.view.add_alert_to_table(alert_data)

    @Slot()
    def clear_table_display(self):
        self.view.clear_table()
        logging.info("UI表格显示已被用户清空。")

    @Slot()
    def clear_database(self):
        reply = QMessageBox.warning(
            self.parent_window, "危险操作确认",
            "您确定要永久删除所有历史告警记录吗？\n此操作无法撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_service.clear_all_alerts():
                QMessageBox.information(self.parent_window, "成功", "所有历史记录已成功清除。")
                self.view.clear_table()
            else:
                QMessageBox.critical(self.parent_window, "失败", "清除历史记录时发生错误。")
    
    @Slot()
    def load_history_on_startup(self):
        try:
            limit_str = self.config_service.get_value("InfoService", "load_history_on_startup", "100")
            limit = int(limit_str)
            if limit > 0:
                records = self.db_service.get_recent_alerts(limit)
                for record in reversed(records):
                    self.view.add_alert_to_table(record)
        except (ValueError, TypeError) as e:
            logging.warning(f"加载历史配置无效: {e}")

    @Slot()
    def sync_toolbar_status(self):
        is_enabled = self.config_service.get_value("InfoService", "enable_desktop_popup", "true").lower() == 'true'
        self.view.update_popup_button_text(is_enabled)
        level = self.config_service.get_value("InfoService", "notification_level", "WARNING")
        self.view.update_level_button_text(level)

    @Slot()
    def toggle_popup_status(self):
        is_enabled = self.config_service.get_value("InfoService", "enable_desktop_popup", "true").lower() == 'true'
        new_status = not is_enabled
        self.config_service.set_option("InfoService", "enable_desktop_popup", str(new_status).lower())
        self.config_service.save_config()
        self.sync_toolbar_status()

    @Slot(str)
    def set_notification_level(self, level: str):
        self.config_service.set_option("InfoService", "notification_level", level)
        self.config_service.save_config()
        self.sync_toolbar_status()