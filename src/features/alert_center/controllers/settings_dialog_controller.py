# desktop_center/src/features/alert_center/controllers/settings_dialog_controller.py
import logging
from src.core.context import ApplicationContext
from ..views.settings_dialog_view import SettingsDialogView
from ..constants import DEFAULT_HOST, DEFAULT_PORT

class SettingsDialogController:
    """
    负责管理告警中心专属设置对话框的业务逻辑。
    """
    def __init__(self, context: ApplicationContext, plugin_name: str, parent_view=None):
        self.context = context
        self.plugin_name = plugin_name
        self.view = SettingsDialogView(parent_view)
        self._load_settings()

    def _load_settings(self):
        """从配置服务加载设置到对话框视图中。"""
        config = self.context.config_service
        settings = {
            "host": config.get_value(self.plugin_name, "host", DEFAULT_HOST),
            "port": config.get_value(self.plugin_name, "port", str(DEFAULT_PORT)),
            "enable_desktop_popup": config.get_value(self.plugin_name, "enable_desktop_popup", "true"),
            "popup_timeout": config.get_value(self.plugin_name, "popup_timeout", "10"),
            "notification_level": config.get_value(self.plugin_name, "notification_level", "WARNING"),
            "load_history_on_startup": config.get_value(self.plugin_name, "load_history_on_startup", "100")
        }
        self.view.set_settings(settings)
        logging.debug(f"[{self.plugin_name}] 设置已加载到对话框: {settings}")

    def _save_settings(self):
        """从对话框视图获取设置并保存到配置服务。"""
        settings = self.view.get_settings()
        config = self.context.config_service
        for key, value in settings.items():
            config.set_option(self.plugin_name, key, str(value))
        
        config.save_config()
        logging.info(f"[{self.plugin_name}] 插件设置已保存: {settings}")
        return True

    def show_dialog(self) -> bool:
        """显示对话框，并根据用户操作返回结果。"""
        if self.view.exec():
            self._save_settings()
            return True
        return False