# src/features/ssh_client/plugin.py
from src.core.plugin_interface import IFeaturePlugin # 修正导入名称
from src.core.context import ApplicationContext # 修正导入名称
from PySide6.QtWidgets import QWidget
import logging

from .views import SshClientView
from .services import SshService
from .controllers import SshClientController

class SshClientPlugin(IFeaturePlugin): # 修正继承的接口名称
    """
    SSH客户端插件，实现IFeaturePlugin。
    """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ssh_service = None
        self.ssh_client_view = None
        self.ssh_client_controller = None

    def name(self) -> str:
        return "ssh_client"

    def display_name(self) -> str:
        return "SSH客户端"

    def load_priority(self) -> int:
        return 150 # 普通独立功能插件优先级

    def initialize(self, context: ApplicationContext): # 修正类型提示
        """
        插件初始化。
        """
        super().initialize(context) # 调用父类初始化
        self.logger.info("SSH客户端插件初始化中...")
        
        # 初始化服务
        self.ssh_service = SshService()
        
        # 初始化视图
        self.ssh_client_view = SshClientView()
        self.page_widget = self.ssh_client_view # 设置主页面widget

        # 初始化控制器
        self.ssh_client_controller = SshClientController(
            view=self.ssh_client_view,
            ssh_service=self.ssh_service,
            context=self.context
        )
        
        self.logger.info("SSH客户端插件初始化完成。")

    def shutdown(self):
        """
        插件关闭。
        """
        self.logger.info("SSH客户端插件关闭中...")
        # 关闭所有活跃的SSH会话
        # 关闭所有活跃的SSH会话
        # 遍历一个副本，因为在循环中可能会修改原始字典
        for session_id in list(self.ssh_client_controller.active_sessions.keys()):
            # 在插件关闭时，直接通过服务关闭会话，避免控制器层面的额外逻辑和潜在的KeyError
            if session_id in self.ssh_client_controller.active_sessions:
                self.logger.info(f"尝试关闭会话 {session_id} (插件关闭)。")
                self.ssh_service.close_session(session_id)
                # 控制器会通过信号机制自行处理active_sessions的移除，此处无需手动删除
                self.logger.info(f"会话 {session_id} 已请求关闭 (插件关闭)。")
            else:
                self.logger.warning(f"会话 {session_id} 在关闭插件时已不存在于活动会话列表中，跳过关闭。")
        
        # 清理资源
        if self.ssh_service:
            self.ssh_service.deleteLater()
        if self.ssh_client_view:
            self.ssh_client_view.deleteLater()
        if self.ssh_client_controller:
            self.ssh_client_controller.deleteLater()
        super().shutdown() # 调用父类关闭方法
        self.logger.info("SSH客户端插件关闭完成。")