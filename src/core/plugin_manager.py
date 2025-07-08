# desktop_center/src/core/plugin_manager.py
import importlib
import pkgutil
import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QThread
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
        import os
        import sys
        import importlib.util # 【新增】导入 importlib.util

        logging.info("[STEP 2.1] PluginManager: 开始扫描 'src/features' 目录以发现插件...")

        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # PyInstaller 打包环境
            plugins_root_path = os.path.join(sys._MEIPASS, 'src', 'features')
            logging.info(f"  - 检测到PyInstaller环境，扫描插件路径: {plugins_root_path}")
            if os.path.exists(plugins_root_path):
                for plugin_dir in os.listdir(plugins_root_path):
                    plugin_path = os.path.join(plugins_root_path, plugin_dir)
                    plugin_main_file = os.path.join(plugin_path, 'plugin.py')
                    if os.path.isdir(plugin_path) and os.path.exists(plugin_main_file):
                        try:
                            # 动态加载插件模块
                            spec = importlib.util.spec_from_file_location(f"src.features.{plugin_dir}.plugin", plugin_main_file)
                            if spec and spec.loader:
                                module = importlib.util.module_from_spec(spec)
                                sys.modules[spec.name] = module
                                spec.loader.exec_module(module)
                                
                                for item_name in dir(module):
                                    item = getattr(module, item_name)
                                    if isinstance(item, type) and issubclass(item, IFeaturePlugin) and item is not IFeaturePlugin:
                                        if not any(isinstance(p, item) for p in self.plugins):
                                            plugin_instance = item()
                                            self.plugins.append(plugin_instance)
                                            logging.info(f"  - 插件已发现并加载: {plugin_instance.name()} (from {plugin_dir}/plugin.py)")
                        except Exception as e:
                            logging.error(f"加载插件模块 {plugin_dir}/plugin.py 时失败: {e}", exc_info=True)
            else:
                logging.warning(f"  - PyInstaller环境下未找到插件目录: {plugins_root_path}")
        else:
            # 开发环境
            import src.features
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
        self.plugins.sort(key=lambda p: p.load_priority())
        logging.info(f"  - 插件将按以下优先级顺序初始化: {[p.name() for p in self.plugins]}")
        
        for plugin in self.plugins:
            try:
                logging.info(f"  - 正在初始化插件: '{plugin.name()}' (优先级: {plugin.load_priority()})...")
                plugin.initialize(self.context)
                
                # 【修改】对插件返回值进行健壮性检查
                page_widget = plugin.get_page_widget()
                if page_widget:
                    if isinstance(page_widget, QWidget):
                        self.context.main_window.add_page(plugin.display_name(), page_widget)
                        logging.info(f"    - 插件 '{plugin.name()}' 的主页面已添加到主窗口。")
                    else:
                        logging.warning(f"    - 插件 '{plugin.name()}' 的 get_page_widget() 返回的不是有效QWidget，已忽略。")

                background_services = plugin.get_background_services()
                if background_services:
                    for service in background_services:
                        if isinstance(service, QThread) and hasattr(service, 'start'):
                            service.start()
                            logging.info(f"    - 已启动插件 '{plugin.name()}' 的后台服务: {type(service).__name__}")
                        else:
                            logging.warning(f"    - 插件 '{plugin.name()}' 返回的后台服务 {type(service).__name__} 不是有效的QThread，已忽略。")
                
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