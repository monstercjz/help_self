# desktop_center/src/features/program_launcher/services/icon_service.py
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileIconProvider
from PySide6.QtCore import QFileInfo

class IconService:
    """
    一个单例服务，用于提供和缓存程序图标，避免重复加载和内存泄漏。
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IconService, cls).__new__(cls)
            cls._instance.icon_cache = {}
            cls._instance.icon_provider = QFileIconProvider()
        return cls._instance

    def get_program_icon(self, path: str) -> QIcon:
        """
        获取指定路径的程序图标。如果已缓存，则从缓存返回。
        """
        if not path or path in self.icon_cache:
            return self.icon_cache.get(path, QIcon.fromTheme("application-x-executable"))
        
        file_info = QFileInfo(path)
        if not file_info.exists():
            # 对于不存在的路径，也缓存一个默认图标，避免重复检查
            icon = QIcon.fromTheme("application-x-executable")
            self.icon_cache[path] = icon
            return icon

        icon = self.icon_provider.icon(file_info)
        if icon.isNull():
            icon = QIcon.fromTheme("application-x-executable")
        
        self.icon_cache[path] = icon
        return icon

    def clear_cache(self):
        """
        清空图标缓存。
        """
        self.icon_cache.clear()

# 创建一个全局实例供应用使用
icon_service = IconService()