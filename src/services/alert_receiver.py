# desktop_center/src/services/alert_receiver.py
import logging
import threading  # 导入Python内置的threading模块
from PySide6.QtCore import QThread, Signal
from flask import Flask, request, jsonify
from plyer import notification
from src.services.config_service import ConfigService

# 将Flask的日志级别调高，避免在控制台输出过多的HTTP请求信息
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

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

            alert_data = {
                'ip': client_ip,
                'type': data.get('type', 'Generic Alert'),
                'message': data.get('message', 'No message provided.')
            }

            log_message = f"ALERT from {client_ip} | Type: {alert_data['type']} | Message: {alert_data['message']}"
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

        try:
            notification_title = f"监控告警: {alert_data['ip']}"
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
        """线程启动时执行的函数。"""
        try:
            # 【最终修正】使用Python标准库 threading.get_ident() 来获取当前线程的唯一标识符。
            # 这是最健壮、跨平台且不受Qt版本变化影响的方式。
            thread_id = threading.get_ident()
            logging.info(f"Flask Web服务正在线程 {thread_id} 中启动，监听 {self.host}:{self.port}...")
            # 启动会阻塞线程的Flask服务
            self.flask_app.run(host=self.host, port=self.port)
        except Exception as e:
            # 捕获任何在线程中发生的错误，并记录下来，防止线程静默失败。
            logging.error(f"Flask Web服务线程发生严重错误: {e}", exc_info=True)