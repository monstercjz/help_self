# src/features/memo_pad/controllers/memo_page_controller.py

import os
import logging
from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtCore import QTimer, Qt
from src.features.memo_pad.views.memo_page_view import MemoPageView
from src.features.memo_pad.services.memo_database_service import MemoDatabaseService
from src.features.memo_pad.models.memo_model import Memo
from src.services.generic_data_service import DataType

class MemoPageController:
    """
    备忘录页面的控制器，负责连接视图和数据服务。
    """
    def __init__(self, view: MemoPageView, db_service: MemoDatabaseService, context, plugin_name: str):
        self.view = view
        self.db_service = db_service
        self.context = context
        self.plugin_name = plugin_name
        self._current_memo_id = None
        self.current_view_mode = 1 # 0: list, 1: split, 2: editor
        
        # 设置自动保存计时器
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.setInterval(1500) # 1.5秒延迟
        self.auto_save_timer.timeout.connect(self.auto_save)

        self._connect_signals()
        
        # 初始化加载
        self.view.set_current_db(self.db_service.db_path)
        self.load_memos()
        logging.info(f"MemoPageController initialized for db: {self.db_service.db_path}")

    def _connect_signals(self):
        """连接视图中的信号到控制器槽函数。"""
        self.view.new_button.clicked.connect(self.new_memo)
        self.view.delete_button.clicked.connect(self.delete_current_memo)
        self.view.delete_requested.connect(self.delete_memo_by_id)
        self.view.memo_list_widget.itemClicked.connect(self.select_memo)
        self.view.memo_list_widget.blank_area_clicked.connect(self.clear_editor)
        self.view.edit_requested.connect(self.enter_edit_mode)
        self.view.search_bar.textChanged.connect(self.filter_memos)
        self.view.clear_action.triggered.connect(self.view.search_bar.clear)
        self.view.search_bar.textChanged.connect(lambda text: self.view.clear_action.setVisible(bool(text)))
        self.view.view_mode_group.idClicked.connect(self.on_view_mode_changed)
        self.view.database_change_requested.connect(self._on_database_change) # 信号不再传递参数
        
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
        logging.info(f"New memo created with id: {new_memo.id}, title: '{new_memo.title}'")
        # 更新内存中的列表
        self.memos.insert(0, new_memo)
        # 刷新整个列表以保证顺序
        self.filter_memos()
        # 选中新创建的备忘录
        self.view.select_item_by_id(new_memo.id)
        self.select_memo_by_id(new_memo.id)
        self.view.title_input.setFocus()
        self.view.title_input.selectAll()

    def on_text_changed(self):
        """
        当编辑器文本改变时，
        如果当前有选中的备忘录，则启动自动保存计时器。
        如果当前没有选中的备忘录，则立即创建一个新的备忘录。
        """
        if self._current_memo_id is None:
            # 这是“从无到有”创建新备忘录的场景
            title = self.view.title_input.text()
            content = self.view.content_text_edit.toPlainText()
            
            # 只有当编辑器里确实有内容时才创建
            # if title or content:
                # 1. 在进行任何操作前，完全断开信号，防止连锁反应
                # try:
                #     self.view.title_input.textChanged.disconnect(self.on_text_changed)
                #     self.view.content_text_edit.textChanged.disconnect(self.on_text_changed)
                # except RuntimeError:
                #     pass # 忽略断开失败的警告
                
            # 只有当编辑器里确实有内容（标题或内容长度大于等于阈值）时才自动创建
            MIN_AUTO_CREATE_LENGTH = 3 # 设定一个最小长度阈值
            if len(title) >= MIN_AUTO_CREATE_LENGTH or len(content) >= MIN_AUTO_CREATE_LENGTH:
                # 1. 在进行任何操作前，临时阻塞信号，防止连锁反应
                self.view.title_input.blockSignals(True)
                self.view.content_text_edit.blockSignals(True)

                # 2. 创建新的备忘录 (在控制器层面处理默认标题)
                final_title = title if title else "新笔记"
                new_memo = self.db_service.create_memo(title=final_title, content=content)
                logging.info(f"New memo auto-created from editor with id: {new_memo.id}")
                
                # 3. 更新数据模型和内部状态
                self.memos.insert(0, new_memo)
                self._current_memo_id = new_memo.id
                
                # 4. 更新UI
                self.filter_memos() # 更新左侧列表
                self.view.select_item_by_id(new_memo.id) # 高亮新条目
                self.view.title_input.setText(new_memo.title) # 用返回的数据更新标题
                
                # 5. 在所有操作完成后，重新连接信号
                # self.view.title_input.textChanged.connect(self.on_text_changed)
                # self.view.content_text_edit.textChanged.connect(self.on_text_changed)
                # 5. 在所有操作完成后，解除信号阻塞
                self.view.title_input.blockSignals(False)
                self.view.content_text_edit.blockSignals(False)
        else:
            # 这是更新现有备忘录的场景
            self.auto_save_timer.start()

    def auto_save(self):
        """自动保存当前备忘录。"""
        if self._current_memo_id is None:
            return

        title = self.view.title_input.text()
        content = self.view.content_text_edit.toPlainText()
        
        updated_memo = self.db_service.update_memo(self._current_memo_id, title, content)
        if updated_memo:
            # 更新内存中的列表顺序
            try:
                # 找到旧的备忘录并移除
                old_memo = next(m for m in self.memos if m.id == updated_memo.id)
                self.memos.remove(old_memo)
            except StopIteration:
                pass # 如果找不到，也没关系
            # 将更新后的备忘录插入到顶部
            self.memos.insert(0, updated_memo)
            # 刷新整个列表
            self.filter_memos()
            # 确保更新后的项仍然被选中
            self.view.select_item_by_id(updated_memo.id)
            
            timestamp = updated_memo.updated_at.strftime("%H:%M:%S")
            self.view.status_label.setText(f"已于 {timestamp} 保存")

    def delete_current_memo(self):
        """删除当前在编辑器中打开的备忘录。"""
        if self._current_memo_id:
            self.delete_memo_by_id(self._current_memo_id)

    def delete_memo_by_id(self, memo_id: int):
        """根据ID删除备忘录。"""
        was_current = (self._current_memo_id == memo_id)
        
        if self.db_service.delete_memo(memo_id):
            logging.info(f"Memo deleted with id: {memo_id}")
        
        # 更新内存列表
        self.memos = [m for m in self.memos if m.id != memo_id]
        
        # 如果删除的是当前正在编辑的笔记，则清空编辑器
        if was_current:
            self.clear_editor()
            
        # 刷新列表
        self.filter_memos()

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
        # 如果计时器是激活状态，意味着有未保存的更改，立即保存。
        if self.auto_save_timer.isActive():
            self.auto_save()

        # 在加载新内容前，停止可能正在进行的自动保存
        self.auto_save_timer.stop()

        memo = self.db_service.get_memo(memo_id)
        if memo:
            self._current_memo_id = memo.id

            # 临时断开信号，以编程方式设置文本，避免触发自动保存
            # try:
            #     self.view.title_input.textChanged.disconnect(self.on_text_changed)
            #     self.view.content_text_edit.textChanged.disconnect(self.on_text_changed)
            # except RuntimeError:
            #      如果信号尚未连接，disconnect会引发RuntimeError，可以安全地忽略
            #     pass
            # 临时阻塞信号，以编程方式设置文本，避免触发自动保存
            self.view.title_input.blockSignals(True)
            self.view.content_text_edit.blockSignals(True)

            self.view.title_input.setText(memo.title)
            self.view.content_text_edit.setText(memo.content)

            # 重新连接信号
            # self.view.title_input.textChanged.connect(self.on_text_changed)
            # self.view.content_text_edit.textChanged.connect(self.on_text_changed)
            # 解除信号阻塞
            self.view.title_input.blockSignals(False)
            self.view.content_text_edit.blockSignals(False)

            timestamp = memo.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            self.view.status_label.setText(f"上次保存于 {timestamp}")
            
            # 确保列表中的项也被选中
            self.view.select_item_by_id(memo.id)

    def clear_editor(self):
        """清空编辑器，并临时断开信号以防止副作用。"""
        self._current_memo_id = None

        # 临时断开信号，以编程方式设置文本，避免触发自动保存
        # try:
        #     self.view.title_input.textChanged.disconnect(self.on_text_changed)
        #     self.view.content_text_edit.textChanged.disconnect(self.on_text_changed)
        # except RuntimeError:
        #      如果信号尚未连接，disconnect会引发RuntimeError，可以安全地忽略
        #     pass
        # 临时阻塞信号，以编程方式设置文本，避免触发自动保存
        self.view.title_input.blockSignals(True)
        self.view.content_text_edit.blockSignals(True)

        self.view.title_input.clear()
        self.view.content_text_edit.clear()

        # 重新连接信号
        # self.view.title_input.textChanged.connect(self.on_text_changed)
        # self.view.content_text_edit.textChanged.connect(self.on_text_changed)
        # 解除信号阻塞
        self.view.title_input.blockSignals(False)
        self.view.content_text_edit.blockSignals(False)

        self.view.clear_selection()
        self.view.status_label.setText("就绪")

    def on_view_mode_changed(self, mode_id: int):
        """当视图模式按钮被点击时，更新控制器内的状态。"""
        self.current_view_mode = mode_id
        # The view handles the visual change itself, we just track the state.

    def _on_database_change(self): # 不再接收文件路径参数
        """处理用户主动发起的数据库切换请求。"""
        # 使用重构后的通用数据源切换服务
        new_generic_service = self.context.switch_service.switch(
            parent_widget=self.view,
            current_path=self.db_service.db_path,
            config_service=self.context.config_service,
            config_section=self.plugin_name,
            config_key="db_path",
            data_type=DataType.SQLITE,
            file_filter="数据库文件 (*.db);;所有文件 (*)",
            db_service_class=MemoDatabaseService
        )

        if new_generic_service:
            # 确保任何待处理的更改都已保存
            if self.auto_save_timer.isActive():
                self.auto_save()

            # 返回的是一个包装过的服务实例，需要通过 .db_service 访问原始的 MemoDatabaseService
            self.db_service = new_generic_service.db_service
            self.clear_editor()
            self.memos = []
            self.load_memos()
            self.view.set_current_db(self.db_service.db_path)
            file_name = os.path.basename(self.db_service.db_path)
            self.view.status_label.setText(f"成功加载数据库: {file_name}")

    def _refresh_memo_list(self, memos_to_display: list[Memo]):
        """
        核心刷新函数：清空并根据给定列表重新渲染UI。
        """
        self.view.memo_list_widget.clear()
        for memo in memos_to_display:
            self.view.add_memo_card(memo)

    def filter_memos(self):
        """根据搜索框文本过滤并显示备忘录。"""
        search_text = self.view.search_bar.text().lower()
        
        if not search_text:
            # 如果没有搜索文本，显示所有备忘录
            memos_to_display = self.memos
        else:
            # 如果有搜索文本，过滤备忘录
            memos_to_display = [
                memo for memo in self.memos
                if search_text in memo.title.lower() or search_text in memo.content.lower()
            ]
        
        self._refresh_memo_list(memos_to_display)
