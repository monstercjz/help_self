# desktop_center/src/features/alert_center/views/statistics/custom_analysis_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QPushButton, QTreeWidget, QTreeWidgetItem, QAbstractItemView,
                               QLabel, QGroupBox)
from PySide6.QtCore import Signal, Slot, QEvent, Qt
from PySide6.QtGui import QFont, QColor
from ...widgets.date_filter_widget import DateFilterWidget

class CustomAnalysisView(QWidget):
    analysis_requested = Signal(list)
    became_visible = Signal()

    AVAILABLE_DIMS = {
        '严重等级': 'severity',
        '信息类型': 'type',
        '来源IP': 'source_ip',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.installEventFilter(self)
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # --- 左侧控制面板 ---
        control_panel = QGroupBox("分析维度配置")
        control_layout = QVBoxLayout(control_panel)
        control_panel.setFixedWidth(250)

        # 可用维度
        control_layout.addWidget(QLabel("可用维度:"))
        self.available_dims_list = QListWidget()
        for display_name, internal_name in self.AVAILABLE_DIMS.items():
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, internal_name)
            self.available_dims_list.addItem(item)
        control_layout.addWidget(self.available_dims_list)

        # 操作按钮
        button_layout = QHBoxLayout()
        self.add_button = QPushButton(">>")
        self.remove_button = QPushButton("<<")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        control_layout.addLayout(button_layout)

        # 已选维度
        control_layout.addWidget(QLabel("已选维度 (可拖拽排序):"))
        self.selected_dims_list = QListWidget()
        self.selected_dims_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        control_layout.addWidget(self.selected_dims_list)

        # 日期和执行
        self.date_filter = DateFilterWidget()
        control_layout.addWidget(self.date_filter)
        self.analyze_button = QPushButton("开始分析")
        control_layout.addWidget(self.analyze_button)
        
        # --- 右侧结果展示 ---
        results_panel = QGroupBox("分析结果")
        results_layout = QVBoxLayout(results_panel)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["钻取路径", "告警数量"])
        self.tree.setStyleSheet("QTreeView::item:selected { background-color: #cce8ff; color: black; }")
        results_layout.addWidget(self.tree)

        main_layout.addWidget(control_panel)
        main_layout.addWidget(results_panel)

        self._connect_signals()
    
    def _connect_signals(self):
        self.add_button.clicked.connect(self._add_dimension)
        self.remove_button.clicked.connect(self._remove_dimension)
        self.analyze_button.clicked.connect(self._request_analysis)
        self.available_dims_list.itemDoubleClicked.connect(self._add_dimension)
        self.selected_dims_list.itemDoubleClicked.connect(self._remove_dimension)

    def _add_dimension(self):
        selected_items = self.available_dims_list.selectedItems()
        if not selected_items: return
        item = self.available_dims_list.takeItem(self.available_dims_list.row(selected_items[0]))
        self.selected_dims_list.addItem(item)
        
    def _remove_dimension(self):
        selected_items = self.selected_dims_list.selectedItems()
        if not selected_items: return
        item = self.selected_dims_list.takeItem(self.selected_dims_list.row(selected_items[0]))
        self.available_dims_list.addItem(item)

    def _request_analysis(self):
        selected_dims = []
        for i in range(self.selected_dims_list.count()):
            item = self.selected_dims_list.item(i)
            selected_dims.append(item.data(Qt.ItemDataRole.UserRole))
        self.analysis_requested.emit(selected_dims)

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj is self and event.type() == QEvent.Type.Show:
            self.became_visible.emit()
        return super().eventFilter(obj, event)

    @Slot(dict, list)
    def update_tree(self, tree_data: dict, dimensions: list):
        self.tree.clear()
        if not tree_data: return

        def build_ui_tree(parent_item, data_node, level):
            if not isinstance(data_node, dict): return

            for key, value_node in data_node.items():
                count = value_node.get('_count', 0)
                children = value_node.get('_children')
                
                item = QTreeWidgetItem(parent_item, [str(key), str(count)])
                if children:
                    build_ui_tree(item, children, level + 1)
        
        build_ui_tree(self.tree, tree_data, 0)
        self.tree.expandToDepth(0)