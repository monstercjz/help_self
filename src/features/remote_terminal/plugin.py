from src.core.plugin_interface import IFeaturePlugin
from src.core.context import ApplicationContext
from src.features.remote_terminal.controllers.terminal_controller import TerminalController
from PySide6.QtWidgets import QWidget

class RemoteTerminalPlugin(IFeaturePlugin):
    """
    Plugin for the remote terminal feature.
    """
    def __init__(self):
        super().__init__()
        self.controller = None

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
        if not self.context:
            raise ValueError("Context not initialized for RemoteTerminalPlugin")
        self.controller = TerminalController(self.context)

    def get_page_widget(self) -> QWidget | None:
        """
        Returns the main widget for the terminal page.
        """
        if self.controller:
            return self.controller.get_view()
        return None

    def shutdown(self):
        """
        Handles plugin shutdown.
        """
        if self.controller:
            # Ensure the SSH connection is closed
            self.controller.service.disconnect()
        super().shutdown()
