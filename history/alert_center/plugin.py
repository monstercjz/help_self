# desktop_center/src/features/alert_center/plugin.py
import logging
from src.core.plugin_interface import IFeaturePlugin
from src.core.context import ApplicationContext
from .controllers.alerts_page_controller import AlertsPageController
from .services.alert_receiver import AlertReceiverThread

class AlertCenterPlugin(IFeaturePlugin):
    """
    【插件】告警中心。
    负责接收、展示、查询和分析外部系统发送的告警信息。
    """

    def name(self) -> str:
        return "alert_center"

    def display_name(self) -> str:
        return "告警中心"

    def load_priority(self) -> int:
        # 普通功能插件，使用标准优先级
        return 100

    def initialize(self, context: ApplicationContext):
        """
        初始化告警中心插件。
        1. 调用父类的initialize以保存上下文。
        2. 创建后台告警接收服务。
        3. 创建主页面的控制器，由控制器管理视图和模型。
        4. 将后台服务和主页面UI注册到平台。
        """
        super().initialize(context)
        logging.info(f"[{self.display_name()}] 插件开始初始化...")

        # 1. 初始化后台服务
        # 从配置中读取监听地址和端口，如果未配置，则使用默认值
        host = self.context.config_service.get_value("InfoService", "host", "0.0.0.0")
        port_str = self.context.config_service.get_value("InfoService", "port", "9527")
        try:
            port = int(port_str)
        except (ValueError, TypeError):
            logging.warning(f"[{self.display_name()}] 无效的端口配置 '{port_str}'，将使用默认端口 9527。")
            port = 9527
            
        self.alert_receiver = AlertReceiverThread(
            context=self.context,
            host=host,
            port=port
        )
        self.background_services.append(self.alert_receiver)
        logging.info(f"[{self.display_name()}] 后台告警接收服务准备就绪，监听地址：{host}:{port}。")

        # 2. 初始化主控制器
        # 控制器将负责创建和管理视图(View)和模型(Model)
        self.alerts_page_controller = AlertsPageController(self.context)
        
        # 3. 将新告警信号连接到主控制器的槽
        self.alert_receiver.new_alert_received.connect(self.alerts_page_controller.on_new_alert)
        logging.info(f"[{self.display_name()}] 新告警信号已连接到主页面控制器。")
        
        # 4. 设置插件的主UI页面
        self.page_widget = self.alerts_page_controller.get_view()
        logging.info(f"[{self.display_name()}] 插件初始化完成。")

    def shutdown(self):
        """
        安全关闭插件。
        父类的shutdown方法会处理后台服务的停止。
        """
        logging.info(f"[{self.display_name()}] 插件开始关闭...")
        super().shutdown()
        logging.info(f"[{self.display_name()}] 插件关闭完成。")