# desktop_center/src/features/program_launcher/widgets/menu_factory.py
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction

class MenuFactory:
    """
    一个工厂类，用于创建程序启动器中统一的上下文菜单。
    """
    @staticmethod
    def create_context_menu(item_type: str, item_id: str, parent_view):
        """
        根据项目类型和ID，创建一个上下文菜单。

        Args:
            item_type: 'group' 或 'program'.
            item_id: 项目的唯一ID.
            parent_view: 调用此菜单的视图控件，用于连接信号。

        Returns:
            一个配置好的 QMenu 实例。
        """
        menu = QMenu(parent_view)
        
        if item_type == 'group':
            add_program_action = QAction("添加程序到此分组...", menu)
            add_program_action.triggered.connect(lambda: parent_view.add_program_to_group_requested.emit(item_id))
            menu.addAction(add_program_action)
            
            menu.addSeparator()
            
            rename_action = QAction("重命名分组", menu)
            rename_action.triggered.connect(lambda: parent_view.edit_item_requested.emit(item_id, 'group'))
            menu.addAction(rename_action)
            
            delete_action = QAction("删除分组", menu)
            delete_action.triggered.connect(lambda: parent_view.delete_item_requested.emit(item_id, 'group'))
            menu.addAction(delete_action)

        elif item_type == 'program':
            launch_action = QAction("启动", menu)
            launch_action.triggered.connect(lambda: parent_view.item_double_clicked.emit(item_id))
            menu.addAction(launch_action)
            
            edit_action = QAction("编辑...", menu)
            edit_action.triggered.connect(lambda: parent_view.edit_item_requested.emit(item_id, 'program'))
            menu.addAction(edit_action)
            
            delete_action = QAction("删除", menu)
            delete_action.triggered.connect(lambda: parent_view.delete_item_requested.emit(item_id, 'program'))
            menu.addAction(delete_action)
            
        return menu