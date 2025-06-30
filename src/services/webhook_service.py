# desktop_center/src/services/webhook_service.py
import logging
import requests
from PySide6.QtCore import QObject, QRunnable, QThreadPool

class WebhookWorker(QRunnable):
    """
    一个在独立线程中发送 Webhook 请求的工作器，以避免阻塞调用方。
    """
    def __init__(self, url: str, payload: dict):
        super().__init__()
        self.url = url
        self.payload = payload

    def run(self):
        """执行 HTTP POST 请求。"""
        try:
            response = requests.post(self.url, json=self.payload, timeout=5)
            response.raise_for_status() # 如果状态码不是 2xx，则抛出异常
            logging.info(f"Webhook 已成功推送到 {self.url}，响应: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"推送 Webhook 到 {self.url} 失败: {e}")

class WebhookService(QObject):
    """
    平台级共享服务，用于异步发送 Webhook (HTTP POST) 请求。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_pool = QThreadPool()
        # 设置线程池的最大线程数，以防滥用
        self.thread_pool.setMaxThreadCount(5) 
        logging.info("Webhook 服务 (WebhookService) 初始化完成。")

    def push(self, url: str, payload: dict):
        """
        异步地将一个 JSON payload 推送到指定的 URL。
        
        Args:
            url (str): 目标 URL。
            payload (dict): 要作为 JSON 发送的数据。
        """
        if not url or not url.startswith(('http://', 'https://')):
            logging.warning(f"无效的 Webhook URL: '{url}'，推送已取消。")
            return
            
        worker = WebhookWorker(url, payload)
        self.thread_pool.start(worker)