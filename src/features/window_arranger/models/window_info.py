# desktop_center/src/features/window_arranger/models/window_info.py
from dataclasses import dataclass

@dataclass
class WindowInfo:
    """数据类，用于存储检测到的窗口信息。
    pygw_window_obj 字段存储 pygetwindow.Window 对象的引用，以便直接操作。
    """
    title: str
    left: int
    top: int
    width: int
    height: int
    pygw_window_obj: object # 存储 pygetwindow.Window 实例