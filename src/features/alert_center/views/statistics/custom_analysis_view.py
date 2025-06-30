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
        # 根布局：垂直组合F (组合E + 分析结果)
        main_layout = QVBoxLayout(self)
        
        # --- 组合E (水平组合C + 单元D) 的容器 ---
        # 严格限制这个容器的高度
        top_section_container = QWidget()
        # 【变更】严格限制这个容器的高度
        top_section_container.setMaximumHeight(145) # 根据实际需要调整这个值
        top_section_layout = QHBoxLayout(top_section_container) # 组合E的布局



        # --- 单元D (维度选择区域) ---
        dimension_group = QGroupBox("第二步：配置分析维度和顺序")
        dimension_main_layout = QHBoxLayout(dimension_group)

        available_layout = QVBoxLayout()
        # available_layout.addWidget(QLabel("可用维度:"))
        self.available_dims_list = QListWidget()
        for display_name, internal_name in self.AVAILABLE_DIMS.items():
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, internal_name)
            self.available_dims_list.addItem(item)
        self.available_dims_list.setMaximumHeight(150)
        available_layout.addWidget(self.available_dims_list)
        dimension_main_layout.addLayout(available_layout)

        button_layout = QVBoxLayout()
        button_layout.addStretch()
        self.add_button = QPushButton(">>")
        self.remove_button = QPushButton("<<")
        self.up_button = QPushButton("↑ ↑ ↑")
        self.down_button = QPushButton("↓ ↓ ↓")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        # button_layout.addSpacing(10)
        button_layout.addWidget(self.up_button)
        button_layout.addWidget(self.down_button)
        button_layout.addStretch()
        dimension_main_layout.addLayout(button_layout)
        
        selected_layout = QVBoxLayout()
        # selected_layout.addWidget(QLabel("已选维度 (可拖拽或使用按钮排序):"))
        self.selected_dims_list = QListWidget()
        self.selected_dims_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.selected_dims_list.setMaximumHeight(150)
        selected_layout.addWidget(self.selected_dims_list)
        dimension_main_layout.addLayout(selected_layout)
        
        top_section_layout.addWidget(dimension_group) # 单元D添加到组合E的右侧
        top_section_layout.setStretch(0, 1) # 组合C和单元D平分或按比例分配水平空间
        top_section_layout.setStretch(1, 2) # 维度选择区域可以稍微宽一点


        # --- 组合C (垂直组合A + 单元B) ---
        C_layout = QVBoxLayout()

        # 单元B (日期过滤器)
        date_filter_group = QGroupBox("第一步：选择数据时间范围")
        date_filter_layout = QVBoxLayout(date_filter_group)
        self.date_filter = DateFilterWidget()
        date_filter_layout.addWidget(self.date_filter)
        C_layout.addWidget(date_filter_group)
        
        top_section_layout.addLayout(C_layout) # 组合C添加到组合E的左侧

        # 组合A (水平组合：执行按钮 + 展开/折叠按钮)
        control_buttons_layout = QHBoxLayout()
        self.analyze_button = QPushButton("执行分析")
        self.analyze_button.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        
        # control_buttons_layout.addStretch() # 将按钮推到右侧
        control_buttons_layout.addWidget(self.analyze_button)
        self.expand_all_button = QPushButton("展开全部")
        self.collapse_all_button = QPushButton("折叠全部")
        control_buttons_layout.addWidget(self.expand_all_button)
        control_buttons_layout.addWidget(self.collapse_all_button)
        
        C_layout.addLayout(control_buttons_layout)

        

        
        


        main_layout.addWidget(top_section_container) # 将严格限制高度的组合E添加到主布局

        # --- “分析结果”区域 ---
        results_group = QGroupBox("分析结果")
        results_layout = QVBoxLayout(results_group)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["钻取路径", "告警数量"])
        self.tree.setStyleSheet("QTreeView::item:selected { background-color: #cce8ff; color: black; }")
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(1, Qt.SortOrder.DescendingOrder)
        results_layout.addWidget(self.tree)
        
        # 结果区域的控制按钮 (原有的)
        # 它们现在已经包含在组合A中，所以这里不需要重复
        # tree_control_layout = QHBoxLayout()
        # tree_control_layout.addStretch()
        # self.expand_all_button = QPushButton("展开全部")
        # self.collapse_all_button = QPushButton("折叠全部")
        # tree_control_layout.addWidget(self.expand_all_button)
        # tree_control_layout.addWidget(self.collapse_all_button)
        # results_layout.addLayout(tree_control_layout)

        main_layout.addWidget(results_group)
        main_layout.setStretch(1, 1) # 【关键】让结果区域占据所有剩余的垂直空间

        self._connect_signals()
    
    def _connect_signals(self):
        self.add_button.clicked.connect(self._add_dimension)
        self.remove_button.clicked.connect(self._remove_dimension)
        self.up_button.clicked.connect(self._move_item_up)
        self.down_button.clicked.connect(self._move_item_down)
        
        # 将 analyze_button, expand_all_button, collapse_all_button 的连接从顶部布局移到这里
        self.analyze_button.clicked.connect(self._request_analysis)
        self.expand_all_button.clicked.connect(self.tree.expandAll)
        self.collapse_all_button.clicked.connect(self.tree.collapseAll)

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

    def _move_item_up(self):
        current_row = self.selected_dims_list.currentRow()
        if current_row > 0:
            item = self.selected_dims_list.takeItem(current_row)
            self.selected_dims_list.insertItem(current_row - 1, item)
            self.selected_dims_list.setCurrentRow(current_row - 1)

    def _move_item_down(self):
        current_row = self.selected_dims_list.currentRow()
        if 0 <= current_row < self.selected_dims_list.count() - 1:
            item = self.selected_dims_list.takeItem(current_row)
            self.selected_dims_list.insertItem(current_row + 1, item)
            self.selected_dims_list.setCurrentRow(current_row + 1)

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
        self.tree.setSortingEnabled(False)
        self.tree.clear()
        if not tree_data: 
            self.tree.setSortingEnabled(True)
            return

        level_colors = [
            QColor("#003366"),
            QColor("#8B4513"),
            QColor("#006400"),
            QColor("#483D8B"),
            QColor("#800000"),
        ]
        bold_font = QFont()
        bold_font.setBold(True)

        def build_ui_tree(parent_item, data_node, level):
            if not isinstance(data_node, dict): return
            if level >= len(dimensions): return

            color = level_colors[min(level, len(level_colors) - 1)]

            for key, value_node in data_node.items():
                count = value_node.get('_count', 0)
                children = value_node.get('_children')
                
                display_key = f"{int(key):02d}:00" if dimensions[level] == 'dim_hour' and str(key).isdigit() else str(key)
                
                item = QTreeWidgetItem(parent_item)
                item.setText(0, display_key)
                
                item.setText(1, str(count))
                item.setData(1, Qt.ItemDataRole.UserRole, count)
                
                item.setForeground(0, color)
                item.setForeground(1, color)
                if level == 0:
                    item.setFont(0, bold_font)
                    item.setFont(1, bold_font)

                if children:
                    build_ui_tree(item, children, level + 1)
        
        build_ui_tree(self.tree, tree_data, 0)
        self.tree.expandToDepth(0)
        self.tree.setSortingEnabled(True)