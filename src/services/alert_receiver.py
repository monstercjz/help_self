# src/services/alert_receiver.py
import logging
from PySide6.QtCore import QThread, Signal
from flask import Flask, request, jsonify

HOST = '0.0.0.0'
PORT = 5000

class AlertReceiverThread(QThread):
    """将Flask Web服务封装在Qt线程中"""
    new_alert = Signal(dict)

    def __init__(self):
        super().__init__()
        self.flask_app = Flask(__name__)
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        @self.flask_app.route('/alert', methods=['POST'])
        def receive_alert():
            try:
                client_ip = request.remote_addr
                data = request.get_json()
                alert_data = {
                    'ip': client_ip,
                    'type': data.get('type', 'Unknown'),
                    'message': data.get('message', 'N/A')
                }
                self.new_alert.emit(alert_data)
                return jsonify({"status": "success"}), 200
            except Exception as e:
                logging.error(f"Error in Flask route: {e}")
                return jsonify({"status": "error"}), 500

    def run(self):
        logging.info(f"Flask Web服务正在线程 {self.currentThreadId()} 中启动...")
        try:
            self.flask_app.run(host=HOST, port=PORT)
        except Exception as e:
            logging.error(f"Flask Web服务启动失败: {e}")

    def stop(self):
        logging.info("正在请求停止Web服务线程...")
        self.terminate()