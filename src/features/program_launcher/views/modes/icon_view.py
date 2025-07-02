# desktop_center/src/features/program_launcher/views/modes/icon_view.py
import logging
from PySide6.QtWidgets import (QMenu, QFileIconProvider, QVBoxLayout, 
                               QLabel, QWidget, QScrollArea, QFrame)
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QDragMoveEvent
from PySide6.QtCore import Qt, QFileInfo, QSize, QPoint, QRect

from .base_view import BaseViewMode
from ...widgets.card_widget import CardWidget
from .flow_layout import FlowLayout

class IconViewMode(BaseViewMode):
    """
    图标网格视图模式的实现。
    【修改】修复了拖放事件中的坐标系问题。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_cache = {}
        self.icon_provider = QFileIconProvider()
        self.card_containers = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # content_widget 是所有内容的父控件，也是我们的“世界坐标系”
        self.content_widget = QWidget()
        scroll_area.setWidget(self.content_widget)

        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        main_layout.addWidget(scroll_area)
        
        # 拖拽指示器，它的父控件应该是 content_widget
        self.drop_indicator = QFrame(self.content_widget)
        self.drop_indicator.setFrameShape(QFrame.Shape.VLine)
        self.drop_indicator.setLineWidth(2)
        self.drop_indicator.setStyleSheet("background-color: #0078d4;")
        self.drop_indicator.hide()
        
        # 自身也需要接收拖放事件，以便将坐标转换为 content_widget 的坐标
        self.setAcceptDrops(True)

    def update_view(self, data: dict):
        self.card_containers.clear()
        
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        groups = data.get("groups", [])
        programs = data.get("programs", {})
        
        programs_by_group = {}
        for prog_id, prog_data in programs.items():
            group_id = prog_data.get('group_id')
            if group_id not in programs_by_group: programs_by_group[group_id] = []
            programs_by_group[group_id].append(prog_data)
        for group_id in programs_by_group:
            programs_by_group[group_id].sort(key=lambda p: p.get("order", 0))

        if not groups:
            self.content_layout.addWidget(QLabel("没有内容，请先添加分组和程序。"))
            return

        for group_data in groups:
            group_title = QLabel(f"<b>{group_data['name']}</b>")
            group_title.setStyleSheet("padding: 15px 0 8px 5px; font-size: 14px; border-bottom: 1px solid #e0e0e0; margin-bottom: 5px;")
            self.content_layout.addWidget(group_title)

            card_container = QWidget()
            flow_layout = FlowLayout(card_container, h_spacing=10, v_spacing=10)
            self.card_containers[group_data['id']] = card_container

            programs_in_group = programs_by_group.get(group_data['id'], [])
            if not programs_in_group:
                flow_layout.addWidget(QLabel("(此分组为空)"))
            else:
                for prog_data in programs_in_group:
                    icon = self._get_program_icon(prog_data['path'])
                    card = CardWidget(prog_data, icon)
                    card.doubleClicked.connect(self.item_double_clicked)
                    card.customContextMenuRequested.connect(self._on_context_menu)
                    flow_layout.addWidget(card)
            
            self.content_layout.addWidget(card_container)
        
        self.content_layout.addStretch()
    
    def _get_program_icon(self, path: str) -> QIcon:
        if not path or path in self.icon_cache: return self.icon_cache.get(path, QIcon.fromTheme("application-x-executable"))
        icon = self.icon_provider.icon(QFileInfo(path))
        if icon.isNull(): icon = QIcon.fromTheme("application-x-executable")
        self.icon_cache[path] = icon
        return icon

    def _on_context_menu(self, program_id, event):
        menu = QMenu(self)
        menu.addAction("启动").triggered.connect(lambda: self.item_double_clicked.emit(program_id))
        menu.addAction("编辑...").triggered.connect(lambda: self.edit_item_requested.emit(program_id, 'program'))
        menu.addAction("删除").triggered.connect(lambda: self.delete_item_requested.emit(program_id, 'program'))
        menu.exec_(event.globalPos())

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-program-launcher-card"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.drop_indicator.hide()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if not event.mimeData().hasFormat("application/x-program-launcher-card"):
            event.ignore(); return
        
        # 【核心修复】将事件坐标转换为 content_widget 的内部坐标
        pos_in_content_widget = self.content_widget.mapFrom(self, event.position().toPoint())
        target_group_id, target_index, indicator_pos = self._find_drop_pos(pos_in_content_widget)
        
        if indicator_pos:
            self.drop_indicator.setGeometry(indicator_pos)
            self.drop_indicator.show()
            event.accept()
        else:
            self.drop_indicator.hide()

    def dropEvent(self, event: QDropEvent):
        self.drop_indicator.hide()
        if not event.mimeData().hasFormat("application/x-program-launcher-card"):
            event.ignore(); return
        
        program_id = event.mimeData().data("application/x-program-launcher-card").data().decode('utf-8')
        
        # 【核心修复】将事件坐标转换为 content_widget 的内部坐标
        pos_in_content_widget = self.content_widget.mapFrom(self, event.position().toPoint())
        target_group_id, target_index, _ = self._find_drop_pos(pos_in_content_widget)

        if target_group_id is not None:
            logging.info(f"Program '{program_id}' dropped on group '{target_group_id}' at index {target_index}")
            self.program_dropped.emit(program_id, target_group_id, target_index)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _find_drop_pos(self, pos_in_content_widget: QPoint):
        for group_id, container in self.card_containers.items():
            # 【核心修复】现在 container.geometry() 和 pos_in_content_widget 都在同一个坐标系下
            if container.geometry().contains(pos_in_content_widget):
                layout = container.layout()
                local_pos = container.mapFrom(self.content_widget, pos_in_content_widget)
                
                target_index = 0
                for i in range(layout.count()):
                    widget = layout.itemAt(i).widget()
                    # 判断鼠标是否在卡片中心线的左边
                    if local_pos.x() < widget.geometry().center().x():
                        break
                    target_index = i + 1
                
                # 计算指示器的位置 (相对于 container)
                indicator_rect = QRect()
                if layout.count() == 0:
                    indicator_rect.setRect(5, 5, 2, 80) # 在空容器里的位置
                elif target_index < layout.count():
                    widget = layout.itemAt(target_index).widget()
                    indicator_rect.setRect(widget.x() - 5, widget.y(), 2, widget.height())
                else:
                    last_widget = layout.itemAt(layout.count() - 1).widget()
                    indicator_rect.setRect(last_widget.x() + last_widget.width() + 3, last_widget.y(), 2, last_widget.height())

                # 将指示器的相对位置转换为 content_widget 的坐标
                final_indicator_rect = QRect(container.mapTo(self.content_widget, indicator_rect.topLeft()), indicator_rect.size())
                return group_id, target_index, final_indicator_rect
                
        return None, -1, None