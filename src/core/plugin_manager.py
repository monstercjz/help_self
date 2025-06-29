# src/core/plugin_manager.py (【修正版】)
import importlib
import pkgutil
import logging
# 【修正】保持导入风格统一
from src.core.plugin_interface import IFeaturePlugin

class PluginManager:
    """负责发现、加载和管理所有插件的管理器。"""
    def __init__(self, context):
        self.context = context
        self.plugins: list[IFeaturePlugin] = []

    def load_plugins(self):
        """
        使用 walk_packages 递归地发现并加载所有在 src.features 包下的插件。
        """
        import src.features
        
        for module_info in pkgutil.walk_packages(path=src.features.__path__, prefix=src.features.__name__ + '.'):
            try:
                module = importlib.import_module(module_info.name)
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if isinstance(item, type) and issubclass(item, IFeaturePlugin) and item is not IFeaturePlugin:
                        # 检查插件是否已经加载，防止重复
                        if not any(isinstance(p, item) for p in self.plugins):
                            plugin_instance = item()
                            self.plugins.append(plugin_instance)
                            logging.info(f"成功加载插件: {plugin_instance.name()} from {module_info.name}")
            except Exception as e:
                logging.error(f"加载插件模块 {module_info.name} 时失败: {e}", exc_info=True)

    def initialize_plugins(self):
        """初始化所有已加载的插件。"""
        # 为了让“信息接收中心”排在第一位，可以简单排序
        self.plugins.sort(key=lambda p: p.display_name() != "信息接收中心")
        
        for plugin in self.plugins:
            try:
                plugin.initialize(self.context)
                
                page_widget = plugin.get_page_widget()
                if page_widget:
                    self.context.main_window.add_page(plugin.display_name(), page_widget)

                for service in plugin.get_background_services():
                    service.start()
                    logging.info(f"已启动插件 '{plugin.name()}' 的后台服务: {type(service).__name__}")
            except Exception as e:
                logging.error(f"初始化插件 {plugin.name()} 失败: {e}", exc_info=True)

    def shutdown_plugins(self):
        """安全关闭所有插件。"""
        for plugin in self.plugins:
            try:
                plugin.shutdown()
                logging.info(f"插件 {plugin.name()} 已关闭。")
            except Exception as e:
                logging.error(f"关闭插件 {plugin.name()} 时发生错误: {e}", exc_info=True)