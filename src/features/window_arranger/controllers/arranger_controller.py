# desktop_center/src/features/window_arranger/controllers/arranger_controller.py
import logging
import time
from datetime import datetime
from typing import List, Tuple, Dict, Callable, Set
import pygetwindow as gw
import psutil
import win32process
from PySide6.QtWidgets import QDialog, QApplication
from PySide6.QtCore import Signal, QObject, QRect
from src.core.context import ApplicationContext
from src.features.window_arranger.views.arranger_page_view import ArrangerPageView
from src.features.window_arranger.views.settings_dialog_view import SettingsDialog
from src.features.window_arranger.models.window_info import WindowInfo
from src.features.window_arranger.controllers.sorting_strategy_manager import SortingStrategyManager
from src.features.window_arranger.services.monitor_service import MonitorService

class ArrangerController(QObject):
    """
    【重构】负责窗口排列功能的业务逻辑。
    控制器现在主要负责UI交互和准备启动监控服务所需的数据。
    """
    def __init__(self, context: ApplicationContext, view: ArrangerPageView):
        super().__init__()
        self.context = context
        self.view = view
        self.detected_windows: list[WindowInfo] = []
        self.strategy_manager = SortingStrategyManager()
        self.monitor_service = MonitorService(self.context)

        # 连接主视图的信号
        self.view.detect_windows_requested.connect(self.detect_windows)
        self.view.open_settings_requested.connect(self.open_settings_dialog)
        self.view.toggle_monitoring_requested.connect(self.toggle_monitoring)
        self.view.arrange_grid_requested.connect(self.arrange_windows_grid)
        self.view.arrange_cascade_requested.connect(self.arrange_windows_cascade)
        
        # 连接后台服务的信号
        self.monitor_service.status_updated.connect(self.view.status_label.setText)
        # 【修复】连接MonitorService的finished信号，以在线程真正停止时更新UI
        self.monitor_service.finished.connect(self._on_monitor_thread_finished)

        self._load_filter_settings()
        self._initial_monitor_start()

    def _initial_monitor_start(self):
        """根据配置决定是否在启动时开启监控。"""
        if self.context.config_service.get_value("WindowArranger", "auto_monitor_enabled", "false") == 'true':
            self.view.monitor_toggle_button.setChecked(True)

    def toggle_monitoring(self, checked: bool):
        """【重构】启动或停止后台监控服务，并为其准备初始数据和依赖。"""
        self.context.config_service.set_option("WindowArranger", "auto_monitor_enabled", str(checked).lower())
        self.context.config_service.save_config()
        
        if checked:
            if not self.detected_windows:
                logging.warning("[WindowArranger] 未检测到窗口，无法启动监控。")
                self.view.set_monitoring_status(False)
                return
            
            if not self.monitor_service.isRunning():
                mode = self.context.config_service.get_value("WindowArranger", "monitor_mode", "template")
                position_map: Dict[int, Tuple[QRect, int, str]] = {} 
                
                # 获取当前选定的排序函数
                sorting_func = self._get_current_sorting_strategy().sort

                if mode == 'snapshot':
                    for win_info in self.detected_windows:
                        hwnd = win_info.pygw_window_obj._hWnd
                        rect = QRect(win_info.left, win_info.top, win_info.width, win_info.height)
                        position_map[hwnd] = (rect, win_info.pid, win_info.title) 
                else: # template mode
                    sorted_windows = sorting_func(self.detected_windows)
                    calculated_positions = self._calculate_grid_positions(sorted_windows)
                    for i, win_info in enumerate(sorted_windows):
                        if i < len(calculated_positions):
                            hwnd = win_info.pygw_window_obj._hWnd
                            x, y, w, h = calculated_positions[i]
                            position_map[hwnd] = (QRect(x, y, w, h), win_info.pid, win_info.title) 

                baseline_hwnds = set(position_map.keys())
                
                self.monitor_service.start_monitoring(
                    position_map=position_map,
                    baseline_hwnds=baseline_hwnds,
                    find_windows_func=self._find_and_filter_windows,
                    rearrange_logic_func=self._calculate_grid_positions,
                    sorting_func=sorting_func
                )
                # 【修复】启动时立即更新UI按钮状态为“启动中”
                self.view.set_monitoring_status(True)
        else:
            if self.monitor_service.isRunning():
                self.monitor_service.stop()
                # 【修复】停止时，不在此处立即将按钮设置为“停止”，等待finished信号
                # self.view.set_monitoring_status(False) # 旧代码，已移除

    def _on_monitor_thread_finished(self):
        """【新增】当MonitorService线程真正停止时，更新UI按钮状态。"""
        logging.info("[ArrangerController] MonitorService线程已结束，更新UI为停止状态。")
        self.view.set_monitoring_status(False)


    def _get_current_sorting_strategy(self) -> 'ISortStrategy':
        """辅助方法：根据配置获取当前的排序策略实例。"""
        strategy_name = self.context.config_service.get_value("WindowArranger", "sorting_strategy", "默认排序 (按标题)")
        strategy = self.strategy_manager.get_strategy(strategy_name)
        if not strategy:
            logging.error(f"未找到排序策略 '{strategy_name}'，将使用默认策略。")
            strategy = self.strategy_manager.get_strategy("默认排序 (按标题)")
            if not strategy: # 双重保险，确保至少有一个默认策略
                raise RuntimeError("无法加载任何排序策略，请检查配置和插件。")
        return strategy

    def open_settings_dialog(self):
        """打开设置对话框，并在保存后自动重新检测窗口。"""
        dialog = SettingsDialog(self.context, self.strategy_manager, self.view)
        
        if dialog.exec() == QDialog.Accepted:
            logging.info("[WindowArranger] 设置已保存，将自动重新检测窗口以应用新设置...")
            self.detect_windows(from_user_action=False)
        else:
            logging.info("[WindowArranger] 设置对话框已取消。")

    def _load_filter_settings(self):
        """从配置加载过滤相关的设置并更新主视图UI。"""
        config = self.context.config_service
        self.view.filter_keyword_input.setText(config.get_value("WindowArranger", "filter_keyword", ""))
        self.view.process_name_input.setText(config.get_value("WindowArranger", "process_name_filter", ""))
        self.view.exclude_title_input.setText(config.get_value("WindowArranger", "exclude_title_keywords", ""))

    def _save_settings_from_view(self):
        """仅保存主视图上的过滤相关设置。"""
        config = self.context.config_service
        config.set_option("WindowArranger", "filter_keyword", self.view.get_filter_keyword())
        config.set_option("WindowArranger", "process_name_filter", self.view.get_process_name_filter())
        config.set_option("WindowArranger", "exclude_title_keywords", self.view.get_exclude_keywords())
        config.save_config()
        
    def _show_notification_if_enabled(self, title: str, message: str):
        """
        【移除】此方法不再直接被调用，通知和推送由MonitorService统一管理。
        保留函数体，以防未来其他部分仍需调用，但功能上已废弃。
        """
        logging.warning(f"[_show_notification_if_enabled] 此方法已废弃，通知和推送由MonitorService统一管理。尝试通知: {title} - {message}")
        if self.context.config_service.get_value("WindowArranger", "enable_notifications", "true").lower() == 'true':
            self.context.notification_service.show(title=title, message=message)
    
    def detect_windows(self, from_user_action=True):
        """
        检测并过滤窗口，然后使用选定的策略进行排序。
        """
        logging.info("[WindowArranger] 正在检测窗口...")
        if from_user_action:
            self._save_settings_from_view()
            logging.info("[WindowArranger] 用户触发检测，过滤设置已保存。")
        
        unfiltered_windows = self._find_and_filter_windows()

        # 使用当前选定的排序策略对窗口进行排序
        strategy = self._get_current_sorting_strategy()
        self.detected_windows = strategy.sort(unfiltered_windows)
        
        num_detected = len(self.detected_windows)
        color_a, color_b, color_c = "#333", "#005a9e", "#5cb85c"
        summary_text = f"<span style='color: {color_a};'>检测结果 (</span><span style='color: {color_b}; font-weight: bold;'>{num_detected}</span><span style='color: {color_a};'> 个) | 排序: </span><span style='color: {color_c};'>{strategy.name}</span>"
        self.view.summary_label.setText(summary_text)
        
        self.view.update_detected_windows_list(self.detected_windows)
        self.view.status_label.setText("检测完成，准备排列。")

    def _find_and_filter_windows(self) -> List[WindowInfo]:
        """辅助方法，负责查找所有窗口并应用过滤规则。"""
        config = self.context.config_service
        title_kws = [kw.strip().lower() for kw in config.get_value("WindowArranger", "filter_keyword", "").split(',') if kw.strip()]
        proc_kws = [kw.strip().lower() for kw in config.get_value("WindowArranger", "process_name_filter", "").split(',') if kw.strip()]
        exclude_kws = [kw.strip().lower() for kw in config.get_value("WindowArranger", "exclude_title_keywords", "").split(',') if kw.strip()]
        
        # 即使没有UI（例如在服务内部调用），也要返回空列表而不是None
        if not title_kws and not proc_kws:
            # 只有在view存在时才显示通知和更新UI
            if self.view and hasattr(self.view, 'update_detected_windows_list'):
                self.view.update_detected_windows_list([])
                self.view.summary_label.setText("无有效过滤条件，请重新输入。")
            return []

        filtered_windows = []
        app_main_window_id = self.context.main_window.winId()
        
        for win in gw.getAllWindows():
            # 1. 过滤无效/隐藏/最小化/自身窗口
            if not (win.title and win.visible and not win.isMinimized and win._hWnd != app_main_window_id):
                continue
            
            title_lower = win.title.lower()
            # 2. 排除关键词过滤
            if exclude_kws and any(ex_kw in title_lower for ex_kw in exclude_kws):
                continue

            # 3. 标题关键词匹配
            title_match = not title_kws or any(kw in title_lower for kw in title_kws)
            
            # 4. 进程信息获取与匹配
            proc_name, pid = "[未知进程]", 0
            try:
                _, pid_val = win32process.GetWindowThreadProcessId(win._hWnd)
                if pid_val != 0:
                    pid = pid_val
                    process = psutil.Process(pid)
                    proc_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError): # 捕获可能的进程相关异常
                proc_name = f"[PID获取失败/权限不足-{pid_val}]" if pid_val else "[PID获取失败]"
                pid = 0 # 确保PID为0或无效
            except Exception as e:
                logging.debug(f"获取进程名失败 for window '{win.title}' (HWND:{win._hWnd}): {e}")
                proc_name = "[获取进程名失败]"
                pid = 0

            proc_name_lower = proc_name.lower()
            proc_match = not proc_kws or any(kw in proc_name_lower for kw in proc_kws)

            # 5. 最终匹配逻辑
            if (proc_kws and title_kws and proc_match and title_match) or \
               (proc_kws and not title_kws and proc_match) or \
               (title_kws and not proc_kws and title_match):
                filtered_windows.append(WindowInfo(
                    title=win.title, left=win.left, top=win.top, width=win.width, height=win.height,
                    process_name=proc_name, pid=pid, pygw_window_obj=win
                ))
        return filtered_windows

    def _arrange_windows(self, arrangement_logic) -> int:
        """通用排列逻辑，现在返回排列的窗口数。"""
        delay_ms = int(self.context.config_service.get_value("WindowArranger", "animation_delay", "50"))
        windows_to_arrange = self.view.get_selected_window_infos()
        if not windows_to_arrange:
            logging.warning("[WindowArranger] 未选择可排列的窗口。")
            return 0
        
        arranged_count = arrangement_logic(windows_to_arrange, delay_ms / 1000.0)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.status_label.setText(f"上次排列于 {timestamp} 完成 ({arranged_count} 个窗口)")
        if self.monitor_service.isRunning():
            # 手动排列后，通过MonitorService分发停止通知，然后更新UI
            self.monitor_service.stop() # MonitorService会发出停止通知
            # _on_monitor_thread_finished 会将按钮设置为停止状态
        
        return arranged_count

    def arrange_windows_grid(self):
        """将选定的窗口按网格布局排列。"""
        logging.info("[WindowArranger] 正在按网格排列...")
        count = self._arrange_windows(self._execute_grid_arrangement)
        if count > 0:
            # 手动排列成功后，发出一个事件通知
            self.monitor_service._dispatch_event(
                event_type="MANUAL_ARRANGE_COMPLETED",
                title="手动网格排列完成",
                message=f"已成功手动排列 {count} 个窗口。",
                level="INFO",
                details={"arranged_count": count, "type": "grid"}
            )

    def arrange_windows_cascade(self):
        """将选定的窗口按级联布局排列。"""
        logging.info("[WindowArranger] 正在按级联排列...")
        count = self._arrange_windows(self._execute_cascade_arrangement)
        if count > 0:
            # 手动排列成功后，发出一个事件通知
            self.monitor_service._dispatch_event(
                event_type="MANUAL_ARRANGE_COMPLETED",
                title="手动级联排列完成",
                message=f"已成功手动排列 {count} 个窗口。",
                level="INFO",
                details={"arranged_count": count, "type": "cascade"}
            )
    
    def _get_target_screen_geometry(self) -> QRect:
        """辅助方法，获取并返回目标屏幕的几何信息。"""
        config = self.context.config_service
        target_screen_index = int(config.get_value("WindowArranger", "target_screen_index", "0"))
        screens = self.context.app.screens()
        if not (0 <= target_screen_index < len(screens)):
            logging.warning(f"目标屏幕索引 {target_screen_index} 无效，将使用主屏幕。")
            return self.context.app.primaryScreen().geometry()
        return screens[target_screen_index].geometry()

    def _apply_window_transformations(self, windows: List[WindowInfo], positions: List[Tuple[int, int, int, int]], delay: float) -> int:
        """辅助方法，将计算好的位置和大小应用到窗口上。"""
        arranged_count = 0
        for i, window_info in enumerate(windows):
            if i >= len(positions): break
            x, y, w, h = positions[i]
            try:
                win_obj = window_info.pygw_window_obj
                win_obj.restore()
                win_obj.moveTo(int(x), int(y))
                win_obj.resizeTo(int(w), int(h))
                arranged_count += 1
                if delay > 0:
                    QApplication.processEvents()
                    time.sleep(delay)
            except Exception as e:
                logging.error(f"排列窗口 '{window_info.title}' 失败: {e}", exc_info=True)
        return arranged_count
    
    def _calculate_grid_positions(self, windows: List[WindowInfo]) -> List[Tuple[int, int, int, int]]:
        """仅计算网格位置，不应用。"""
        config = self.context.config_service
        rows = int(config.get_value("WindowArranger", "grid_rows", "2")); cols = int(config.get_value("WindowArranger", "grid_cols", "3"))
        margin_t = int(config.get_value("WindowArranger", "grid_margin_top", "0")); margin_b = int(config.get_value("WindowArranger", "grid_margin_bottom", "0"))
        margin_l = int(config.get_value("WindowArranger", "grid_margin_left", "0")); margin_r = int(config.get_value("WindowArranger", "grid_margin_right", "0"))
        spacing_h = int(config.get_value("WindowArranger", "grid_spacing_h", "10")); spacing_v = int(config.get_value("WindowArranger", "grid_spacing_v", "10"))
        direction = config.get_value("WindowArranger", "grid_direction", "row-major")
        
        screen = self._get_target_screen_geometry()
        
        available_w = screen.width() - margin_l - margin_r - (cols - 1) * spacing_h
        available_h = screen.height() - margin_t - margin_b - (rows - 1) * spacing_v
        cell_w = max(100, available_w / cols if cols > 0 else 0)
        cell_h = max(100, available_h / rows if rows > 0 else 0)

        positions = []
        for i in range(len(windows)): # 这里遍历的顺序就是传入windows的顺序
            if i >= rows * cols: break
            row_idx, col_idx = (i // cols, i % cols) if direction == "row-major" else (i % rows, i // rows)
            x = screen.x() + margin_l + col_idx * (cell_w + spacing_h)
            y = screen.y() + margin_t + row_idx * (cell_h + spacing_v)
            positions.append((int(x), int(y), int(cell_w), int(cell_h)))
        return positions

    def _execute_grid_arrangement(self, windows: List[WindowInfo], delay: float) -> int:
        """执行网格排列的核心逻辑。"""
        positions = self._calculate_grid_positions(windows)
        return self._apply_window_transformations(windows, positions, delay)

    def _execute_cascade_arrangement(self, windows: List[WindowInfo], delay: float) -> int:
        """执行级联排列的核心逻辑。"""
        config = self.context.config_service
        x_offset = int(config.get_value("WindowArranger", "cascade_x_offset", "30"))
        y_offset = int(config.get_value("WindowArranger", "cascade_y_offset", "30"))
        
        screen = self._get_target_screen_geometry()
        base_w = max(300, min(int(screen.width() * 0.5), int(screen.width() * 0.8)))
        base_h = max(200, min(int(screen.height() * 0.5), int(screen.height() * 0.8)))
        
        positions = []
        for i in range(len(windows)):
            start_x, start_y = 20, 20
            curr_x, curr_y = start_x + (i * x_offset), start_y + (i * y_offset)
            
            if curr_x + base_w > screen.width() - 10: curr_x = start_x + ((curr_x + base_w - screen.width() + 10) % (screen.width() - base_w - start_x))
            if curr_y + base_h > screen.height() - 10: curr_y = start_y + ((curr_y + base_h - screen.height() + 10) % (screen.height() - base_h - start_y))
            
            x, y = screen.x() + curr_x, screen.y() + curr_y
            positions.append((int(x), int(y), int(base_w), int(base_h)))
            
        return self._apply_window_transformations(windows, positions, delay)

    def shutdown(self):
        """由插件的 shutdown 方法调用，确保后台线程被安全停止。"""
        if self.monitor_service.isRunning():
            self.monitor_service.stop()