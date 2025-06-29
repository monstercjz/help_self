# desktop_center/src/core/plugin_interface.py
from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget
from .context import ApplicationContext

class IFeaturePlugin(ABC):
    """
    【文档化】所有功能插件必须实现的接口（契约）。

    这个接口定义了一个插件的基本行为和与平台核心交互的方式。
    平台核心通过这些方法来识别、加载、初始化和关闭插件。
    """
    
    @abstractmethod
    def name(self) -> str:
        """
        返回插件的唯一内部名称。

        这个名称用于日志记录、内部管理和插件间的唯一识别。
        它应该是简短、无空格的ASCII字符串，例如 "alert_center"。

        Returns:
            str: 插件的唯一标识符。
        """
        pass

    @abstractmethod
    def display_name(self) -> str:
        """
        返回插件在用户界面上显示的名称。

        这个名称将用于主窗口的导航栏、菜单项等面向用户的地方。
        它可以是任何UTF-8字符串，例如 "告警中心"。

        Returns:
            str: 插件的显示名称。
        """
        pass
        
    @abstractmethod
    def load_priority(self) -> int:
        """
        返回插件的加载优先级，数字越小，优先级越高。

        这个值决定了插件 `initialize` 方法的调用顺序。
        如果插件A依赖于插件B，则插件B的优先级应高于（即数值小于）插件A。

        建议使用以下范围：
        - 0-99: 核心服务型插件
        - 100-199: 普通独立功能插件
        - 200+: 依赖其他插件的功能插件

        Returns:
            int: 加载优先级。
        """
        pass

    def initialize(self, context: ApplicationContext):
        """
        初始化插件。

        平台核心在加载所有插件后会调用此方法。插件应该在这里：
        1. 保存 `context` 的引用，以便后续访问共享服务。
        2. 创建并准备其UI页面（如果需要）。
        3. 创建并准备其后台服务（如果需要）。
        4. 注册全局动作到 `ActionManager`。
        5. 连接到核心或其他服务的信号。

        Args:
            context (ApplicationContext): 包含所有共享服务和组件的应用上下文。
        """
        self.context = context
        self.background_services = []
        self.page_widget = None

    def get_page_widget(self) -> QWidget | None:
        """
        返回此插件的主UI页面控件实例。

        如果插件没有UI页面，应返回 `None`。
        返回的控件将被添加到主窗口的内容区域。

        Returns:
            QWidget | None: 插件的UI页面实例或None。
        """
        return self.page_widget

    def get_background_services(self) -> list:
        """
        返回此插件需要在后台运行的服务列表。

        这些服务通常是继承自 `QThread` 的对象。
        平台核心会自动调用每个服务的 `start()` 方法。

        Returns:
            list: 需要在后台运行的服务实例列表。
        """
        return self.background_services

    def shutdown(self):
        """
        在应用程序关闭时，安全地关闭插件。

        平台核心在退出前会调用此方法。插件应该在这里：
        1. 停止并等待所有后台线程结束。
        2. 断开所有信号连接。
        3. 释放所有持有的资源。

        默认实现会尝试优雅地停止 `get_background_services()` 返回的服务。
        如果插件有更复杂的关闭逻辑，应重写此方法。
        """
        for service in self.background_services:
            if hasattr(service, 'running') and hasattr(service, 'quit'):
                if service.running:
                    service.running = False
                    service.quit()
                    service.wait(5000)