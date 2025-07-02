import sys
import logging
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel)
from PySide6.QtGui import (QMouseEvent, QDrag, QDragEnterEvent, QDropEvent, 
                           QCursor) # 【核心修复】导入 QCursor
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint, QRect

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

最终修复方案总结:
整个修复过程涉及多个层面，最终的成功方案整合了以下关键修正：

解决了 QLabel 的事件拦截问题: 通过在 group_header_widget.py 和 card_widget.py 中为 QLabel 设置 setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)，确保了鼠标事件能够被正确的父控件捕获。
确保了 QDrag 对象的生命周期: 通过将 QDrag 对象的父级设置为 self.parentWidget()，保证了拖拽对象在整个操作过程中的稳定性。
统一了MIME数据格式: 所有拖拽操作现在都使用 "type:id" 的文本格式，消除了数据解析的歧义。
修正了拖放目标逻辑: 重构了 icon_view.py 中的拖放事件处理方法，使其能够正确解析新的MIME格式，并能准确处理包括跨分组在内的所有拖拽场景。
所有相关功能，包括分组排序、组内程序排序以及跨分组移动程序，均已恢复正常。

# --- Draggable Widget (不变) ---
class DraggableItemWidget(QWidget):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.drag_start_position = None
        self.setLayout(QHBoxLayout())
        self.setMinimumHeight(40)
        self.label = QLabel(f"Draggable: {item_data['type']} '{item_data['name']}'")
        self.layout().addWidget(self.label)
        self.setStyleSheet("border: 1px solid black; margin: 2px;")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.MouseButton.LeftButton): return
        if not self.drag_start_position or (event.position().toPoint() - self.drag_start_position).manhattanLength() < 10: return
        
        drag = QDrag(self.parentWidget()) # 使用父容器作为parent
        mime_data = QMimeData()
        mime_text = f"{self.item_data['type']}:{self.item_data['id']}"
        mime_data.setText(mime_text)
        drag.setMimeData(mime_data)
        
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.position().toPoint())
        
        logging.info(f"Drag started for: {mime_text}")
        drag.exec(Qt.DropAction.MoveAction)

# --- Container (纯QWidget) ---
class DropContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.widgets = [] 

    def add_item(self, item_data):
        widget = DraggableItemWidget(item_data, self)
        self.main_layout.addWidget(widget)
        self.widgets.append(widget)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText():
            logging.info("dragEnterEvent: Accepted")
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        logging.info("--- Drop Event Received ---")
        
        # 1. 获取源信息
        mime_text = event.mimeData().text()
        if ':' not in mime_text: event.ignore(); return
        source_type, source_id = mime_text.split(':', 1)
        
        # 2. 获取目标控件
        # 【核心修复】使用 QCursor.pos() 获取全局坐标
        target_widget = QApplication.widgetAt(QCursor.pos())
        
        if not target_widget:
            logging.warning("Drop on empty space, ignoring.")
            event.ignore(); return

        # 向上追溯，找到DraggableItemWidget
        while target_widget and not isinstance(target_widget, DraggableItemWidget):
            target_widget = target_widget.parent()

        if not target_widget or not hasattr(target_widget, 'item_data'):
            logging.warning("Drop target is not a valid DraggableItemWidget.")
            event.ignore(); return

        target_data = target_widget.item_data
        target_type = target_data.get('type')
        target_id = target_data.get('id')
        
        if source_id == target_id: # 不能拖到自己身上
            event.ignore(); return

        logging.info(f"Source='{source_type}:{source_id}' --- Target='{target_type}:{target_id}'")
        
        # 3. 计算新顺序 (简化逻辑)
        source_item_data = None
        for data in self.widgets:
            if data.item_data['id'] == source_id:
                source_item_data = data.item_data
                break

        if source_item_data is None: event.ignore(); return

        current_data_list = [w.item_data for w in self.widgets]
        current_data_list.remove(source_item_data)
        
        target_index = -1
        for i, data in enumerate(current_data_list):
            if data['id'] == target_id:
                target_index = i
                break
        
        current_data_list.insert(target_index, source_item_data)
        
        logging.info("--- Reordering Complete ---")
        logging.info("New logical order:")
        for data in current_data_list:
            logging.info(f"- {data['type']}: {data['name']}")
            
        event.acceptProposedAction()
        # QApplication.instance().exit() # 成功后不再退出，以便多次测试

# --- 主窗口 ---
class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pure QWidget Drag and Drop Test (Fixed)")
        self.setGeometry(300, 300, 400, 500)
        
        self.container = DropContainer()
        self.setCentralWidget(self.container)
        
        groups = [
            {"id": "g1", "name": "Group Alpha"},
            {"id": "p1", "name": "Program A1"},
            {"id": "p2", "name": "Program A2"},
            {"id": "g2", "name": "Group Bravo"},
            {"id": "p3", "name": "Program B1"}
        ]
        
        for item in groups:
            item['type'] = 'group' if 'g' in item['id'] else 'program'
            self.container.add_item(item)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())