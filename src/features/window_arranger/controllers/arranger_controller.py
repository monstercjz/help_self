# desktop_center/src/features/window_arranger/controllers/arranger_controller.py
import logging
import time
from datetime import datetime
import math
import pygetwindow as gw
import psutil
import win32process
from PySide6.QtWidgets import QDialog, QApplication
from src.core.context import ApplicationContext
from src.features.window_arranger.views.arranger_page_view import ArrangerPageView
from src.features.window_arranger.views.settings_dialog_view import SettingsDialog
from src.features.window_arranger.models.window_info import WindowInfo
from src.features.window_arranger.controllers.sorting_strategy_manager import SortingStrategyManager
from src.features.window_arranger.services.monitor_service import MonitorService
from PySide6.QtGui import QScreen

class ArrangerController:
    """
    负责窗口排列功能的业务逻辑。
    """
    def __init__(self, context: ApplicationContext, view: ArrangerPageView):
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

        self._load_filter_settings()
        self._initial_monitor_start()

    def _initial_monitor_start(self):
        """根据配置决定是否在启动时开启监控。"""
        if self.context.config_service.get_value("WindowArranger", "auto_monitor_enabled", "false") == 'true':
            self.view.monitor_toggle_button.setChecked(True)

    def toggle_monitoring(self, checked: bool):
        """启动或停止后台监控服务。"""
        self.context.config_service.set_option("WindowArranger", "auto_monitor_enabled", str(checked).lower())
        self.context.config_service.save_config()
        
        if checked:
            # 【修复】在启动监控前，强制执行一次最新的检测，以确保窗口列表有效
            logging.info("[WindowArranger] 启动监控前，正在刷新窗口列表...")
            self.detect_windows()
            
            # 检查检测后是否有可监控的窗口
            if not self.detected_windows:
                self._show_notification_if_enabled("无法启动监控", "未检测到任何符合条件的窗口。")
                self.view.set_monitoring_status(False)
                return
            
            if not self.monitor_service.isRunning():
                # 使用刚刚刷新过的、最新的窗口列表来更新期望状态
                self.monitor_service.update_expected_states(self.detected_windows)
                self.monitor_service.start()
        else:
            if self.monitor_service.isRunning():
                self.monitor_service.stop()
        
        # 确保UI状态与实际服务状态一致
        self.view.set_monitoring_status(self.monitor_service.isRunning())

    def open_settings_dialog(self):
        """打开设置对话框，并在保存后自动重新检测窗口。"""
        dialog = SettingsDialog(self.context, self.strategy_manager, self.view)
        
        if dialog.exec() == QDialog.Accepted:
            logging.info("[WindowArranger] 设置已保存，将自动重新检测窗口以应用新设置...")
            self.detect_windows()
        else:
            logging.info("[WindowArranger] 设置对话框已取消，未做任何更改。")

    def _load_filter_settings(self):
        """从配置加载过滤相关的设置并更新主视图UI。"""
        config = self.context.config_service
        self.view.filter_keyword_input.setText(config.get_value("WindowArranger", "filter_keyword", "完全控制"))
        self.view.process_name_input.setText(config.get_value("WindowArranger", "process_name_filter", ""))
        self.view.exclude_title_input.setText(config.get_value("WindowArranger", "exclude_title_keywords", "Radmin Viewer"))
        logging.info("[WindowArranger] 过滤设置已加载到主视图。")

    def _save_settings_from_view(self):
        """仅保存主视图上的过滤相关设置。"""
        filter_keyword = self.view.get_filter_keyword()
        process_name_filter = self.view.get_process_name_filter()
        exclude_keywords = self.view.get_exclude_keywords()
        
        config = self.context.config_service
        config.set_option("WindowArranger", "filter_keyword", filter_keyword)
        config.set_option("WindowArranger", "process_name_filter", process_name_filter)
        config.set_option("WindowArranger", "exclude_title_keywords", exclude_keywords)
        config.save_config()
        logging.info("[WindowArranger] 过滤设置已保存。")
        
    def _show_notification_if_enabled(self, title: str, message: str):
        """如果配置允许，则显示通知。"""
        if self.context.config_service.get_value("WindowArranger", "enable_notifications", "true") == 'true':
            self.context.notification_service.show(title=title, message=message)
    
    def detect_windows(self):
        """检测并使用选定的策略对窗口进行排序。"""
        logging.info("[WindowArranger] 正在检测窗口...")
        self._save_settings_from_view()
        
        config = self.context.config_service
        title_keyword_str = config.get_value("WindowArranger", "filter_keyword", "")
        process_keyword_str = config.get_value("WindowArranger", "process_name_filter", "")
        exclude_keywords_str = config.get_value("WindowArranger", "exclude_title_keywords", "")
        
        title_keywords = [kw.strip().lower() for kw in title_keyword_str.split(',') if kw.strip()]
        process_keywords = [kw.strip().lower() for kw in process_keyword_str.split(',') if kw.strip()]
        exclude_keywords_list = [kw.strip().lower() for kw in exclude_keywords_str.split(',') if kw.strip()]
        
        if not title_keywords and not process_keywords:
            self._show_notification_if_enabled(title="检测失败", message="请输入窗口标题关键词或进程名称进行过滤。")
            self.view.update_detected_windows_list([])
            self.view.summary_label.setText("无有效过滤条件，请重新输入。")
            return

        all_windows = gw.getAllWindows()
        unfiltered_windows = []
        app_main_window_id = self.context.main_window.winId()
        
        for win in all_windows:
            if not (win.title and win.visible and not win.isMinimized and win._hWnd != app_main_window_id):
                continue
            
            current_window_title = win.title
            if exclude_keywords_list and any(ex_kw in current_window_title.lower() for ex_kw in exclude_keywords_list):
                continue
            
            is_title_match = not title_keywords or any(kw in current_window_title.lower() for kw in title_keywords)
            
            current_process_name = "[未知进程]"
            is_process_match = not process_keywords
            if process_keywords:
                try:
                    thread_id, pid = win32process.GetWindowThreadProcessId(win._hWnd)
                    if pid != 0:
                        process = psutil.Process(pid)
                        current_process_name = process.name()
                        if any(kw in current_process_name.lower() for kw in process_keywords):
                            is_process_match = True
                        else:
                            is_process_match = False
                except Exception:
                    is_process_match = False
            
            should_add = False
            if process_keywords and title_keywords:
                should_add = is_process_match and is_title_match
            elif process_keywords:
                should_add = is_process_match
            elif title_keywords:
                should_add = is_title_match
            
            if should_add:
                unfiltered_windows.append(WindowInfo(
                    title=win.title, left=win.left, top=win.top,
                    width=win.width, height=win.height,
                    process_name=current_process_name, pygw_window_obj=win
                ))

        strategy_name = config.get_value("WindowArranger", "sorting_strategy", "默认排序 (按标题)")
        strategy = self.strategy_manager.get_strategy(strategy_name)
        if not strategy:
            logging.error(f"未找到排序策略 '{strategy_name}'，将使用默认策略。")
            default_strategy = self.strategy_manager.get_strategy("默认排序 (按标题)")
            if default_strategy:
                strategy = default_strategy
            else:
                self.detected_windows = unfiltered_windows
                self.view.update_detected_windows_list(self.detected_windows)
                self._show_notification_if_enabled(title="排序失败", message="无法加载任何排序策略。")
                return

        self.detected_windows = strategy.sort(unfiltered_windows)
        
        num_detected = len(self.detected_windows)
        color_a = "#333"
        color_b = "#005a9e"
        color_c = "#5cb85c"
        summary_text = (
            f"<span style='color: {color_a};'>检测结果 (</span>"
            f"<span style='color: {color_b}; font-weight: bold;'>{num_detected}</span>"
            f"<span style='color: {color_a};'> 个) | 排序: </span>"
            f"<span style='color: {color_c};'>{strategy_name}</span>"
        )
        self.view.summary_label.setText(summary_text)
        
        self.view.update_detected_windows_list(self.detected_windows)
        self._show_notification_if_enabled(title="窗口检测完成", message=f"已检测到 {num_detected} 个符合条件的窗口。")
        self.view.status_label.setText("检测完成，准备排列。")

    def _arrange_windows(self, arrange_function):
        """通用排列逻辑，包含延时和状态更新。"""
        config = self.context.config_service
        delay_ms = int(config.get_value("WindowArranger", "animation_delay", "50"))
        delay_s = delay_ms / 1000.0

        windows_to_arrange = self.view.get_selected_window_infos()
        if not windows_to_arrange:
            self._show_notification_if_enabled(title="窗口排列失败", message="没有选择可排列的窗口。")
            return
        
        arranged_count = arrange_function(windows_to_arrange, delay_s)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.status_label.setText(f"上次排列于 {timestamp} 完成 ({arranged_count} 个窗口)")

        # 在手动排列后，如果监控服务正在运行，则用最新的排列结果更新其期望状态
        if self.monitor_service.isRunning():
            self.monitor_service.update_expected_states(windows_to_arrange)
        
        return arranged_count

    def arrange_windows_grid(self):
        """将选定的窗口按网格布局排列。"""
        logging.info(f"[WindowArranger] 正在按网格排列...")
        
        def do_grid_arrangement(windows, delay):
            config = self.context.config_service
            rows = int(config.get_value("WindowArranger", "grid_rows", "2"))
            cols = int(config.get_value("WindowArranger", "grid_cols", "3"))
            margin_top = int(config.get_value("WindowArranger", "grid_margin_top", "0"))
            margin_bottom = int(config.get_value("WindowArranger", "grid_margin_bottom", "0"))
            margin_left = int(config.get_value("WindowArranger", "grid_margin_left", "0"))
            margin_right = int(config.get_value("WindowArranger", "grid_margin_right", "0"))
            spacing_h = int(config.get_value("WindowArranger", "grid_spacing_h", "10"))
            spacing_v = int(config.get_value("WindowArranger", "grid_spacing_v", "10"))
            grid_direction = config.get_value("WindowArranger", "grid_direction", "row-major")
            target_screen_index = int(config.get_value("WindowArranger", "target_screen_index", "0"))

            screens = self.context.app.screens()
            if not (0 <= target_screen_index < len(screens)):
                self._show_notification_if_enabled(title="排列失败", message="配置中目标屏幕索引无效。")
                return 0
            
            target_screen = screens[target_screen_index]
            screen_geometry = target_screen.geometry()
            screen_x_offset = screen_geometry.x()
            screen_y_offset = screen_geometry.y()
            usable_screen_width = screen_geometry.width()
            usable_screen_height = screen_geometry.height()

            if len(windows) > rows * cols:
                logging.warning(f"窗口数量({len(windows)})超过网格槽位({rows*cols})。")
                self._show_notification_if_enabled(title="警告", message=f"窗口数量({len(windows)})超过网格槽位，部分窗口可能无法排列。")
            
            available_width = usable_screen_width - margin_left - margin_right - (cols - 1) * spacing_h
            available_height = usable_screen_height - margin_top - margin_bottom - (rows - 1) * spacing_v
            avg_width = available_width / cols if cols > 0 else available_width
            avg_height = available_height / rows if rows > 0 else available_height
            avg_width, avg_height = max(100, int(avg_width)), max(100, int(avg_height))

            arranged_count = 0
            for i, window_info in enumerate(windows):
                if i >= rows * cols: break
                row, col = (i // cols, i % cols) if grid_direction == "row-major" else (i % rows, i // rows)
                x = screen_x_offset + margin_left + col * (avg_width + spacing_h)
                y = screen_y_offset + margin_top + row * (avg_height + spacing_v)
                
                try:
                    window_info.pygw_window_obj.restore()
                    window_info.pygw_window_obj.moveTo(int(x), int(y))
                    window_info.pygw_window_obj.resizeTo(avg_width, avg_height)
                    arranged_count += 1
                    if delay > 0:
                        QApplication.processEvents()
                        time.sleep(delay)
                except Exception as e:
                    logging.error(f"排列窗口 '{window_info.title}' 失败: {e}", exc_info=True)
            return arranged_count

        count = self._arrange_windows(do_grid_arrangement)
        if count is not None:
            self._show_notification_if_enabled(title="网格排列完成", message=f"已成功排列 {count} 个窗口。")

    def arrange_windows_cascade(self):
        """将选定的窗口按级联布局排列。"""
        logging.info(f"[WindowArranger] 正在按级联排列...")

        def do_cascade_arrangement(windows, delay):
            config = self.context.config_service
            x_offset = int(config.get_value("WindowArranger", "cascade_x_offset", "30"))
            y_offset = int(config.get_value("WindowArranger", "cascade_y_offset", "30"))
            target_screen_index = int(config.get_value("WindowArranger", "target_screen_index", "0"))

            screens = self.context.app.screens()
            if not (0 <= target_screen_index < len(screens)):
                self._show_notification_if_enabled(title="排列失败", message="配置中目标屏幕索引无效。")
                return 0

            target_screen = screens[target_screen_index]
            screen_geometry = target_screen.geometry()
            screen_x_offset = screen_geometry.x()
            screen_y_offset = screen_geometry.y()
            usable_width = screen_geometry.width()
            usable_height = screen_geometry.height()

            base_width = int(usable_width * 0.5); base_height = int(usable_height * 0.5)
            base_width = max(300, min(base_width, int(usable_width * 0.8)))
            base_height = max(200, min(base_height, int(usable_height * 0.8)))

            arranged_count = 0
            for i, window_info in enumerate(windows):
                start_x = 20; start_y = 20
                curr_x = start_x + (i * x_offset)
                curr_y = start_y + (i * y_offset)

                if curr_x + base_width > usable_width - 10:
                    curr_x = start_x + ((curr_x + base_width - (usable_width - 10)) % (usable_width - base_width - start_x))
                if curr_y + base_height > usable_height - 10:
                    curr_y = start_y + ((curr_y + base_height - (usable_height - 10)) % (usable_height - base_height - start_y))
                
                x = screen_x_offset + curr_x
                y = screen_y_offset + curr_y

                try:
                    window_info.pygw_window_obj.restore()
                    window_info.pygw_window_obj.moveTo(int(x), int(y))
                    window_info.pygw_window_obj.resizeTo(base_width, base_height)
                    arranged_count += 1
                    if delay > 0:
                        QApplication.processEvents()
                        time.sleep(delay)
                except Exception as e:
                    logging.error(f"排列窗口 '{window_info.title}' 失败: {e}", exc_info=True)
            return arranged_count

        count = self._arrange_windows(do_cascade_arrangement)
        if count is not None:
            self._show_notification_if_enabled(title="级联排列完成", message=f"已成功排列 {count} 个窗口。")
    
    def shutdown(self):
        """由插件的 shutdown 方法调用，确保后台线程被安全停止。"""
        if self.monitor_service.isRunning():
            self.monitor_service.stop()