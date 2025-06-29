# src/features/alert_center/services/alert_receiver.py (【最终修复版 - 完美复刻】)
import logging
from flask import Flask, request, jsonify
from PySide6.QtCore import QThread, Signal
from werkzeug.serving import make_server
from src.services.config_service import ConfigService
from src.services.database_service import DatabaseService
from threading import Thread

class ServerThread(Thread):
    def __init__(self, app, host, port):
        super().__init__()
        self.daemon = True
        self.server = make_server(host, port, app, threaded=True)

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

class AlertReceiverThread(QThread):
    new_alert_received = Signal(dict)
    
    def __init__(self, config_service: ConfigService, db_service: DatabaseService, host='0.0.0.0', port=5000):
        super().__init__()
        # 【注意】虽然传入了config_service，但在这个类中将不再使用它进行过滤
        self.config_service = config_service
        self.db_service = db_service
        self.host = host
        self.port = port
        self.server_thread = None
        
        self.flask_app = Flask(__name__)
        self.flask_app.add_url_rule('/alert', view_func=self.handle_alert, methods=['POST'])

    def handle_alert(self):
        try:
            data = request.json
            if not data:
                return jsonify({"status": "error", "message": "Invalid JSON"}), 400
            
            # 从请求中获取来源IP，并更新到data字典中
            source_ip = request.remote_addr
            data['source_ip'] = source_ip
            
            logging.info(f"收到告警 (来自 {source_ip}): {data}")
            
            # 1. 无条件存入数据库
            self.db_service.add_alert(data)
            
            # 2. 【核心修复】无条件发射信号给Controller，让Controller决定如何处理
            self.new_alert_received.emit(data)
            
            return jsonify({"status": "success", "message": "Alert received"}), 200
        except Exception as e:
            logging.error(f"处理告警时发生错误: {e}", exc_info=True)
            return jsonify({"status": "error", "message": str(e)}), 500
            
    def run(self):
        logging.info(f"启动Web服务于 http://{self.host}:{self.port}")
        self.server_thread = ServerThread(self.flask_app, self.host, self.port)
        self.server_thread.start()

    def quit(self):
        if self.server_thread:
            logging.info("正在关闭Web服务...")
            self.server_thread.shutdown()
        super().quit()