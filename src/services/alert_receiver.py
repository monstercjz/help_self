# desktop_center/src/services/alert_receiver.py
import logging
import threading
from PySide6.QtCore import QThread, Signal
from flask import Flask, request, jsonify
from plyer import notification
from src.services.config_service import ConfigService

# 将Flask的日志级别调高，避免在控制台输出过多的HTTP请求信息
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# 【新增】定义严重等级及其排序，便于比较
SEVERITY_LEVELS = {
    "INFO": 1,
    "WARNING": 2,
    "CRITICAL": 3
}

class AlertReceiverThread(QThread):
    """
    将Flask Web服务封装在Qt线程中，用于接收外部告警。
    通过Qt信号与主UI线程通信，并可选地触发桌面弹窗通知。
    """
    new_alert_received = Signal(dict)

    def __init__(self, config_service: ConfigService, host='0.0.0.0', port=5000, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        self.host = host
        self.port = port
        self.flask_app = Flask(__name__)
        self.flask_app.route('/alert', methods=['POST'])(self.receive_alert)

    def receive_alert(self):
        try:
            client_ip = request.remote_addr
            data = request.get_json()
            if not data:
                logging.warning(f"Received invalid or empty JSON from {client_ip}")
                return jsonify({"status": "error", "message": "Invalid JSON"}), 400

            # 【修改】引入严重等级解析逻辑
            # 1. 从JSON中获取severity，并转为大写以便比较
            raw_severity = data.get('severity', 'INFO').upper()
            # 2. 如果获取到的值不在我们定义的等级中，则默认为INFO
            severity = raw_severity if raw_severity in SEVERITY_LEVELS else 'INFO'
            
            alert_data = {
                'ip': client_ip,
                'type': data.get('type', 'Generic Alert'),
                'message': data.get('message', 'No message provided.'),
                'severity': severity  # 将解析后的等级添加到数据包中
            }

            log_message = f"ALERT from {client_ip} | Severity: {alert_data['severity']} | Type: {alert_data['type']} | Message: {alert_data['message']}"
            logging.info(log_message)
            
            self.new_alert_received.emit(alert_data)
            self.trigger_desktop_notification(alert_data)

            return jsonify({"status": "success", "message": "Alert received"}), 200

        except Exception as e:
            logging.error(f"处理告警请求时出错: {e}", exc_info=True)
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    def trigger_desktop_notification(self, alert_data: dict):
        is_enabled = self.config_service.get_value("Notification", "enable_desktop_popup", "false").lower() == 'true'
        
        if not is_enabled:
            return
            
        # 【修改】实现智能通知，检查等级是否满足阈值
        try:
            # 从配置中获取通知阈值等级，默认为WARNING
            threshold_str = self.config_service.get_value("Notification", "notification_level", "WARNING").upper()
            threshold_level = SEVERITY_LEVELS.get(threshold_str, SEVERITY_LEVELS["WARNING"])
            
            # 获取当前信息的等级
            current_level = SEVERITY_LEVELS.get(alert_data['severity'], SEVERITY_LEVELS["INFO"])
            
            # 只有当前等级大于或等于阈值时才发送通知
            if current_level < threshold_level:
                logging.info(f"信息等级 '{alert_data['severity']}'低于阈值 '{threshold_str}'，已跳过弹窗通知。")
                return

            notification_title = f"[{alert_data['severity']}] 监控告警: {alert_data['ip']}"
            notification_message = f"类型: {alert_data['type']}\n详情: {alert_data['message']}"
            timeout = int(self.config_service.get_value("Notification", "popup_timeout", 10))
            
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
        try:
            thread_id = threading.get_ident()
            logging.info(f"Flask Web服务正在线程 {thread_id} 中启动，监听 {self.host}:{self.port}...")
            self.flask_app.run(host=self.host, port=self.port)
        except Exception as e:
            logging.error(f"Flask Web服务线程发生严重错误: {e}", exc_info=True)