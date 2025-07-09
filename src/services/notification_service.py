# desktop_center/src/services/notification_service.py
import logging
import os
from plyer import notification
from src.services.config_service import ConfigService

class NotificationService:
    """
    负责管理和显示桌面弹窗通知的核心服务。
    此版本使用系统的原生通知功能，通过 'plyer' 库实现。
    """
    def __init__(self, app_name: str, app_icon: str, config_service: ConfigService, app_id: str = None):
        """
        初始化通知服务。

        Args:
            app_name (str): 应用程序的名称，将显示在通知中。
            app_icon (str): 指向应用程序图标文件的路径 (.ico for Windows)。
            config_service (ConfigService): 配置服务实例。
            app_id (str, optional): 应用程序的唯一ID (AUMID)，用于Windows通知。
        """
        self.app_name = app_name
        self.app_icon = app_icon
        self.config_service = config_service
        self.app_id = app_id
        logging.info(f"通知服务 (NotificationService) 初始化完成。App ID: {self.app_id}")

    def show(self, title: str, message: str, level: str = 'INFO'):
        """
        供所有插件调用的公共接口，用于显示一个系统原生通知。

        Args:
            title (str): 通知的标题。
            message (str): 通知的主体内容。
            level (str, optional): 通知的级别（暂未使用，为未来扩展保留）。
        """
        # 1. 检查全局配置是否允许弹窗
        if self.config_service.get_value("InfoService", "enable_desktop_popup", "true").lower() != 'true':
            logging.info("桌面通知被全局禁用，本次通知已忽略。")
            return

        # 2. 检查通知级别是否满足阈值 (未来可扩展)
        # ...

        # 3. 调用plyer发送通知
        try:
            # 确保图标文件存在
            icon_path = self.app_icon if os.path.exists(self.app_icon) else ''
            
            timeout_str = self.config_service.get_value("InfoService", "popup_timeout", "10")
            timeout = int(timeout_str) if timeout_str.isdigit() else 10
            
            # 【核心修复】在Windows上，plyer的 'app_name' 参数实际上被用作 AppUserModelID
            # 因此，我们传递 self.app_id 而不是 self.app_name
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_id or self.app_name, # 优先使用ID
                app_icon=icon_path,
                timeout=timeout
            )
            logging.info(f"已发送系统通知: title='{title}'")
        except Exception as e:
            # plyer在某些环境下（如无GUI的服务器或缺少依赖）可能会失败
            logging.error(f"发送系统通知时发生错误: {e}", exc_info=True)