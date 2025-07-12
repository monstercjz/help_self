# desktop_center/src/features/alert_center/services/alert_receiver.py
import logging
import threading
from PySide6.QtCore import QThread, Signal
from flask import Flask, request, jsonify

from src.services.config_service import ConfigService
from src.services.notification_service import NotificationService
from .alert_database_service import AlertDatabaseService

# 抑制Flask的常规日志输出，只保留错误信息
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

SEVERITY_LEVELS = {
    "INFO": 1,
    "WARNING": 2,
    "CRITICAL": 3
}

class AlertReceiverThread(QThread):
    """
    将Flask Web服务封装在Qt线程中，作为告警中心插件的私有服务。
    负责监听HTTP POST请求，接收告警，并将其转发给应用程序。
    """
    new_alert_received = Signal(dict)

    def __init__(self, config_service: ConfigService, db_service: AlertDatabaseService, notification_service: NotificationService, host: str, port: int, parent=None):
        """
        初始化告警接收器。

        Args:
            config_service (ConfigService): 配置服务。
            db_service (AlertDatabaseService): 告警数据库服务。
            notification_service (NotificationService): 通知服务。
            host (str): Flask服务监听的主机地址。
            port (int): Flask服务监听的端口。
            parent (QObject, optional): 父对象。
        """
        super().__init__(parent)
        self.config_service = config_service
        self.db_service = db_service
        self.notification_service = notification_service
        self.host = host
        self.port = port
        self.running = False
        
        self.flask_app = Flask(__name__)
        self.flask_app.route('/alert', methods=['POST'])(self.receive_alert)

    def receive_alert(self):
        """处理/alert端点的核心逻辑。"""
        try:
            client_ip = request.remote_addr
            data = request.get_json()
            if not data:
                logging.warning(f"Received invalid or empty JSON from {client_ip}")
                return jsonify({"status": "error", "message": "Invalid JSON"}), 400

            raw_severity = data.get('severity', 'INFO').upper()
            severity = raw_severity if raw_severity in SEVERITY_LEVELS else 'INFO'
            
            alert_data = {
                'source_ip': client_ip,
                'type': data.get('type', 'Generic Alert'),
                'message': data.get('message', 'No message provided.'),
                'severity': severity
            }

            log_message = f"ALERT from {alert_data['source_ip']} | Severity: {alert_data['severity']} | Type: {alert_data['type']}"
            logging.info(log_message)

            # 1. 将告警写入共享的数据库服务
            self.db_service.add_alert(alert_data)
            logging.info(f"告警已存入数据库。")
            
            # 2. 发射信号通知插件内部的控制器
            self.new_alert_received.emit(alert_data)
            
            # 3. 通过共享的通知服务触发桌面通知
            self.trigger_desktop_notification(alert_data)

            return jsonify({"status": "success", "message": "Alert received"}), 200

        except Exception as e:
            logging.error(f"处理告警请求时出错: {e}", exc_info=True)
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    def trigger_desktop_notification(self, alert_data: dict):
        """
        【核心重构点】
        通过平台共享的 NotificationService 发送桌面通知。
        不再直接调用 plyer，将通知逻辑与平台统一。
        """
        # 检查通知级别是否满足阈值
        try:
            threshold_str = self.config_service.get_value("InfoService", "notification_level", "WARNING").upper()
            threshold_level = SEVERITY_LEVELS.get(threshold_str, SEVERITY_LEVELS["WARNING"])
            current_level = SEVERITY_LEVELS.get(alert_data['severity'], SEVERITY_LEVELS["INFO"])
            
            if current_level < threshold_level:
                logging.info(f"信息等级 '{alert_data['severity']}' 低于阈值 '{threshold_str}'，已跳过弹窗通知。")
                return

            notification_title = f"[{alert_data['severity']}] 监控告警: {alert_data['source_ip']}"
            notification_message = f"类型: {alert_data['type']}\n详情: {alert_data['message']}"
            
            # 调用共享的通知服务
            self.notification_service.show(
                title=notification_title,
                message=notification_message,
                level=alert_data['severity']
            )
        except Exception as e:
            # 错误日志已在 NotificationService 内部记录，此处仅记录上下文
            logging.error(f"调用共享通知服务时发生错误: {e}")

    def run(self):
        """线程启动时执行的函数。"""
        self.running = True
        try:
            thread_id = threading.get_ident()
            logging.info(f"Flask Web服务正在线程 {thread_id} 中启动，监听 {self.host}:{self.port}...")
            # 在生产环境中，建议使用 waitress 或 gunicorn 等WSGI服务器
            self.flask_app.run(host=self.host, port=self.port, debug=False)
        except Exception as e:
            # 捕获端口占用等启动错误
            logging.critical(f"Flask Web服务线程发生严重错误，可能无法启动: {e}", exc_info=True)
        finally:
            self.running = False
            logging.info("Flask Web服务线程已停止。")