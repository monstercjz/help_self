# desktop_center/src/features/window_arranger/services/monitor_service.py
import logging
import time
from datetime import datetime
import pygetwindow as gw
import win32process
import psutil
from PySide6.QtCore import QThread, Signal
from src.core.context import ApplicationContext
from src.features.window_arranger.models.window_info import WindowInfo

class MonitorService(QThread):
    """
    后台监控服务，用于自动检测窗口变化并执行排列。
    """
    status_updated = Signal(str)
    
    def __init__(self, context: ApplicationContext, parent=None):
        super().__init__(parent)
        self.context = context
        self.running = False
        self._expected_states = {} # {hWnd: {"rect": (l,t,w,h), "title": str}}

    def run(self):
        """线程主循环。"""
        self.running = True
        logging.info("[MonitorService] 自动监测服务已启动。")
        self.status_updated.emit("监控中...")

        while self.running:
            config = self.context.config_service
            interval = int(config.get_value("WindowArranger", "monitor_interval", "5"))
            time.sleep(interval)

            if not self.running: 
                break

            logging.debug("[MonitorService] 开始新一轮监测...")
            self._check_and_correct_windows()

        logging.info("[MonitorService] 自动监测服务已停止。")
        self.status_updated.emit("监控已停止")

    def stop(self):
        """停止线程循环。"""
        self.running = False
        logging.info("[MonitorService] 正在请求停止监测服务...")
        self.quit()
        self.wait(2000) # 等待线程优雅退出

    def update_expected_states(self, windows: list[WindowInfo]):
        """
        由外部（例如 ArrangerController）调用，以更新期望的窗口状态。
        这通常在一次完整的手动排列后调用。
        """
        self._expected_states.clear()
        for win_info in windows:
            win = win_info.pygw_window_obj
            self._expected_states[win._hWnd] = {
                "rect": (win.left, win.top, win.width, win.height),
                "title": win.title
            }
        logging.info(f"[MonitorService] 期望状态已更新，当前管理 {len(self._expected_states)} 个窗口。")
    
    def _check_and_correct_windows(self):
        """核心监测与校正逻辑。"""
        if not self._expected_states:
            logging.debug("[MonitorService] 期望状态为空，跳过本轮监测。")
            return

        current_windows_map = {win._hWnd: win for win in gw.getAllWindows() if win.title and win.visible}
        
        # 1. 检查已关闭的窗口
        closed_windows_hwnds = set(self._expected_states.keys()) - set(current_windows_map.keys())
        if closed_windows_hwnds:
            for hwnd in closed_windows_hwnds:
                title = self._expected_states[hwnd].get("title", f"hWnd={hwnd}")
                message = f"窗口 '{title}' 已关闭。"
                logging.info(f"[MonitorService] {message}")
                self._push_event("Window Closed", message, "WARNING")
            
            # 从期望状态中移除已关闭的窗口
            for hwnd in closed_windows_hwnds:
                del self._expected_states[hwnd]
            
            self.status_updated.emit(f"窗口关闭，剩余 {len(self._expected_states)} 个窗口受监控。")

        # 2. 检查位置或大小不匹配的窗口
        for hwnd, expected in list(self._expected_states.items()):
            if hwnd in current_windows_map:
                current_win = current_windows_map[hwnd]
                current_rect = (current_win.left, current_win.top, current_win.width, current_win.height)
                
                # 增加一个小的容差范围，避免因1像素的微小差异而误判
                if not self._is_rect_close(current_rect, expected["rect"]):
                    message = f"窗口 '{expected['title']}' 位置或大小已校正。"
                    logging.info(f"[MonitorService] {message} 从 {current_rect} -> {expected['rect']}")
                    self._push_event("Window Corrected", message, "INFO")
                    try:
                        current_win.restore()
                        l, t, w, h = expected["rect"]
                        current_win.moveTo(l, t)
                        current_win.resizeTo(w, h)
                        self.status_updated.emit(f"已校正窗口 '{expected['title']}'")
                    except Exception as e:
                        logging.error(f"校正窗口 '{expected['title']}' 失败: {e}")

    def _is_rect_close(self, rect1, rect2, tolerance=2):
        """比较两个矩形元组是否在容差范围内近似相等。"""
        return all(abs(a - b) <= tolerance for a, b in zip(rect1, rect2))

    def _push_event(self, event_type: str, message: str, severity: str):
        """构建并发送 Webhook 事件。"""
        config = self.context.config_service
        
        if config.get_value("WindowArranger", "enable_push", "false").lower() != 'true':
            return
            
        host = config.get_value("WindowArranger", "push_host").strip() or config.get_value("WebhookDefaults", "default_host", "127.0.0.1").strip()
        port = config.get_value("WindowArranger", "push_port").strip() or config.get_value("WebhookDefaults", "default_port", "5000").strip()
        path = config.get_value("WindowArranger", "push_path", "/alert").strip()
        
        url = f"http://{host}:{port}{path if path.startswith('/') else '/' + path}"
        
        payload = {
            "type": event_type,
            "message": message,
            "severity": severity,
            "source": "WindowArrangerPlugin",
            "timestamp": datetime.now().isoformat()
        }
        
        self.context.webhook_service.push(url, payload)