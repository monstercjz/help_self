# desktop_center/src/core/plugin_interface.py
from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget
from .context import ApplicationContext

class IFeaturePlugin(ABC):
    """所有功能插件必须实现的接口。"""
    
    @abstractmethod
    def name(self) -> str:
        """返回插件的唯一名称，用于内部识别。"""
        pass

    @abstractmethod
    def display_name(self) -> str:
        """返回显示在UI上的名称（如导航栏标题）。"""
        pass
        
    @abstractmethod
    def load_priority(self) -> int:
        """
        【新增】返回插件的加载优先级。数字越小，优先级越高。
        例如：核心服务插件=0, 普通功能=100, 依赖其他插件的功能=200。
        """
        pass

    def initialize(self, context: ApplicationContext):
        self.context = context
        self.background_services = []
        self.page_widget = None

    def get_page_widget(self) -> QWidget | None:
        return self.page_widget

    def get_background_services(self) -> list:
        return self.background_services

    def shutdown(self):
        for service in self.background_services:
            if hasattr(service, 'running') and hasattr(service, 'quit'):
                if service.running:
                    service.running = False
                    service.quit()
                    service.wait(5000)