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
    process_name: str
    pid: int # 【新增】存储窗口的进程ID
    pygw_window_obj: object # 存储 pygetwindow.Window 实例
    
    @property
    def display_process_name(self) -> str:
        """返回用于在UI上显示的进程名，对无效值进行格式化。"""
        invalid_names = {'[未知进程]', '[PID获取失败]', '[进程不存在]', '[权限不足]', '[获取进程名失败]'}
        return "N/A" if self.process_name in invalid_names else self.process_name