# desktop_center/src/features/window_arranger/controllers/arranger_controller.py
import logging
import math
import pygetwindow as gw
import psutil
import win32process
from src.core.context import ApplicationContext
from src.features.window_arranger.views.arranger_page_view import ArrangerPageView
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
        self.screens: list[QScreen] = []

        self.view.detect_windows_requested.connect(self.detect_windows)
        self.view.arrange_grid_requested.connect(self.arrange_windows_grid)
        self.view.arrange_cascade_requested.connect(self.arrange_windows_cascade)
        
        self._populate_screen_selection()
        self._load_settings()

    def _populate_screen_selection(self):
        self.screens = self.context.app.screens()
        screen_names = []
        for i, screen in enumerate(self.screens):
            screen_name = f"屏幕 {i+1} ({screen.geometry().width()}x{screen.geometry().height()})"
            if screen == self.context.app.primaryScreen():
                screen_name += " (主屏幕)"
            screen_names.append(screen_name)
        
        default_index = int(self.context.config_service.get_value("WindowArranger", "target_screen_index", "0"))
        self.view.update_screen_list(screen_names, default_index)
        logging.info(f"[WindowArranger] 已加载 {len(screen_names)} 个屏幕信息到UI。")


    def _load_settings(self):
        settings = {
            "filter_keyword": self.context.config_service.get_value("WindowArranger", "filter_keyword", "完全控制"),
            "process_name_filter": self.context.config_service.get_value("WindowArranger", "process_name_filter", ""),
            "target_screen_index": self.context.config_service.get_value("WindowArranger", "target_screen_index", "0"),
            "exclude_title_keywords": self.context.config_service.get_value("WindowArranger", "exclude_title_keywords", "Radmin Viewer"),
            "grid_direction": self.context.config_service.get_value("WindowArranger", "grid_direction", "row-major"), # 【新增】
            "grid_rows": self.context.config_service.get_value("WindowArranger", "grid_rows", "2"),
            "grid_cols": self.context.config_service.get_value("WindowArranger", "grid_cols", "3"),
            "grid_spacing": self.context.config_service.get_value("WindowArranger", "grid_spacing", "10"),
            "cascade_x_offset": self.context.config_service.get_value("WindowArranger", "cascade_x_offset", "30"),
            "cascade_y_offset": self.context.config_service.get_value("WindowArranger", "cascade_y_offset", "30"),
        }
        self.view.load_settings_to_ui(settings)
        logging.info("[WindowArranger] 设置已从配置文件加载并同步到UI。")

    def _save_settings(self):
        filter_keyword = self.view.get_filter_keyword()
        process_name_filter = self.view.get_process_name_filter()
        target_screen_index = self.view.get_selected_screen_index()
        exclude_keywords = self.view.get_exclude_keywords()
        grid_direction = self.view.get_grid_direction() # 【新增】
        grid_rows, grid_cols, grid_spacing = self.view.get_grid_params()
        cascade_x_offset, cascade_y_offset = self.view.get_cascade_params()

        self.context.config_service.set_option("WindowArranger", "filter_keyword", filter_keyword)
        self.context.config_service.set_option("WindowArranger", "process_name_filter", process_name_filter)
        self.context.config_service.set_option("WindowArranger", "target_screen_index", str(target_screen_index))
        self.context.config_service.set_option("WindowArranger", "exclude_title_keywords", exclude_keywords)
        self.context.config_service.set_option("WindowArranger", "grid_direction", grid_direction) # 【新增】
        self.context.config_service.set_option("WindowArranger", "grid_rows", str(grid_rows))
        self.context.config_service.set_option("WindowArranger", "grid_cols", str(grid_cols))
        self.context.config_service.set_option("WindowArranger", "grid_spacing", str(grid_spacing))
        self.context.config_service.set_option("WindowArranger", "cascade_x_offset", str(cascade_x_offset))
        self.context.config_service.set_option("WindowArranger", "cascade_y_offset", str(cascade_y_offset))
        self.context.config_service.save_config()
        logging.info("[WindowArranger] 设置已保存到配置文件。")

    def detect_windows(self):
        logging.info("[WindowArranger] 正在检测窗口...")
        self._save_settings()

        title_keyword_str = self.view.get_filter_keyword()
        process_keyword_str = self.view.get_process_name_filter()
        exclude_keywords_str = self.view.get_exclude_keywords()
        
        title_keywords = [kw.strip().lower() for kw in title_keyword_str.split(',') if kw.strip()]
        process_keywords = [kw.strip().lower() for kw in process_keyword_str.split(',') if kw.strip()]
        exclude_keywords_list = [kw.strip().lower() for kw in exclude_keywords_str.split(',') if kw.strip()]
        
        if not title_keywords and not process_keywords:
            self.context.notification_service.show(
                title="检测失败",
                message="请输入窗口标题关键词或进程名称进行过滤。"
            )
            logging.warning("[WindowArranger] 窗口标题关键词和进程名均为空，无法检测。")
            self.view.update_detected_windows_list([])
            return

        all_windows = gw.getAllWindows()
        
        self.detected_windows = []
        app_main_window_id = self.context.main_window.winId()
        
        for win in all_windows:
            current_window_title = win.title if win.title else "[无标题]"
            current_process_name = "[未知进程]"

            if not (win.title and win.visible and not win.isMinimized and win._hWnd != app_main_window_id):
                continue

            if exclude_keywords_list and any(ex_kw in current_window_title.lower() for ex_kw in exclude_keywords_list):
                continue

            is_title_match = not title_keywords or any(kw in win.title.lower() for kw in title_keywords)
            is_process_match = not process_keywords
            
            if process_keywords:
                try:
                    thread_id, pid = win32process.GetWindowThreadProcessId(win._hWnd)
                    if pid != 0:
                        process = psutil.Process(pid)
                        current_process_name = process.name()
                        if any(kw in current_process_name.lower() for kw in process_keywords):
                            is_process_match = True
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
                self.detected_windows.append(WindowInfo(
                    title=win.title, left=win.left, top=win.top,
                    width=win.width, height=win.height,
                    process_name=current_process_name, pygw_window_obj=win
                ))
        
        self.detected_windows = sorted(self.detected_windows, key=lambda w: (w.title, w.process_name))
        self.view.update_detected_windows_list(self.detected_windows)
        
        num_detected = len(self.detected_windows)
        logging.info(f"[WindowArranger] 已检测到 {num_detected} 个符合条件的窗口。")
        self.context.notification_service.show(
            title="窗口检测完成",
            message=f"已检测到 {num_detected} 个符合条件的窗口。"
        )

    def arrange_windows_grid(self, rows: int, cols: int, spacing: int):
        grid_direction = self.view.get_grid_direction() # 【新增】获取排列方向
        logging.info(f"[WindowArranger] 正在按网格排列窗口：{rows}x{cols}, 间距{spacing}px, 方向:{grid_direction}。")
        self._save_settings()

        windows_to_arrange = self.view.get_selected_window_infos()

        if not windows_to_arrange:
            self.context.notification_service.show(
                title="窗口排列失败",
                message="没有选择可排列的窗口。"
            )
            logging.warning("[WindowArranger] 无窗口被选择进行网格排列。")
            return

        target_screen_index = self.view.get_selected_screen_index()
        if not (0 <= target_screen_index < len(self.screens)):
            self.context.notification_service.show(
                title="排列失败",
                message="无效的目标屏幕选择。"
            )
            logging.error(f"[WindowArranger] 目标屏幕索引 {target_screen_index} 无效。")
            return
            
        target_screen = self.screens[target_screen_index]
        screen_geometry = target_screen.geometry()
        screen_x_offset = screen_geometry.x()
        screen_y_offset = screen_geometry.y()
        usable_screen_width = screen_geometry.width()
        usable_screen_height = screen_geometry.height()

        num_windows = len(windows_to_arrange)
        if num_windows > rows * cols:
            logging.warning(f"[WindowArranger] 窗口数量 ({num_windows}) 超过网格槽位。")
            self.context.notification_service.show(
                title="警告",
                message=f"窗口数量 ({num_windows}) 超过网格槽位，部分窗口可能无法排列。"
            )

        margin = 10
        available_width_for_grid = usable_screen_width - 2 * margin
        available_height_for_grid = usable_screen_height - 2 * margin
        
        total_horizontal_spacing = (cols - 1) * spacing
        total_vertical_spacing = (rows - 1) * spacing
        
        avg_window_width = (available_width_for_grid - total_horizontal_spacing) / cols if cols > 0 else available_width_for_grid
        avg_window_height = (available_height_for_grid - total_vertical_spacing) / rows if rows > 0 else available_height_for_grid

        avg_window_width = max(100, int(avg_window_width))
        avg_window_height = max(100, int(avg_window_height))

        arranged_count = 0
        for i, window_info in enumerate(windows_to_arrange):
            if i >= rows * cols:
                break 

            row, col = 0, 0
            # 【修改】根据排列方向计算行列
            if grid_direction == "row-major":
                row = i // cols
                col = i % cols
            else: # "col-major"
                row = i % rows
                col = i // rows

            x_relative = int(margin + col * (avg_window_width + spacing))
            y_relative = int(margin + row * (avg_window_height + spacing))
            
            x_absolute = screen_x_offset + x_relative
            y_absolute = screen_y_offset + y_relative

            try:
                target_window = window_info.pygw_window_obj
                target_window.restore()
                target_window.moveTo(x_absolute, y_absolute)
                target_window.resizeTo(avg_window_width, avg_window_height)
                arranged_count += 1
            except Exception as e:
                logging.error(f"排列窗口 '{window_info.title}' 失败: {e}", exc_info=True)
        
        self.context.notification_service.show(
            title="网格排列完成",
            message=f"已成功排列 {arranged_count} 个窗口到网格。"
        )
        logging.info(f"[WindowArranger] 网格排列完成，共排列 {arranged_count} 个窗口。")

    def arrange_windows_cascade(self, x_offset: int, y_offset: int):
        # ... (此方法无变化)
        logging.info(f"[WindowArranger] 正在按级联排列窗口，偏移量 ({x_offset}, {y_offset})px。")
        self._save_settings()

        windows_to_arrange = self.view.get_selected_window_infos()

        if not windows_to_arrange:
            self.context.notification_service.show(
                title="窗口排列失败",
                message="没有选择可排列的窗口。"
            )
            logging.warning("[WindowArranger] 无窗口被选择进行级联排列。")
            return

        target_screen_index = self.view.get_selected_screen_index()
        if not (0 <= target_screen_index < len(self.screens)):
            self.context.notification_service.show(
                title="排列失败",
                message="无效的目标屏幕选择。"
            )
            logging.error(f"[WindowArranger] 目标屏幕索引 {target_screen_index} 无效。")
            return
            
        target_screen = self.screens[target_screen_index]
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
                target_window = window_info.pygw_window_obj
                target_window.restore()
                target_window.moveTo(int(x_absolute), int(y_absolute))
                target_window.resizeTo(base_width, base_height)
                arranged_count += 1
            except Exception as e:
                logging.error(f"排列窗口 '{window_info.title}' 失败: {e}", exc_info=True)

        self.context.notification_service.show(
            title="级联排列完成",
            message=f"已成功排列 {arranged_count} 个窗口为级联。"
        )
        logging.info(f"[WindowArranger] 级联排列完成，共排列 {arranged_count} 个窗口。")