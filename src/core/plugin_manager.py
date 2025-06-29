# desktop_center/src/core/plugin_manager.py
import importlib
import pkgutil
import logging
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
        logging.info("[STEP 2.1] PluginManager: 开始扫描 'src/features' 目录以发现插件...")
        
        for module_info in pkgutil.walk_packages(path=src.features.__path__, prefix=src.features.__name__ + '.'):
            try:
                module = importlib.import_module(module_info.name)
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if isinstance(item, type) and issubclass(item, IFeaturePlugin) and item is not IFeaturePlugin:
                        if not any(isinstance(p, item) for p in self.plugins):
                            plugin_instance = item()
                            self.plugins.append(plugin_instance)
                            logging.info(f"  - 插件已发现并加载: {plugin_instance.name()} (from {module_info.name})")
            except Exception as e:
                logging.error(f"加载插件模块 {module_info.name} 时失败: {e}", exc_info=True)
        logging.info("[STEP 2.1] PluginManager: 插件扫描和加载完成。")


    def initialize_plugins(self):
        """初始化所有已加载的插件。"""
        logging.info("[STEP 2.2] PluginManager: 开始初始化所有已加载的插件...")
        # 【修改】使用新的 load_priority() 方法进行排序，移除硬编码依赖
        self.plugins.sort(key=lambda p: p.load_priority())
        logging.info(f"  - 插件将按以下优先级顺序初始化: {[p.name() for p in self.plugins]}")
        
        for plugin in self.plugins:
            try:
                logging.info(f"  - 正在初始化插件: '{plugin.name()}' (优先级: {plugin.load_priority()})...")
                plugin.initialize(self.context)
                
                page_widget = plugin.get_page_widget()
                if page_widget:
                    self.context.main_window.add_page(plugin.display_name(), page_widget)
                    logging.info(f"    - 插件 '{plugin.name()}' 的主页面已添加到主窗口。")

                for service in plugin.get_background_services():
                    service.start()
                    logging.info(f"    - 已启动插件 '{plugin.name()}' 的后台服务: {type(service).__name__}")
                logging.info(f"  - 插件 '{plugin.name()}' 初始化完成。")
            except Exception as e:
                logging.error(f"初始化插件 {plugin.name()} 失败: {e}", exc_info=True)

    def shutdown_plugins(self):
        """安全关闭所有插件。"""
        for plugin in self.plugins:
            try:
                plugin.shutdown()
                logging.info(f"  - 插件 '{plugin.name()}' 已成功关闭。")
            except Exception as e:
                logging.error(f"关闭插件 {plugin.name()} 时发生错误: {e}", exc_info=True)