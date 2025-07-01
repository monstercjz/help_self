# desktop_center/src/features/program_launcher/services/win_icon_extractor.py
import sys
import ctypes
from ctypes import wintypes
import logging

from PySide6.QtGui import QImage, QPixmap

# 仅在Windows上定义WinAPI相关结构
if sys.platform == "win32":
    # 定义 SHGetFileInfo 函数需要的常量和结构体
    SHGFI_ICON = 0x000000100
    SHGFI_LARGEICON = 0x000000000
    SHGFI_SMALLICON = 0x000000001
    SHGFI_USEFILEATTRIBUTES = 0x000000010
    FILE_ATTRIBUTE_NORMAL = 0x00000080

    class SHFILEINFO(ctypes.Structure):
        _fields_ = [
            ("hIcon", wintypes.HICON),
            ("iIcon", ctypes.c_int),
            ("dwAttributes", wintypes.DWORD),
            ("szDisplayName", wintypes.CHAR * 260),
            ("szTypeName", wintypes.CHAR * 80),
        ]
else:
    # 在非Windows平台上提供假的定义，以避免导入错误
    SHFILEINFO = type('SHFILEINFO', (object,), {})


class WinIconExtractor:
    """
    一个专门用于从Windows可执行文件中提取图标的服务。
    如果不在Windows上运行，它将不会执行任何操作。
    """
    def __init__(self):
        self.is_windows = sys.platform == "win32"
        if not self.is_windows:
            logging.info("非Windows平台，WinIconExtractor将不生效。")

    def get_icon_pixmap(self, file_path: str, small: bool = True) -> QPixmap | None:
        """
        获取指定文件路径的图标，并返回一个QPixmap。

        Args:
            file_path (str): 可执行文件的路径。
            small (bool): 是否获取小图标 (16x16)，否则为大图标 (32x32)。

        Returns:
            QPixmap | None: 成功则返回图标的QPixmap，否则返回None。
        """
        if not self.is_windows:
            return None

        try:
            file_info = SHFILEINFO()
            flags = SHGFI_ICON | SHGFI_USEFILEATTRIBUTES
            flags |= SHGFI_SMALLICON if small else SHGFI_LARGEICON

            result = ctypes.windll.shell32.SHGetFileInfoW(
                ctypes.c_wchar_p(file_path),
                FILE_ATTRIBUTE_NORMAL,
                ctypes.byref(file_info),
                ctypes.sizeof(file_info),
                flags,
            )

            if not result:
                logging.warning(f"SHGetFileInfoW failed for path: {file_path}")
                return None

            icon_handle = file_info.hIcon

            # 从HICON创建QPixmap
            # 注意：Qt for Python (PySide6) 提供了便捷的方法
            # QPixmap.fromImage(QImage.fromHICON(icon_handle)) 在某些Qt版本可能存在
            # 这里我们使用一个更通用的方法
            from PySide6.QtWinExtras import QWinFunctions
            
            pixmap = QWinFunctions.fromHICON(icon_handle)

            # 销毁图标句柄以避免资源泄漏
            ctypes.windll.user32.DestroyIcon(icon_handle)

            return pixmap if not pixmap.isNull() else None

        except Exception as e:
            logging.error(f"提取图标时发生未知错误 for path {file_path}: {e}", exc_info=True)
            return None