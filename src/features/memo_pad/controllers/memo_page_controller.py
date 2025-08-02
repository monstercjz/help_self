# src/features/memo_pad/controllers/memo_page_controller.py

from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtCore import QTimer, Qt
from src.features.memo_pad.views.memo_page_view import MemoPageView
from src.features.memo_pad.services.memo_database_service import MemoDatabaseService
from src.features.memo_pad.models.memo_model import Memo

class MemoPageController:
    """
    备忘录页面的控制器，负责连接视图和数据服务。
    """
    def __init__(self, view: MemoPageView, db_service: MemoDatabaseService):
        self.view = view
        self.db_service = db_service
        self._current_memo_id = None
        self.current_view_mode = 1 # 0: list, 1: split, 2: editor
        
        # 设置自动保存计时器
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.setInterval(1500) # 1.5秒延迟
        self.auto_save_timer.timeout.connect(self.auto_save)

        self._connect_signals()
        self.load_memos()

    def _connect_signals(self):
        """连接视图中的信号到控制器槽函数。"""
        self.view.new_button.clicked.connect(self.new_memo)
        self.view.delete_button.clicked.connect(self.delete_current_memo)
        self.view.delete_requested.connect(self.delete_memo_by_id)
        self.view.memo_list_widget.itemClicked.connect(self.select_memo)
        self.view.edit_requested.connect(self.enter_edit_mode)
        self.view.search_bar.textChanged.connect(self.filter_memos)
        self.view.clear_action.triggered.connect(self.view.search_bar.clear)
        self.view.search_bar.textChanged.connect(lambda text: self.view.clear_action.setVisible(bool(text)))
        self.view.view_mode_group.idClicked.connect(self.on_view_mode_changed)
        
        # 当文本变化时，启动自动保存计时器
        self.view.title_input.textChanged.connect(self.on_text_changed)
        self.view.content_text_edit.textChanged.connect(self.on_text_changed)

    def load_memos(self):
        """从数据库加载所有备忘录并更新列表。"""
        self.memos = self.db_service.get_all_memos()
        self.filter_memos()

    def new_memo(self):
        """立即创建一个新的空备忘录并选中它。"""
        new_memo = self.db_service.create_memo(title="新笔记", content="")
        self.view.add_memo_card(new_memo)
        self.view.select_item_by_id(new_memo.id)
        self.select_memo_by_id(new_memo.id)
        self.view.title_input.setFocus()
        self.view.title_input.selectAll()

    def on_text_changed(self):
        """当编辑器文本改变时，重启自动保存计时器。"""
        if self._current_memo_id is not None:
            self.auto_save_timer.start()

    def auto_save(self):
        """自动保存当前备忘录。"""
        if self._current_memo_id is None:
            return

        title = self.view.title_input.text()
        content = self.view.content_text_edit.toPlainText()
        
        updated_memo = self.db_service.update_memo(self._current_memo_id, title, content)
        if updated_memo:
            self.view.update_memo_card(updated_memo)
            timestamp = updated_memo.updated_at.strftime("%H:%M:%S")
            self.view.status_label.setText(f"已于 {timestamp} 保存")

    def delete_current_memo(self):
        """删除当前在编辑器中打开的备忘录。"""
        if self._current_memo_id:
            self.delete_memo_by_id(self._current_memo_id)

    def delete_memo_by_id(self, memo_id: int):
        """根据ID删除备忘录。"""
        self.db_service.delete_memo(memo_id)
        self.view.remove_memo_card(memo_id)
        # 如果删除的是当前正在编辑的笔记，则清空编辑器
        if self._current_memo_id == memo_id:
            self.clear_editor()

    def select_memo(self, item: QListWidgetItem):
        """当用户在列表中选择一个备忘录时，加载其内容。"""
        memo_id = item.data(Qt.UserRole)
        self.select_memo_by_id(memo_id)

    def enter_edit_mode(self, memo_id: int):
        """进入编辑模式，如果需要则切换视图。"""
        self.select_memo_by_id(memo_id)
        # 如果当前是“仅列表”视图，则自动切换到“列表与编辑”视图
        if self.current_view_mode == 0:
            self.view.view_btn2.setChecked(True)
            self.view.set_view_mode(1)

    def select_memo_by_id(self, memo_id: int):
        """根据ID加载备忘录内容到编辑器。"""
        memo = self.db_service.get_memo(memo_id)
        if memo:
            # 在加载新内容前，停止可能正在进行的自动保存
            self.auto_save_timer.stop()
            
            self._current_memo_id = memo.id
            self.view.title_input.setText(memo.title)
            self.view.content_text_edit.setText(memo.content)
            timestamp = memo.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            self.view.status_label.setText(f"上次保存于 {timestamp}")
            
            # 确保列表中的项也被选中
            self.view.select_item_by_id(memo.id)

    def clear_editor(self):
        """清空编辑器。"""
        self._current_memo_id = None
        self.view.title_input.clear()
        self.view.content_text_edit.clear()
        self.view.clear_selection()
        self.view.status_label.setText("就绪")

    def on_view_mode_changed(self, mode_id: int):
        """当视图模式按钮被点击时，更新控制器内的状态。"""
        self.current_view_mode = mode_id
        # The view handles the visual change itself, we just track the state.

    def filter_memos(self):
        """根据搜索框文本过滤并显示备忘录。"""
        search_text = self.view.search_bar.text().lower()
        self.view.memo_list_widget.clear()
        
        if not search_text:
            for memo in self.memos:
                self.view.add_memo_card(memo)
        else:
            for memo in self.memos:
                if search_text in memo.title.lower() or search_text in memo.content.lower():
                    self.view.add_memo_card(memo)
