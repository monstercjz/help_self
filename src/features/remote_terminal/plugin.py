import logging
from src.core.plugin_interface import IFeaturePlugin
from src.core.context import ApplicationContext
from src.features.remote_terminal.controllers.terminal_controller import TerminalController
from src.features.remote_terminal.services.connection_db_service import ConnectionDBService
from src.services.generic_data_service import DataType
from PySide6.QtWidgets import QWidget

class RemoteTerminalPlugin(IFeaturePlugin):
    """
    Plugin for the remote terminal feature.
    """
    def __init__(self):
        super().__init__()
        self.controller = None
        self.db_service = None

    def name(self) -> str:
        return "remote_terminal"

    def display_name(self) -> str:
        return "远程终端"

    def load_priority(self) -> int:
        return 100

    def initialize(self, context: ApplicationContext):
        """
        Initializes the plugin by creating the controller.
        """
        super().initialize(context)
        logging.info(f"[{self.display_name()}] 插件开始初始化...")

        # 1. Initialize the database service using the global initializer
        generic_service = self.context.initializer.initialize(
            context=self.context,
            plugin_name=self.name(),
            config_section=self.name(),
            config_key="db_path",
            default_relative_path="plugins/remote_terminal/connections.db",
            data_type=DataType.SQLITE,
            db_service_class=ConnectionDBService
        )

        if not generic_service:
            logging.error(f"[{self.display_name()}] 插件因数据源错误无法加载。")
            return
        # self.db_service = generic_service.db_service
        self.db_service = generic_service.load_data()
        logging.info(f"[{self.display_name()}] 插件专属数据库服务已初始化。")

        # 2. Initialize the main controller
        self.controller = TerminalController(self.context, self.db_service, self.name())
        self.page_widget = self.controller.get_view()
        logging.info(f"[{self.display_name()}] 插件初始化完成。")


    def get_page_widget(self) -> QWidget | None:
        """
        Returns the main widget for the terminal page.
        """
        return self.page_widget

    def shutdown(self):
        """
        Handles plugin shutdown.
        """
        logging.info(f"[{self.display_name()}] 插件开始关闭...")
        if self.controller:
            self.controller.cleanup()
        if self.db_service:
            self.db_service.close()
            logging.info(f"[{self.display_name()}] 数据库服务已关闭。")
        super().shutdown()
        logging.info(f"[{self.display_name()}] 插件关闭完成。")
