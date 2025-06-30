# desktop_center/src/features/window_arranger/controllers/arranger_controller.py
import logging
import math
import pygetwindow as gw # 导入 pygetwindow 库，用于窗口操作
from src.core.context import ApplicationContext
from src.features.window_arranger.views.arranger_page_view import ArrangerPageView
from src.features.window_arranger.models.window_info import WindowInfo

class ArrangerController:
    """
    负责窗口排列功能的业务逻辑。
    处理窗口检测、排列计算和与UI及核心服务的交互。
    """
    def __init__(self, context: ApplicationContext, view: ArrangerPageView):
        self.context = context
        self.view = view
        self.detected_windows: list[WindowInfo] = []

        # 连接视图发出的信号到控制器的方法
        self.view.detect_windows_requested.connect(self.detect_windows)
        self.view.arrange_grid_requested.connect(self.arrange_windows_grid)
        self.view.arrange_cascade_requested.connect(self.arrange_windows_cascade)
        
        # 加载初始设置到UI
        self._load_settings()

    def _load_settings(self):
        """从配置文件加载窗口排列相关的设置并同步到UI。"""
        settings = {
            "filter_keyword": self.context.config_service.get_value("WindowArranger", "filter_keyword", "完全控制"),
            "grid_rows": self.context.config_service.get_value("WindowArranger", "grid_rows", "2"),
            "grid_cols": self.context.config_service.get_value("WindowArranger", "grid_cols", "3"),
            "grid_spacing": self.context.config_service.get_value("WindowArranger", "grid_spacing", "10"),
            "cascade_x_offset": self.context.config_service.get_value("WindowArranger", "cascade_x_offset", "30"),
            "cascade_y_offset": self.context.config_service.get_value("WindowArranger", "cascade_y_offset", "30"),
        }
        self.view.load_settings_to_ui(settings)
        logging.info("[WindowArranger] 设置已从配置文件加载并同步到UI。")

    def _save_settings(self):
        """将当前UI上的设置保存到配置文件中。"""
        filter_keyword = self.view.get_filter_keyword()
        grid_rows, grid_cols, grid_spacing = self.view.get_grid_params()
        cascade_x_offset, cascade_y_offset = self.view.get_cascade_params()

        self.context.config_service.set_option("WindowArranger", "filter_keyword", filter_keyword)
        self.context.config_service.set_option("WindowArranger", "grid_rows", str(grid_rows))
        self.context.config_service.set_option("WindowArranger", "grid_cols", str(grid_cols))
        self.context.config_service.set_option("WindowArranger", "grid_spacing", str(grid_spacing))
        self.context.config_service.set_option("WindowArranger", "cascade_x_offset", str(cascade_x_offset))
        self.context.config_service.set_option("WindowArranger", "cascade_y_offset", str(cascade_y_offset))
        self.context.config_service.save_config()
        logging.info("[WindowArranger] 设置已保存到配置文件。")

    def detect_windows(self):
        """
        检测所有可见且标题包含指定关键词的窗口。
        并过滤掉自身应用的主窗口，避免误操作。
        """
        logging.info("[WindowArranger] 正在检测窗口...")
        self._save_settings() # 保存当前设置的过滤关键词
        
        keyword = self.view.get_filter_keyword()
        if not keyword:
            self.context.notification_service.show(
                title="检测失败",
                message="请输入窗口标题关键词进行过滤。"
            )
            logging.warning("[WindowArranger] 窗口关键词为空，无法检测。")
            self.view.update_detected_windows_list([])
            return

        all_windows = gw.getAllWindows()
        
        filtered_windows = []
        app_main_window_id = self.context.main_window.winId() # 获取自身主窗口的句柄/ID
        
        for win in all_windows:
            # 过滤条件：窗口可见、未最小化，并且标题包含关键词
            # 忽略没有标题的窗口（通常是特殊窗口或后台进程）
            # 忽略自身应用的主窗口，避免自身被排列
            # 【修复】将 'win.isVisible' 更正为 'win.visible'
            if win.title and win.visible and not win.isMinimized and keyword.lower() in win.title.lower() and win._hWnd != app_main_window_id:
                filtered_windows.append(WindowInfo(
                    title=win.title,
                    left=win.left,
                    top=win.top,
                    width=win.width,
                    height=win.height,
                    pygw_window_obj=win # 保留 pygetwindow 对象引用以便后续操作
                ))
        
        self.detected_windows = sorted(filtered_windows, key=lambda w: w.title) # 按标题排序，确保排列顺序一致
        self.view.update_detected_windows_list([w.title for w in self.detected_windows])
        
        num_detected = len(self.detected_windows)
        logging.info(f"[WindowArranger] 已检测到 {num_detected} 个符合关键词 '{keyword}' 的窗口。")
        self.context.notification_service.show(
            title="窗口检测完成",
            message=f"已检测到 {num_detected} 个符合条件的窗口。"
        )

    def arrange_windows_grid(self, rows: int, cols: int, spacing: int):
        """
        将检测到的窗口按网格布局排列。
        计算每个窗口的目标位置和大小，并进行移动和调整。
        """
        logging.info(f"[WindowArranger] 正在按网格排列窗口：{rows} 行 x {cols} 列，间距 {spacing}px。")
        self._save_settings() # 保存当前布局设置

        if not self.detected_windows:
            self.context.notification_service.show(
                title="窗口排列失败",
                message="没有可排列的窗口，请先点击'检测桌面窗口'。"
            )
            logging.warning("[WindowArranger] 无窗口可进行网格排列。")
            return

        num_windows = len(self.detected_windows)
        if num_windows > rows * cols:
            logging.warning(f"[WindowArranger] 窗口数量 ({num_windows}) 超过网格槽位 ({rows*cols})。部分窗口将无法完全适配。")
            self.context.notification_service.show(
                title="警告",
                message=f"窗口数量 ({num_windows}) 超过网格槽位 ({rows*cols})，部分窗口可能无法排列。"
            )

        # 获取主屏幕的尺寸
        screen = self.context.app.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # 确保窗口不会超出屏幕边界，为安全起见留出一些边距
        margin = 10 # 屏幕边缘留出10px边距
        usable_width = screen_width - 2 * margin
        usable_height = screen_height - 2 * margin

        # 计算每个网格单元格的理想宽度和高度
        total_horizontal_spacing = (cols - 1) * spacing
        total_vertical_spacing = (rows - 1) * spacing
        
        # 避免除以零
        if cols == 0: avg_window_width = usable_width
        else: avg_window_width = (usable_width - total_horizontal_spacing) / cols

        if rows == 0: avg_window_height = usable_height
        else: avg_window_height = (usable_height - total_vertical_spacing) / rows

        # 确保计算出的尺寸为正数
        avg_window_width = max(100, int(avg_window_width)) # 最小宽度
        avg_window_height = max(100, int(avg_window_height)) # 最小高度

        arranged_count = 0
        for i, window_info in enumerate(self.detected_windows):
            if i >= rows * cols: # 达到网格最大容量时停止
                break 

            row = i // cols
            col = i % cols

            # 计算目标位置（加上屏幕左上角的边距）
            x = int(margin + col * (avg_window_width + spacing))
            y = int(margin + row * (avg_window_height + spacing))

            try:
                target_window = window_info.pygw_window_obj
                target_window.restore() # 确保窗口不处于最小化状态
                target_window.moveTo(x, y)
                target_window.resizeTo(avg_window_width, avg_window_height)
                arranged_count += 1
                logging.debug(f"  - 排列窗口 '{window_info.title}' 到 ({x}, {y}) 尺寸 ({avg_window_width}, {avg_window_height})")
            except Exception as e:
                logging.error(f"排列窗口 '{window_info.title}' 失败: {e}", exc_info=True)
        
        self.context.notification_service.show(
            title="网格排列完成",
            message=f"已成功排列 {arranged_count} 个窗口到网格。"
        )
        logging.info(f"[WindowArranger] 网格排列完成，共排列 {arranged_count} 个窗口。")

    def arrange_windows_cascade(self, x_offset: int, y_offset: int):
        """
        将检测到的窗口按级联布局排列。
        窗口将从屏幕左上角开始，依次向右下方偏移。
        """
        logging.info(f"[WindowArranger] 正在按级联排列窗口，偏移量 ({x_offset}, {y_offset})px。")
        self._save_settings() # 保存当前布局设置

        if not self.detected_windows:
            self.context.notification_service.show(
                title="窗口排列失败",
                message="没有可排列的窗口，请先点击'检测桌面窗口'。"
            )
            logging.warning("[WindowArranger] 无窗口可进行级联排列。")
            return

        # 获取主屏幕尺寸
        screen = self.context.app.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()

        # 定义级联窗口的基础尺寸，以确保它们可见且不会过大或过小
        # 我们可以取屏幕宽度和高度的一定比例
        base_width = int(screen_width * 0.5)
        base_height = int(screen_height * 0.5)
        
        # 确保基础尺寸不小于某个最小值，并有最大值限制
        base_width = max(300, min(base_width, int(screen_width * 0.8)))
        base_height = max(200, min(base_height, int(screen_height * 0.8)))

        arranged_count = 0
        for i, window_info in enumerate(self.detected_windows):
            # 计算级联位置，确保窗口不会完全超出屏幕边界
            # 考虑屏幕的右下边界，防止窗口完全溢出
            
            # 初始位置可以设定一个小的边距
            start_x = 20
            start_y = 20

            current_x = start_x + (i * x_offset)
            current_y = start_y + (i * y_offset)

            # 简单的边界处理：如果当前窗口的右边界或下边界将超出屏幕，则回绕到屏幕左上角
            # 这会形成一个重复的级联模式
            if current_x + base_width > screen_width - 10: # 留10px边距
                current_x = start_x + ((current_x + base_width - (screen_width - 10)) % (screen_width - base_width - start_x))
            if current_y + base_height > screen_height - 10:
                current_y = start_y + ((current_y + base_height - (screen_height - 10)) % (screen_height - base_height - start_y))

            try:
                target_window = window_info.pygw_window_obj
                target_window.restore() # 确保窗口不处于最小化状态
                target_window.moveTo(int(current_x), int(current_y))
                target_window.resizeTo(base_width, base_height)
                arranged_count += 1
                logging.debug(f"  - 排列窗口 '{window_info.title}' 到 ({current_x}, {current_y}) 尺寸 ({base_width}, {base_height})")

            except Exception as e:
                logging.error(f"排列窗口 '{window_info.title}' 失败: {e}", exc_info=True)

        self.context.notification_service.show(
            title="级联排列完成",
            message=f"已成功排列 {arranged_count} 个窗口为级联。"
        )
        logging.info(f"[WindowArranger] 级联排列完成，共排列 {arranged_count} 个窗口。")