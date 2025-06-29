# src/features/alert_center/services/alert_receiver.py
# (此文件内容与您提供的版本完全相同，仅是位置移动)
import logging
import json
from flask import Flask, request, jsonify
from PySide6.QtCore import QThread, Signal
from werkzeug.serving import make_server
from src.services.config_service import ConfigService
from src.services.database_service import DatabaseService

class AlertReceiverThread(QThread):
    new_alert_received = Signal(dict)
    
    def __init__(self, config_service: ConfigService, db_service: DatabaseService, host='0.0.0.0', port=5000):
        super().__init__()
        self.config_service = config_service
        self.db_service = db_service
        self.host = host
        self.port = port
        self.server = None
        self.running = True

        self.flask_app = Flask(__name__)
        self.flask_app.route('/alert', methods=['POST'])(self.handle_alert)

    def handle_alert(self):
        try:
            data = request.json
            if not data:
                return jsonify({"status": "error", "message": "Invalid JSON"}), 400
            
            logging.info(f"收到告警: {data}")
            self.db_service.add_alert(data)
            self.new_alert_received.emit(data)
            
            return jsonify({"status": "success", "message": "Alert received"}), 200
        except Exception as e:
            logging.error(f"处理告警时发生错误: {e}", exc_info=True)
            return jsonify({"status": "error", "message": str(e)}), 500
            
    def run(self):
        logging.info(f"启动Web服务于 http://{self.host}:{self.port}")
        self.server = make_server(self.host, self.port, self.flask_app)
        self.server.serve_forever()

    def shutdown(self):
        if self.server:
            logging.info("正在关闭Web服务...")
            self.server.shutdown()

    def quit(self):
        self.shutdown()
        super().quit()