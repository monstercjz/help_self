from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QAbstractItemView, QComboBox, QPushButton, QTableView, QMessageBox,
    QSplitter, QSizePolicy
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Signal, Qt, QSortFilterProxyModel
import pandas as pd
import re

class AnalysisTabView(QWidget):
    """
    数据分析选项卡视图，用于进行数据透视和分析。
    """
    pivot_table_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 顶部工具栏，包含切换设置面板的按钮
        top_toolbar_layout = QHBoxLayout()
        self.toggle_settings_button = QPushButton("显示/隐藏设置面板")
        self.toggle_settings_button.clicked.connect(self._toggle_settings_panel)
        top_toolbar_layout.addWidget(self.toggle_settings_button)
        top_toolbar_layout.addStretch()
        layout.addLayout(top_toolbar_layout)

        # 使用 QSplitter 来管理设置面板和分析结果的布局
        self.splitter = QSplitter(Qt.Horizontal)
        
        # --- 设置面板 ---
        self.settings_panel = QWidget()
        settings_layout = QVBoxLayout(self.settings_panel)
        
        # 左侧：可用字段列表
        left_v_layout = QVBoxLayout()
        left_v_layout.addWidget(QLabel("可用字段:"))
        self.available_fields_list = QListWidget()
        self.available_fields_list.setDragEnabled(True)
        self.available_fields_list.setDragDropMode(QListWidget.DragDrop)
        self.available_fields_list.setDefaultDropAction(Qt.MoveAction)
        self.available_fields_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        left_v_layout.addWidget(self.available_fields_list)
        settings_layout.addLayout(left_v_layout, 2) # 设置伸展因子为2

        # 中间：行、列、值字段区域
        center_v_layout = QVBoxLayout()

        # 行字段
        center_v_layout.addWidget(QLabel("行字段 (Rows): <small>（将源数据字段拖放到此处，作为透视表的行索引）</small>"))
        self.rows_fields_list = QListWidget()
        self.rows_fields_list.setAcceptDrops(True)
        self.rows_fields_list.setDropIndicatorShown(True)
        self.rows_fields_list.setDragDropMode(QListWidget.DragDrop)
        self.rows_fields_list.setDefaultDropAction(Qt.MoveAction)
        self.rows_fields_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        center_v_layout.addWidget(self.rows_fields_list)

        # 列字段
        center_v_layout.addWidget(QLabel("列字段 (Columns): <small>（将源数据字段拖放到此处，作为透视表的列索引）</small>"))
        self.columns_fields_list = QListWidget()
        self.columns_fields_list.setAcceptDrops(True)
        self.columns_fields_list.setDropIndicatorShown(True)
        self.columns_fields_list.setDragDropMode(QListWidget.DragDrop)
        self.columns_fields_list.setDefaultDropAction(Qt.MoveAction)
        self.columns_fields_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        center_v_layout.addWidget(self.columns_fields_list)

        # 值字段
        center_v_layout.addWidget(QLabel("值字段 (Values): <small>（将数值字段拖放到此处进行聚合计算）</small>"))
        self.values_fields_list = QListWidget()
        self.values_fields_list.setAcceptDrops(True)
        self.values_fields_list.setDropIndicatorShown(True)
        self.values_fields_list.setDragDropMode(QListWidget.DragDrop)
        self.values_fields_list.setDefaultDropAction(Qt.MoveAction)
        self.values_fields_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        center_v_layout.addWidget(self.values_fields_list)

        settings_layout.addLayout(center_v_layout, 1) # 设置伸展因子为1
        self.splitter.addWidget(self.settings_panel)

        # --- 分析结果显示 ---
        self.analysis_result_view_container = QWidget()
        right_v_layout = QVBoxLayout(self.analysis_result_view_container)

        # 聚合函数选择和分析按钮（移动到这里）
        agg_func_and_analyze_layout = QHBoxLayout()
        agg_func_and_analyze_layout.addWidget(QLabel("聚合函数:"))
        self.agg_func_combo = QComboBox()
        self.agg_func_combo.addItems(["求和 (sum)", "平均值 (mean)", "计数 (count)", "最小值 (min)", "最大值 (max)"])
        self.agg_func_combo.setCurrentText("求和 (sum)")
        agg_func_and_analyze_layout.addWidget(self.agg_func_combo)
        self.analyze_button = QPushButton("执行分析")
        self.analyze_button.clicked.connect(self._on_analyze_data)
        agg_func_and_analyze_layout.addWidget(self.analyze_button)
        agg_func_and_analyze_layout.addStretch()
        right_v_layout.addLayout(agg_func_and_analyze_layout)

        right_v_layout.addWidget(QLabel("分析结果:"))
        
        self.analysis_result_view = QTableView()
        self.analysis_result_model = QStandardItemModel()
        self.analysis_result_proxy_model = QSortFilterProxyModel()
        self.analysis_result_proxy_model.setSourceModel(self.analysis_result_model)
        self.analysis_result_view.setModel(self.analysis_result_proxy_model)
        
        self.analysis_result_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.analysis_result_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.analysis_result_view.setSortingEnabled(True)
        self.analysis_result_view.horizontalHeader().setStretchLastSection(True)
        self.analysis_result_view.setAlternatingRowColors(True)
        
        right_v_layout.addWidget(self.analysis_result_view)
        self.splitter.addWidget(self.analysis_result_view_container)

        self.initial_sizes_set = False
        self.showEvent = self._initial_show_event

        layout.addWidget(self.splitter)

    def _initial_show_event(self, event):
        """在窗口首次显示时设置 QSplitter 的初始大小。"""
        if not self.initial_sizes_set:
            self.splitter.setSizes([self.width() // 3, self.width() * 2 // 3])
            self.initial_sizes_set = True
        super().showEvent(event)

    def _toggle_settings_panel(self):
        """切换设置面板的可见性。"""
        is_visible = self.settings_panel.isVisible()
        if is_visible:
            self.settings_panel.hide()
            self.splitter.setSizes([0, self.splitter.width()])
        else:
            self.settings_panel.show()
            self.splitter.setSizes([self.splitter.width() // 3, self.splitter.width() * 2 // 3])

    def _on_analyze_data(self):
        """收集透视表配置并发出信号。"""
        rows = [self.rows_fields_list.item(i).text() for i in range(self.rows_fields_list.count())]
        columns = [self.columns_fields_list.item(i).text() for i in range(self.columns_fields_list.count())]
        values = [self.values_fields_list.item(i).text() for i in range(self.values_fields_list.count())]
        
        selected_agg_func_text = self.agg_func_combo.currentText()
        match = re.search(r'\((.*?)\)', selected_agg_func_text)
        aggfunc = match.group(1) if match else "sum"

        pivot_config = {
            "rows": rows,
            "columns": columns,
            "values": values,
            "aggfunc": aggfunc
        }
        self.pivot_table_requested.emit(pivot_config)

    def populate_analysis_columns(self, columns):
        """填充可用字段列表。"""
        self.available_fields_list.clear()
        self.available_fields_list.addItems(columns)

    def display_analysis_result(self, result):
        """
        显示分析结果。
        result 可以是 pandas.DataFrame 或字符串（错误信息）。
        """
        self.analysis_result_model.clear()
        if isinstance(result, pd.DataFrame):
            if result.empty:
                self.analysis_result_model.setHorizontalHeaderLabels(["无结果"])
                return

            headers = result.columns.tolist()
            self.analysis_result_model.setHorizontalHeaderLabels(headers)
            
            result_filled = result.fillna('')
            
            for r_idx, row_data in result_filled.iterrows():
                row_items = [QStandardItem(str(item)) for item in row_data]
                self.analysis_result_model.appendRow(row_items)
            
            self.analysis_result_view.resizeColumnsToContents()
        elif isinstance(result, str):
            self.analysis_result_model.setHorizontalHeaderLabels(["错误/信息"])
            item = QStandardItem(result)
            self.analysis_result_model.appendRow(item)
        else:
            self.analysis_result_model.setHorizontalHeaderLabels(["未知结果类型"])
            item = QStandardItem(str(result))
            self.analysis_result_model.appendRow(item)