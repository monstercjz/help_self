# desktop_center/src/features/window_arranger/services/monitor_service.py
import logging
import time
from datetime import datetime
from typing import Dict, Tuple, Set, Callable, List
import pygetwindow as gw
from PySide6.QtCore import QThread, Signal, QRect, QCoreApplication
from src.core.context import ApplicationContext
from src.features.window_arranger.models.window_info import WindowInfo

class MonitorService(QThread):
    """
    【重构】后台监控服务，实现了更健壮和智能的窗口布局维护逻辑。
    引入了PID校验，并区分了“全局重排”和“单窗口归位”。
    """
    status_updated = Signal(str)
    
    def __init__(self, context: ApplicationContext, parent=None):
        super().__init__(parent)
        self.context = context
        self.running = False
        self.position_map: Dict[int, Tuple[QRect, int, str]] = {} # {HWND: (QRect, PID, Title)} 【修改】包含标题
        self.baseline_hwnds: Set[int] = set() # 用于模板模式判断窗口集变化
        
        # 依赖注入的回调函数
        self.find_windows_func: Callable[[], List[WindowInfo]] = None
        self.rearrange_logic_func: Callable[[List[WindowInfo]], List[Tuple[int, int, int, int]]] = None
        self.sorting_func: Callable[[List[WindowInfo]], List[WindowInfo]] = None 
        
        self.mode = "snapshot" # 默认模式

    def start_monitoring(self, 
                         position_map: Dict[int, Tuple[QRect, int, str]], # 【修改】包含标题
                         baseline_hwnds: Set[int], 
                         find_windows_func: Callable[[], List[WindowInfo]], 
                         rearrange_logic_func: Callable[[List[WindowInfo]], List[Tuple[int, int, int, int]]],
                         sorting_func: Callable[[List[WindowInfo]], List[WindowInfo]]): 
        """由控制器调用，以提供初始数据并启动线程。"""
        self.position_map = position_map
        self.baseline_hwnds = baseline_hwnds
        self.find_windows_func = find_windows_func
        self.rearrange_logic_func = rearrange_logic_func
        self.sorting_func = sorting_func 
        
        self.mode = self.context.config_service.get_value("WindowArranger", "monitor_mode", "template")
        self.start()
        # 初始状态报告
        self._dispatch_event(
            event_type="MONITOR_STARTED",
            title=f"监控已启动",
            message=f"自动监测服务已启动，模式: {self.mode.capitalize()}。",
            level="INFO",
            details={"initial_window_count": len(self.position_map)}
        )

    def run(self):
        """线程主循环。"""
        self.running = True
        logging.info(f"[MonitorService] 自动监测服务已启动 (模式: {self.mode})。")
        self.status_updated.emit(f"监控中 (模式: {self.mode.capitalize()})")

        while self.running:
            interval = int(self.context.config_service.get_value("WindowArranger", "monitor_interval", "5"))
            time.sleep(interval)

            if not self.running: 
                break

            logging.debug("[MonitorService] 开始新一轮监测...")
            try:
                self._check_and_correct_windows()
            except Exception as e:
                # 捕获线程内所有未处理异常，防止线程崩溃
                logging.critical(f"[MonitorService] 线程主循环发生未捕获异常: {e}", exc_info=True)


        logging.info("[MonitorService] 自动监测服务已停止。")
        self.status_updated.emit("监控已停止")
        self._dispatch_event(
            event_type="MONITOR_STOPPED",
            title=f"监控已停止",
            message=f"自动监测服务已停止运行。",
            level="INFO"
        )


    def stop(self):
        """停止线程循环。"""
        self.running = False
        logging.info("[MonitorService] 正在请求停止监测服务...")
        self.quit()
        self.wait(2000)

    def _dispatch_event(self, event_type: str, title: str, message: str, level: str, details: dict = None):
        """【新增】统一处理日志、桌面通知和 Webhook 推送。"""
        # 1. 构造完整的事件数据包
        event_data = {
            "event_type": event_type,
            "level": level,
            "title": title,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "mode": self.mode,
            "details": details if details is not None else {}
        }

        # 2. 日志记录
        log_level = getattr(logging, level.upper(), logging.INFO)
        logging.log(log_level, f"[{self.mode.capitalize()} - {event_type}] {title}: {message}")

        # 3. 桌面通知 (如果启用)
        if self.context.config_service.get_value("WindowArranger", "enable_notifications", "true").lower() == 'true':
            self.context.notification_service.show(
                title=f"桌面窗口 ({title})", 
                message=message
            )

        # 4. Webhook 推送 (如果启用)
        if self.context.config_service.get_value("WindowArranger", "enable_push", "false").lower() == 'true':
            host = self.context.config_service.get_value("WindowArranger", "push_host", "").strip() # 使用空字符串作为fallback，而不是None
            port_str = self.context.config_service.get_value("WindowArranger", "push_port", "").strip()
            path = self.context.config_service.get_value("WindowArranger", "push_path", "/alert").strip()
            
            # 使用 WebhookDefaults 作为 fallback
            if not host:
                host = self.context.config_service.get_value("WebhookDefaults", "default_host", "127.0.0.1").strip()
            if not port_str:
                port_str = self.context.config_service.get_value("WebhookDefaults", "default_port", "5000").strip()
            
            port = int(port_str) if port_str.isdigit() else 5000
            url = f"http://{host}:{port}{path if path.startswith('/') else '/' + path}"
            
            self.context.webhook_service.push(url, event_data) # 推送完整的事件数据

    def _check_and_correct_windows(self):
        """核心监测与校正逻辑。"""
        if not self.find_windows_func:
            logging.warning("[MonitorService] 窗口查找函数未设置，跳过监测。")
            self._dispatch_event(
                event_type="MONITOR_WARNING",
                title="监测警告",
                message="窗口查找函数未设置，无法执行监测。",
                level="WARNING"
            )
            return
            
        current_windows_raw = self.find_windows_func() # 获取原始（未排序）的窗口列表
        current_win_map = {win.pygw_window_obj._hWnd: win for win in current_windows_raw}
        current_hwnds = set(current_win_map.keys())

        if self.mode == 'template':
            self._execute_template_mode_check(current_hwnds, current_win_map, current_windows_raw)
        else: # snapshot mode
            self._execute_snapshot_mode_check(current_hwnds, current_win_map)

    def _execute_snapshot_mode_check(self, current_hwnds: Set[int], current_win_map: Dict[int, WindowInfo]):
        """执行快照模式的检查与恢复。"""
        # 遍历 position_map 的副本，因为可能在循环中修改 position_map
        hwnds_to_check = list(self.position_map.keys()) 

        for hwnd in hwnds_to_check:
            expected_rect, expected_pid, expected_title = self.position_map[hwnd] # 【修改】获取标题

            if hwnd not in current_hwnds:
                # 窗口已关闭：从快照中移除
                self._dispatch_event(
                    event_type="WINDOW_DISAPPEARED",
                    title=f"窗口 '{expected_title}' 已关闭",
                    message=f"快照模式下检测到窗口 '{expected_title}' (HWND:{hwnd}) 已关闭，从监控中移除。",
                    level="INFO",
                    details={"hwnd": hwnd, "title": expected_title, "pid": expected_pid}
                )
                del self.position_map[hwnd]
                continue
            
            # 窗口仍在，执行检查和恢复
            self._check_and_restore_single_window(current_win_map[hwnd], expected_rect, expected_pid)

    def _execute_template_mode_check(self, current_hwnds: Set[int], current_win_map: Dict[int, WindowInfo], current_windows_raw: List[WindowInfo]):
        """执行模板模式的检查，决定是重排还是归位。"""
        if current_hwnds != self.baseline_hwnds:
            # --- 1. 窗口集合发生变化，需要强制重排 ---
            removed_hwnds = self.baseline_hwnds - current_hwnds
            added_hwnds = current_hwnds - self.baseline_hwnds

            # 记录消失的窗口
            for hwnd in removed_hwnds:
                if hwnd in self.position_map: # 确保在旧的position_map中存在
                    _, _, title = self.position_map[hwnd]
                    self._dispatch_event(
                        event_type="WINDOW_DISAPPEARED",
                        title=f"窗口 '{title}' 消失",
                        message=f"模板模式下，检测到窗口 '{title}' (HWND:{hwnd}) 消失。",
                        level="INFO",
                        details={"hwnd": hwnd, "title": title}
                    )
            
            # 记录新增的窗口
            for hwnd in added_hwnds:
                if hwnd in current_win_map: # 确保在当前窗口中存在
                    title = current_win_map[hwnd].title
                    self._dispatch_event(
                        event_type="WINDOW_ADDED",
                        title=f"新窗口 '{title}' 加入",
                        message=f"模板模式下，检测到新窗口 '{title}' (HWND:{hwnd}) 加入。",
                        level="INFO",
                        details={"hwnd": hwnd, "title": title}
                    )

            self._dispatch_event(
                event_type="FORCE_REARRANGE",
                title=f"窗口集合变化，强制重排",
                message=f"检测到 {len(added_hwnds)} 个新增窗口，{len(removed_hwnds)} 个窗口消失，正在执行全面重排。",
                level="INFO",
                details={
                    "added_count": len(added_hwnds),
                    "removed_count": len(removed_hwnds),
                    "added_hwnds": list(added_hwnds),
                    "removed_hwnds": list(removed_hwnds)
                }
            )
            self._force_rearrange(current_windows_raw) # 传入原始未排序的窗口列表
        else:
            # --- 2. 窗口集合未变，只需检查归位 ---
            logging.debug("[Monitor-Template] 窗口集合未变，检查归位。")
            # 遍历基准句柄集合，确保只处理之前模板中存在的窗口
            for hwnd in self.baseline_hwnds:
                # 确保窗口当前仍存在且在 position_map 中有记录
                if hwnd in current_win_map and hwnd in self.position_map:
                    expected_rect, expected_pid, _ = self.position_map[hwnd] # 【修改】获取标题
                    self._check_and_restore_single_window(current_win_map[hwnd], expected_rect, expected_pid)

    def _force_rearrange(self, windows_raw: List[WindowInfo]):
        """模板模式下的强制重排逻辑，使用注入的排序和布局计算函数。"""
        if not self.rearrange_logic_func or not self.sorting_func:
            self._dispatch_event(
                event_type="REARRANGE_FAILED",
                title="强制重排失败",
                message="布局或排序函数未设置，无法执行重排。",
                level="ERROR"
            )
            return

        # 1. 应用注入的排序函数
        sorted_windows = self.sorting_func(windows_raw)
        
        # 2. 使用注入的布局计算函数获取理想位置
        new_positions = self.rearrange_logic_func(sorted_windows)
        
        # 3. 应用新布局
        self._apply_transformations_from_service(sorted_windows, new_positions)
        
        # 4. 重构position_map和baseline_hwnds
        self.position_map.clear()
        for i, win_info in enumerate(sorted_windows):
            if i < len(new_positions):
                hwnd = win_info.pygw_window_obj._hWnd
                x, y, w, h = new_positions[i]
                self.position_map[hwnd] = (QRect(x, y, w, h), win_info.pid, win_info.title) # 【修改】包含标题
        
        self.baseline_hwnds = set(self.position_map.keys())
        self.status_updated.emit("布局已自动重排")
        self._dispatch_event(
            event_type="REARRANGE_COMPLETED",
            title="布局重排完成",
            message=f"已成功重排 {len(sorted_windows)} 个窗口。",
            level="INFO",
            details={"arranged_count": len(sorted_windows)}
        )


    def _apply_transformations_from_service(self, windows: List[WindowInfo], positions: List[Tuple[int, int, int, int]]):
        """在服务内部实现应用窗口变换，以保持解耦。"""
        for i, window_info in enumerate(windows):
            if i >= len(positions): break
            x, y, w, h = positions[i]
            try:
                win_obj = window_info.pygw_window_obj
                win_obj.restore()
                win_obj.moveTo(int(x), int(y))
                win_obj.resizeTo(int(w), int(h))
                # 在非GUI线程中操作GUI，需要处理事件
                if QCoreApplication.instance(): 
                    QCoreApplication.processEvents()
            except Exception as e:
                self._dispatch_event(
                    event_type="APPLY_TRANSFORM_FAILED",
                    title=f"窗口 '{window_info.title}' 变换失败",
                    message=f"无法将窗口 '{window_info.title}' 移动到目标位置 ({x},{y},{w},{h})。错误: {e}",
                    level="ERROR",
                    details={"hwnd": window_info.pygw_window_obj._hWnd, "title": window_info.title, "error": str(e)}
                )

    def _check_and_restore_single_window(self, window_info: WindowInfo, expected_rect: QRect, expected_pid: int):
        """对单个窗口进行安全检查和恢复，被两种模式共用。"""
        win_obj = window_info.pygw_window_obj
        hwnd = win_obj._hWnd
        
        # 进程ID校验：防止句柄复用导致的操作错误
        if window_info.pid != expected_pid:
            self._dispatch_event(
                event_type="HANDLE_REUSED",
                title=f"句柄复用警告: '{window_info.title}'",
                message=f"检测到句柄复用 (HWND: {hwnd})。原进程(PID:{expected_pid})已关闭，新进程为 '{window_info.process_name}'(PID:{window_info.pid})。从监控中移除。",
                level="WARNING",
                details={"hwnd": hwnd, "new_title": window_info.title, "old_pid": expected_pid, "new_pid": window_info.pid}
            )
            # 从position_map中移除此项，因为它不再是“预期”的窗口
            del self.position_map[hwnd]
            # 如果是模板模式，也从baseline_hwnds中移除，防止再次尝试归位
            if self.mode == 'template':
                self.baseline_hwnds.discard(hwnd)
            return

        # 位置校验：如果位置偏离，则恢复
        current_rect = QRect(window_info.left, window_info.top, window_info.width, window_info.height)
        if not self._is_rect_close(current_rect, expected_rect):
            self._dispatch_event(
                event_type="WINDOW_MOVED",
                title=f"窗口 '{window_info.title}' 已移位",
                message=f"窗口 '{window_info.title}' (HWND:{hwnd}) 位置已偏离 ({current_rect.getRect()}), 正在恢复到期望位置 ({expected_rect.getRect()})。",
                level="INFO",
                details={"hwnd": hwnd, "title": window_info.title, "old_rect": current_rect.getRect(), "new_rect": expected_rect.getRect()}
            )
            try:
                win_obj.restore()
                win_obj.moveTo(expected_rect.left(), expected_rect.top())
                win_obj.resizeTo(expected_rect.width(), expected_rect.height())
                self.status_updated.emit(f"已校正: {window_info.title[:30]}...")
            except Exception as e:
                self._dispatch_event(
                    event_type="RESTORE_FAILED",
                    title=f"窗口 '{window_info.title}' 恢复失败",
                    message=f"尝试恢复窗口 '{window_info.title}' (HWND:{hwnd}) 失败: {e}",
                    level="ERROR",
                    details={"hwnd": hwnd, "title": window_info.title, "error": str(e)}
                )

    def _is_rect_close(self, rect1: QRect, rect2: QRect, tolerance=2):
        """比较两个矩形是否在容差范围内近似相等。"""
        return (abs(rect1.left() - rect2.left()) <= tolerance and
                abs(rect1.top() - rect2.top()) <= tolerance and
                abs(rect1.width() - rect2.width()) <= tolerance and
                abs(rect1.height() - rect2.height()) <= tolerance)