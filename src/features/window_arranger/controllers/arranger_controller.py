# desktop_center/src/features/window_arranger/controllers/arranger_controller.py
import logging
import math
import pygetwindow as gw
import psutil
import win32process
from src.core.context import ApplicationContext
from src.features.window_arranger.views.arranger_page_view import ArrangerPageView
from src.features.window_arranger.views.settings_dialog_view import SettingsDialog # 【新增】导入设置对话框
from src.features.window_arranger.models.window_info import WindowInfo
from PySide6.QtGui import QScreen

class ArrangerController:
    """
    负责窗口排列功能的业务逻辑。
    """
    def __init__(self, context: ApplicationContext, view: ArrangerPageView):
        self.context = context
        self.view = view
        self.detected_windows: list[WindowInfo] = []
        
        # 连接主视图的信号
        self.view.detect_windows_requested.connect(self.detect_windows)
        self.view.open_settings_requested.connect(self.open_settings_dialog) # 【新增】
        self.view.arrange_grid_requested.connect(self.arrange_windows_grid)
        self.view.arrange_cascade_requested.connect(self.arrange_windows_cascade)
        
        self._save_settings_from_view() # 保存UI上的过滤设置

    # 【新增】打开设置对话框的方法
    def open_settings_dialog(self):
        dialog = SettingsDialog(self.context, self.view)
        dialog.exec() # 以模态方式执行对话框
        logging.info("[WindowArranger] 设置对话框已关闭。")

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
    
    def detect_windows(self):
        logging.info("[WindowArranger] 正在检测窗口...")
        self._save_settings_from_view() # 保存最新的过滤条件

        # ... (detect_windows 的核心逻辑不变，只是现在它只关心过滤条件)
        title_keyword_str = self.context.config_service.get_value("WindowArranger", "filter_keyword", "")
        process_keyword_str = self.context.config_service.get_value("WindowArranger", "process_name_filter", "")
        exclude_keywords_str = self.context.config_service.get_value("WindowArranger", "exclude_title_keywords", "")
        
        title_keywords = [kw.strip().lower() for kw in title_keyword_str.split(',') if kw.strip()]
        process_keywords = [kw.strip().lower() for kw in process_keyword_str.split(',') if kw.strip()]
        exclude_keywords_list = [kw.strip().lower() for kw in exclude_keywords_str.split(',') if kw.strip()]
        
        if not title_keywords and not process_keywords:
            self.context.notification_service.show(title="检测失败", message="请输入窗口标题关键词或进程名称进行过滤。")
            self.view.update_detected_windows_list([])
            return

        all_windows = gw.getAllWindows()
        self.detected_windows = []
        app_main_window_id = self.context.main_window.winId()
        
        for win in all_windows:
            current_window_title = win.title if win.title else "[无标题]"
            if not (win.title and win.visible and not win.isMinimized and win._hWnd != app_main_window_id): continue
            if exclude_keywords_list and any(ex_kw in current_window_title.lower() for ex_kw in exclude_keywords_list): continue
            
            is_title_match = not title_keywords or any(kw in win.title.lower() for kw in title_keywords)
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
                        else: is_process_match = False
                except Exception: is_process_match = False
            
            should_add = (process_keywords and is_process_match and (is_title_match or not title_keywords)) or \
                         (title_keywords and not process_keywords and is_title_match)
            
            if should_add:
                self.detected_windows.append(WindowInfo(
                    title=win.title, left=win.left, top=win.top,
                    width=win.width, height=win.height,
                    process_name=current_process_name, pygw_window_obj=win
                ))
        
        self.detected_windows = sorted(self.detected_windows, key=lambda w: (w.title, w.process_name))
        self.view.update_detected_windows_list(self.detected_windows)
        self.context.notification_service.show(title="窗口检测完成", message=f"已检测到 {len(self.detected_windows)} 个符合条件的窗口。")

    def arrange_windows_grid(self):
        # 【修改】从 ConfigService 读取所有排列参数
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
        
        logging.info(f"[WindowArranger] 正在按网格排列...")
        windows_to_arrange = self.view.get_selected_window_infos()

        if not windows_to_arrange:
            self.context.notification_service.show(title="窗口排列失败", message="没有选择可排列的窗口。")
            return

        target_screen_index = int(config.get_value("WindowArranger", "target_screen_index", "0"))
        screens = self.context.app.screens()
        if not (0 <= target_screen_index < len(screens)):
            self.context.notification_service.show(title="排列失败", message="配置中目标屏幕索引无效。")
            return
            
        # ... (后续排列算法不变)
        target_screen = screens[target_screen_index]
        screen_geometry = target_screen.geometry()
        screen_x_offset = screen_geometry.x()
        screen_y_offset = screen_geometry.y()
        usable_screen_width = screen_geometry.width()
        usable_screen_height = screen_geometry.height()

        available_width_for_grid = usable_screen_width - margin_left - margin_right
        available_height_for_grid = usable_screen_height - margin_top - margin_bottom

        total_horizontal_spacing = (cols - 1) * spacing_h
        total_vertical_spacing = (rows - 1) * spacing_v
        
        avg_window_width = (available_width_for_grid - total_horizontal_spacing) / cols if cols > 0 else available_width_for_grid
        avg_window_height = (available_height_for_grid - total_vertical_spacing) / rows if rows > 0 else available_height_for_grid

        avg_window_width = max(100, int(avg_window_width))
        avg_window_height = max(100, int(avg_window_height))

        arranged_count = 0
        for i, window_info in enumerate(windows_to_arrange):
            if i >= len(windows_to_arrange) or i >= rows * cols: break 
            row, col = (i // cols, i % cols) if grid_direction == "row-major" else (i % rows, i // rows)
            x_relative = int(margin_left + col * (avg_window_width + spacing_h))
            y_relative = int(margin_top + row * (avg_window_height + spacing_v))
            x_absolute = screen_x_offset + x_relative
            y_absolute = screen_y_offset + y_relative

            try:
                window_info.pygw_window_obj.restore()
                window_info.pygw_window_obj.moveTo(x_absolute, y_absolute)
                window_info.pygw_window_obj.resizeTo(avg_window_width, avg_window_height)
                arranged_count += 1
            except Exception as e:
                logging.error(f"排列窗口 '{window_info.title}' 失败: {e}", exc_info=True)
        
        self.context.notification_service.show(title="网格排列完成", message=f"已成功排列 {arranged_count} 个窗口。")

    def arrange_windows_cascade(self):
        # 【修改】从 ConfigService 读取所有排列参数
        config = self.context.config_service
        x_offset = int(config.get_value("WindowArranger", "cascade_x_offset", "30"))
        y_offset = int(config.get_value("WindowArranger", "cascade_y_offset", "30"))
        
        # ... (后续逻辑与 arrange_windows_grid 类似)
        logging.info(f"[WindowArranger] 正在按级联排列...")
        windows_to_arrange = self.view.get_selected_window_infos()
        if not windows_to_arrange:
            self.context.notification_service.show(title="窗口排列失败", message="没有选择可排列的窗口。")
            return
            
        target_screen_index = int(config.get_value("WindowArranger", "target_screen_index", "0"))
        screens = self.context.app.screens()
        if not (0 <= target_screen_index < len(screens)):
            self.context.notification_service.show(title="排列失败", message="配置中目标屏幕索引无效。")
            return

        target_screen = screens[target_screen_index]
        # ... (后续排列算法不变)
        screen_geometry = target_screen.geometry()
        screen_x_offset = screen_geometry.x()
        screen_y_offset = screen_geometry.y()
        usable_screen_width = screen_geometry.width()
        usable_screen_height = screen_geometry.height()

        base_width = int(usable_screen_width * 0.5)
        base_height = int(usable_screen_height * 0.5)
        
        base_width = max(300, min(base_width, int(usable_screen_width * 0.8)))
        base_height = max(200, min(base_height, int(usable_screen_height * 0.8)))

        arranged_count = 0
        for i, window_info in enumerate(windows_to_arrange):
            start_x_relative = 20
            start_y_relative = 20

            current_x_relative = start_x_relative + (i * x_offset)
            current_y_relative = start_y_relative + (i * y_offset)

            if current_x_relative + base_width > usable_screen_width - 10:
                current_x_relative = start_x_relative + ((current_x_relative + base_width - (usable_screen_width - 10)) % (usable_screen_width - base_width - start_x_relative))
            if current_y_relative + base_height > usable_screen_height - 10:
                current_y_relative = start_y_relative + ((current_y_relative + base_height - (usable_screen_height - 10)) % (usable_screen_height - base_height - start_y_relative))

            x_absolute = screen_x_offset + current_x_relative
            y_absolute = screen_y_offset + current_y_relative

            try:
                window_info.pygw_window_obj.restore()
                window_info.pygw_window_obj.moveTo(int(x_absolute), int(y_absolute))
                window_info.pygw_window_obj.resizeTo(base_width, base_height)
                arranged_count += 1
            except Exception as e:
                logging.error(f"排列窗口 '{window_info.title}' 失败: {e}", exc_info=True)

        self.context.notification_service.show(title="级联排列完成", message=f"已成功排列 {arranged_count} 个窗口。")