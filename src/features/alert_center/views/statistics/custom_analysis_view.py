# desktop_center/src/features/alert_center/views/statistics/custom_analysis_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QPushButton, QTreeWidget, QTreeWidgetItem, QAbstractItemView,
                               QLabel, QGroupBox, QSpacerItem, QSizePolicy)
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
        '按天': 'dim_date',
        '按小时': 'dim_hour',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.installEventFilter(self)
        self._init_ui()

    def _init_ui(self):
        # 【变更】采用全新的三段式垂直布局
        main_layout = QVBoxLayout(self)
        
        # --- 1. 顶部：日期过滤器 ---
        date_filter_group = QGroupBox("第一步：选择数据时间范围")
        date_filter_layout = QVBoxLayout(date_filter_group)
        self.date_filter = DateFilterWidget()
        date_filter_layout.addWidget(self.date_filter)
        main_layout.addWidget(date_filter_group)

        # --- 2. 中部：维度选择 ---
        dimension_group = QGroupBox("第二步：配置分析维度和顺序")
        dimension_main_layout = QHBoxLayout(dimension_group)

        # 左侧：可用维度
        available_layout = QVBoxLayout()
        available_layout.addWidget(QLabel("可用维度:"))
        self.available_dims_list = QListWidget()
        for display_name, internal_name in self.AVAILABLE_DIMS.items():
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, internal_name)
            self.available_dims_list.addItem(item)
        available_layout.addWidget(self.available_dims_list)
        dimension_main_layout.addLayout(available_layout)

        # 中间：操作按钮
        button_layout = QVBoxLayout()
        button_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.add_button = QPushButton(">>")
        self.remove_button = QPushButton("<<")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        dimension_main_layout.addLayout(button_layout)
        
        # 右侧：已选维度
        selected_layout = QVBoxLayout()
        selected_layout.addWidget(QLabel("已选维度 (可拖拽排序):"))
        self.selected_dims_list = QListWidget()
        self.selected_dims_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        selected_layout.addWidget(self.selected_dims_list)
        dimension_main_layout.addLayout(selected_layout)
        
        main_layout.addWidget(dimension_group)
        
        # --- 3. 底部：执行与结果 ---
        self.analyze_button = QPushButton("执行分析")
        self.analyze_button.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        main_layout.addWidget(self.analyze_button)

        results_group = QGroupBox("分析结果")
        results_layout = QVBoxLayout(results_group)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["钻取路径", "告警数量"])
        self.tree.setStyleSheet("QTreeView::item:selected { background-color: #cce8ff; color: black; }")
        results_layout.addWidget(self.tree)
        
        main_layout.addWidget(results_group)
        # 让结果区域占据更多空间
        main_layout.setStretch(3, 1)


        self._connect_signals()
    
    def _connect_signals(self):
        self.add_button.clicked.connect(self._add_dimension)
        self.remove_button.clicked.connect(self._remove_dimension)
        self.analyze_button.clicked.connect(self._request_analysis)
        self.available_dims_list.itemDoubleClicked.connect(self._add_dimension)
        self.selected_dims_list.itemDoubleClicked.connect(self._remove_dimension)
        self.date_filter.filter_changed.connect(self._request_analysis)

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
        if selected_dims:
            self.analysis_requested.emit(selected_dims)
        else:
            self.tree.clear()

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
            if level >= len(dimensions): return

            for key, value_node in data_node.items():
                count = value_node.get('_count', 0)
                children = value_node.get('_children')
                
                display_key = f"{int(key):02d}:00" if dimensions[level] == 'dim_hour' and str(key).isdigit() else str(key)
                
                item = QTreeWidgetItem(parent_item, [display_key, str(count)])
                if children:
                    build_ui_tree(item, children, level + 1)
        
        build_ui_tree(self.tree, tree_data, 0)
        self.tree.expandToDepth(0)