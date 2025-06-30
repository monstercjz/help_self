# desktop_center/src/features/window_arranger/services/monitor_service.py
import logging
import time
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
        self.position_map: Dict[int, Tuple[QRect, int]] = {} # {HWND: (QRect, PID)}
        self.baseline_hwnds: Set[int] = set() # 用于模板模式判断窗口集变化
        
        # 依赖注入的回调函数
        self.find_windows_func: Callable[[], List[WindowInfo]] = None
        self.rearrange_logic_func: Callable[[List[WindowInfo]], List[Tuple[int, int, int, int]]] = None
        self.sorting_func: Callable[[List[WindowInfo]], List[WindowInfo]] = None # 【新增】排序回调函数
        
        self.mode = "snapshot" # 默认模式

    def start_monitoring(self, 
                         position_map: Dict[int, Tuple[QRect, int]], 
                         baseline_hwnds: Set[int], 
                         find_windows_func: Callable[[], List[WindowInfo]], 
                         rearrange_logic_func: Callable[[List[WindowInfo]], List[Tuple[int, int, int, int]]],
                         sorting_func: Callable[[List[WindowInfo]], List[WindowInfo]]): # 【新增】排序函数参数
        """由控制器调用，以提供初始数据并启动线程。"""
        self.position_map = position_map
        self.baseline_hwnds = baseline_hwnds
        self.find_windows_func = find_windows_func
        self.rearrange_logic_func = rearrange_logic_func
        self.sorting_func = sorting_func # 【新增】存储排序函数
        
        self.mode = self.context.config_service.get_value("WindowArranger", "monitor_mode", "template")
        self.start()

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

    def stop(self):
        """停止线程循环。"""
        self.running = False
        logging.info("[MonitorService] 正在请求停止监测服务...")
        self.quit()
        self.wait(2000)

    def _check_and_correct_windows(self):
        """核心监测与校正逻辑。"""
        if not self.find_windows_func:
            logging.warning("[MonitorService] 窗口查找函数未设置，跳过监测。")
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
            # 检查窗口是否仍然在当前活动窗口中
            if hwnd not in current_hwnds:
                # 窗口已关闭：从快照中移除
                logging.info(f"[Monitor-Snapshot] 窗口已关闭 (HWND: {hwnd})。从快照中移除。")
                # TODO: 记录和推送“窗口销毁”事件
                del self.position_map[hwnd]
                continue
            
            # 窗口仍在，执行检查和恢复
            expected_rect, expected_pid = self.position_map[hwnd]
            self._check_and_restore_single_window(current_win_map[hwnd], expected_rect, expected_pid)

    def _execute_template_mode_check(self, current_hwnds: Set[int], current_win_map: Dict[int, WindowInfo], current_windows_raw: List[WindowInfo]):
        """执行模板模式的检查，决定是重排还是归位。"""
        if current_hwnds != self.baseline_hwnds:
            # --- 1. 窗口集合发生变化，需要强制重排 ---
            logging.info("[Monitor-Template] 窗口集合发生变化，执行强制重排。")
            # TODO: 记录和推送“窗口集变化”事件
            self._force_rearrange(current_windows_raw) # 传入原始未排序的窗口列表
        else:
            # --- 2. 窗口集合未变，只需检查归位 ---
            logging.debug("[Monitor-Template] 窗口集合未变，检查归位。")
            # 遍历基准句柄集合，确保只处理之前模板中存在的窗口
            for hwnd in self.baseline_hwnds:
                # 确保窗口当前仍存在且在 position_map 中有记录
                if hwnd in current_win_map and hwnd in self.position_map:
                    expected_rect, expected_pid = self.position_map[hwnd]
                    self._check_and_restore_single_window(current_win_map[hwnd], expected_rect, expected_pid)

    def _force_rearrange(self, windows_raw: List[WindowInfo]):
        """【修复】模板模式下的强制重排逻辑，使用注入的排序和布局计算函数。"""
        if not self.rearrange_logic_func or not self.sorting_func:
            logging.error("[MonitorService] 布局或排序函数未设置，重排失败。")
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
                self.position_map[hwnd] = (QRect(x, y, w, h), win_info.pid)
        
        self.baseline_hwnds = set(self.position_map.keys())
        self.status_updated.emit("布局已自动重排")

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
                if QCoreApplication.instance(): # 确保QApplication实例存在
                    QCoreApplication.processEvents()
            except Exception as e:
                logging.error(f"[MonitorService] 应用窗口变换失败 for '{window_info.title}' (HWND:{window_info.pygw_window_obj._hWnd}): {e}", exc_info=True)


    def _check_and_restore_single_window(self, window_info: WindowInfo, expected_rect: QRect, expected_pid: int):
        """对单个窗口进行安全检查和恢复，被两种模式共用。"""
        win_obj = window_info.pygw_window_obj
        hwnd = win_obj._hWnd
        
        # 进程ID校验：防止句柄复用导致的操作错误
        if window_info.pid != expected_pid:
            logging.warning(f"[Monitor-Safety] 检测到句柄复用 (HWND: {hwnd})。原进程(PID:{expected_pid})已关闭，新进程为 '{window_info.process_name}'(PID:{window_info.pid})。")
            # 从position_map中移除此项，因为它不再是“预期”的窗口
            del self.position_map[hwnd]
            # 如果是模板模式，也从baseline_hwnds中移除，防止再次尝试归位
            if self.mode == 'template':
                self.baseline_hwnds.discard(hwnd)
            # TODO: 记录和推送“句柄复用/窗口已替换”严重警告事件
            return

        # 位置校验：如果位置偏离，则恢复
        current_rect = QRect(window_info.left, window_info.top, window_info.width, window_info.height)
        if not self._is_rect_close(current_rect, expected_rect):
            logging.info(f"[Monitor] 窗口 '{window_info.title}' 位置已偏离，正在恢复...")
            # TODO: 记录和推送“窗口移位”事件
            try:
                win_obj.restore()
                win_obj.moveTo(expected_rect.left(), expected_rect.top())
                win_obj.resizeTo(expected_rect.width(), expected_rect.height())
                self.status_updated.emit(f"已校正: {window_info.title[:30]}...")
            except Exception as e:
                logging.error(f"恢复窗口 '{window_info.title}' 位置时失败: {e}", exc_info=True)

    def _is_rect_close(self, rect1: QRect, rect2: QRect, tolerance=2):
        """比较两个矩形是否在容差范围内近似相等。"""
        return (abs(rect1.left() - rect2.left()) <= tolerance and
                abs(rect1.top() - rect2.top()) <= tolerance and
                abs(rect1.width() - rect2.width()) <= tolerance and
                abs(rect1.height() - rect2.height()) <= tolerance)