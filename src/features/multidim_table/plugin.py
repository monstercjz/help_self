# src/features/multidim_table/plugin.py
import os
from src.core.plugin_interface import IFeaturePlugin
from src.core.context import ApplicationContext
from src.features.multidim_table.models.multidim_table_model import MultidimTableModel
from src.features.multidim_table.views.db_management_view import DbManagementView
from src.features.multidim_table.controllers.multidim_table_controller import MultidimTableController
from PySide6.QtWidgets import QWidget

class MultidimTablePlugin(IFeaturePlugin):
    """
    多维表格功能插件。
    """
    def name(self) -> str:
        return "multidim_table"

    def display_name(self) -> str:
        return "多维表格"

    def load_priority(self) -> int:
        return 150

    def initialize(self, context: ApplicationContext):
        super().initialize(context)
        
        # 创建MVC组件
        model = MultidimTableModel()
        
        # 创建主视图和控制器
        db_management_view = DbManagementView()
        self.controller = MultidimTableController(model, db_management_view, context)
        
        # 设置插件的主页面
        self.page_widget = db_management_view

    def _get_stylesheet(self) -> str | None:
        """加载并返回QSS样式表内容。"""
        qss_path = os.path.join(os.path.dirname(__file__), "assets", "style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                return f.read()
        return None
