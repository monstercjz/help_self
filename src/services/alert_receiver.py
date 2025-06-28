# desktop_center/src/services/alert_receiver.py
import logging
import threading
from PySide6.QtCore import QThread, Signal
from flask import Flask, request, jsonify
from plyer import notification
from src.services.config_service import ConfigService
from src.services.database_service import DatabaseService

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

SEVERITY_LEVELS = {
    "INFO": 1,
    "WARNING": 2,
    "CRITICAL": 3
}

class AlertReceiverThread(QThread):
    """将Flask Web服务封装在Qt线程中。"""
    new_alert_received = Signal(dict)

    def __init__(self, config_service: ConfigService, db_service: DatabaseService, host='0.0.0.0', port=5000, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        self.db_service = db_service
        self.host = host
        self.port = port
        self.flask_app = Flask(__name__)
        self.flask_app.route('/alert', methods=['POST'])(self.receive_alert)

    def receive_alert(self):
        """处理告警请求的核心逻辑。"""
        try:
            client_ip = request.remote_addr
            data = request.get_json()
            if not data:
                logging.warning(f"Received invalid or empty JSON from {client_ip}")
                return jsonify({"status": "error", "message": "Invalid JSON"}), 400

            raw_severity = data.get('severity', 'INFO').upper()
            severity = raw_severity if raw_severity in SEVERITY_LEVELS else 'INFO'
            
            # 【核心修改】统一使用 'source_ip'作为键名
            alert_data = {
                'source_ip': client_ip,
                'type': data.get('type', 'Generic Alert'),
                'message': data.get('message', 'No message provided.'),
                'severity': severity
            }

            log_message = f"ALERT from {alert_data['source_ip']} | Severity: {alert_data['severity']} | Type: {alert_data['type']}"
            logging.info(log_message)

            # 将告警写入数据库
            self.db_service.add_alert(alert_data)
            logging.info(f"告警已存入数据库。")
            
            # 发射信号通知UI
            self.new_alert_received.emit(alert_data)
            # 触发桌面通知
            self.trigger_desktop_notification(alert_data)

            return jsonify({"status": "success", "message": "Alert received"}), 200

        except Exception as e:
            logging.error(f"处理告警请求时出错: {e}", exc_info=True)
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    def trigger_desktop_notification(self, alert_data: dict):
        """根据配置决定是否发送桌面通知。"""
        is_enabled = self.config_service.get_value("InfoService", "enable_desktop_popup", "false").lower() == 'true'
        if not is_enabled:
            return
            
        try:
            threshold_str = self.config_service.get_value("InfoService", "notification_level", "WARNING").upper()
            threshold_level = SEVERITY_LEVELS.get(threshold_str, SEVERITY_LEVELS["WARNING"])
            current_level = SEVERITY_LEVELS.get(alert_data['severity'], SEVERITY_LEVELS["INFO"])
            
            if current_level < threshold_level:
                logging.info(f"信息等级 '{alert_data['severity']}'低于阈值 '{threshold_str}'，已跳过弹窗通知。")
                return

            #【修改】使用正确的键名
            notification_title = f"[{alert_data['severity']}] 监控告警: {alert_data['source_ip']}"
            notification_message = f"类型: {alert_data['type']}\n详情: {alert_data['message']}"
            timeout = int(self.config_service.get_value("InfoService", "popup_timeout", 10))
            
            notification.notify(
                title=notification_title,
                message=notification_message,
                app_name="监控中心",
                timeout=timeout
            )
            logging.info("桌面弹窗通知 (plyer) 已发送。")
        except Exception as e:
            logging.error(f"发送桌面弹窗通知 (plyer) 失败: {e}")

    def run(self):
        """线程启动时执行的函数。"""
        try:
            thread_id = threading.get_ident()
            logging.info(f"Flask Web服务正在线程 {thread_id} 中启动，监听 {self.host}:{self.port}...")
            self.flask_app.run(host=self.host, port=self.port)
        except Exception as e:
            logging.error(f"Flask Web服务线程发生严重错误: {e}", exc_info=True)