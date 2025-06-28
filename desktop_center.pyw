# -*- coding: utf-8 -*-
# desktop_center.pyw - 可扩展的桌面控制与监控中心

import sys
import logging
import queue
from PySide6.QtWidgets import (QApplication, QMainWindow, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QMenu)
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtGui import QAction, QIcon
from flask import Flask, request, jsonify
from pystray import MenuItem, Icon
from PIL import Image

# --- 全局配置 ---
LOG_FILE = 'desktop_center.log'
HOST = '0.0.0.0'
PORT = 5000

# --- 日志设置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8', mode='a'),
        logging.StreamHandler()
    ]
)

# --- 1. Web服务模块 (运行在独立线程) ---
class AlertReceiverThread(QThread):
    """将Flask Web服务封装在Qt线程中"""
    # 定义一个信号，当收到新告警时发射，参数是一个字典
    new_alert = Signal(dict)

    def __init__(self):
        super().__init__()
        self.flask_app = Flask(__name__)
        # 关闭Flask自带的冗余日志
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        @self.flask_app.route('/alert', methods=['POST'])
        def receive_alert():
            try:
                client_ip = request.remote_addr
                data = request.get_json()
                if not data:
                    logging.warning(f"Received invalid JSON from {client_ip}")
                    return jsonify({"status": "error", "message": "Invalid JSON"}), 400
                
                # 将告警数据和真实IP打包
                alert_data = {
                    'ip': client_ip,
                    'type': data.get('type', 'Unknown'),
                    'message': data.get('message', 'N/A')
                }
                # 发射信号，将数据传递给主UI线程
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
        # 实际生产中停止Flask服务需要更复杂的机制，此处为简化示例
        logging.info("正在请求停止Web服务线程...")
        self.terminate() # 强制终止线程

# --- 2. 主窗口UI ---
class MainWindow(QMainWindow):
    """主应用程序窗口，作为所有UI功能的容器"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("桌面控制与监控中心")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("icon.png"))

        # 创建一个表格来显示告警
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["时间", "来源IP", "详情"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.setCentralWidget(self.table)
        
    @Slot(dict)
    def add_alert_to_table(self, alert_data):
        """响应信号，将新告警添加到表格顶部"""
        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.table.insertRow(0)
        self.table.setItem(0, 0, QTableWidgetItem(now))
        self.table.setItem(0, 1, QTableWidgetItem(alert_data.get('ip')))
        self.table.setItem(0, 2, QTableWidgetItem(alert_data.get('message')))
        logging.info(f"UI已更新，新告警来自 {alert_data.get('ip')}")

    def closeEvent(self, event):
        """重写关闭事件，实现点击关闭按钮时隐藏窗口而不是退出程序"""
        event.ignore()
        self.hide()
        logging.info("主窗口已隐藏到后台。")

# --- 3. 主应用与系统托盘管理 ---
class MainApplication:
    def __init__(self):
        self.app = QApplication(sys.argv)
        # 设置关闭最后一个窗口时不退出应用
        self.app.setQuitOnLastWindowClosed(False)

        self.window = MainWindow()
        
        # --- 启动后台Web服务线程 ---
        self.receiver_thread = AlertReceiverThread()
        # 核心：将后台线程的 new_alert 信号连接到主窗口的 add_alert_to_table 槽函数
        self.receiver_thread.new_alert.connect(self.window.add_alert_to_table)
        self.receiver_thread.start()

        # --- 设置系统托盘图标 ---
        image = Image.open("icon.png")
        menu = (MenuItem('显示监控中心', self.show_window),
                MenuItem('退出', self.quit_app))
        self.tray_icon = Icon("DesktopCenter", image, "桌面控制与监控中心", menu)

    def run(self):
        logging.info("应用启动，启动系统托盘图标。")
        # pystray需要在自己的线程中运行
        self.tray_icon.run_detached()
        # 显示主窗口（也可以默认隐藏 self.window.hide()）
        self.show_window()
        # 启动Qt应用事件循环
        sys.exit(self.app.exec())

    def show_window(self):
        self.window.show()
        self.window.activateWindow()

    def quit_app(self):
        logging.info("正在退出应用程序...")
        self.receiver_thread.stop()
        self.tray_icon.stop()
        self.app.quit()

if __name__ == '__main__':
    main_app = MainApplication()
    main_app.run()