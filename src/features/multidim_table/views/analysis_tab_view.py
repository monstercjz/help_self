from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QAbstractItemView, QComboBox, QPushButton, QTableView, QMessageBox,
    QSplitter, QSizePolicy, QMenu, QLineEdit
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction, QGuiApplication
from PySide6.QtCore import Signal, Qt, QSortFilterProxyModel
import pandas as pd
import re

class RowNumberProxyModel(QSortFilterProxyModel):
    """一个自定义的代理模型，以确保垂直表头始终显示正确的行号。"""
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            # 始终返回视图中的行号（section + 1），忽略源模型的排序
            return str(section + 1)
        return super().headerData(section, orientation, role)

class AnalysisTabView(QWidget):
    """
    数据分析选项卡视图，用于进行数据透视和分析。
    """
    pivot_table_requested = Signal(object)
    custom_analysis_requested = Signal(str)

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

        # --- 自定义分析 ---
        custom_analysis_group = QWidget()
        custom_analysis_layout = QHBoxLayout(custom_analysis_group)
        custom_analysis_layout.setContentsMargins(0, 10, 0, 0)

        custom_analysis_layout.addWidget(QLabel("自定义条件查询:"))
        self.custom_analysis_input = QLineEdit()
        self.custom_analysis_input.setPlaceholderText("对上方结果或原始数据进行筛选, 如: 属性 == '玄' and 门派 == '天龙' and 角色名_10")
        custom_analysis_layout.addWidget(self.custom_analysis_input)

        self.custom_analyze_button = QPushButton("执行条件查询")
        self.custom_analyze_button.clicked.connect(self._on_custom_analyze_data)
        custom_analysis_layout.addWidget(self.custom_analyze_button)
        right_v_layout.addWidget(custom_analysis_group)


        right_v_layout.addWidget(QLabel("分析结果:"))
        
        # 必须先创建模型，再创建使用模型的控件
        self.analysis_result_model = QStandardItemModel()
        self.analysis_result_proxy_model = RowNumberProxyModel()

        # 添加筛选框
        self.analysis_filter_input = QLineEdit()
        self.analysis_filter_input.setPlaceholderText("在此输入以筛选分析结果...")
        self.analysis_filter_input.textChanged.connect(self.analysis_result_proxy_model.setFilterRegularExpression)
        right_v_layout.addWidget(self.analysis_filter_input)
        
        self.analysis_result_view = QTableView()
        self.analysis_result_proxy_model.setSourceModel(self.analysis_result_model)
        self.analysis_result_proxy_model.setFilterKeyColumn(-1)  # 确保可以筛选所有列
        self.analysis_result_proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive) # 不区分大小写
        self.analysis_result_view.setModel(self.analysis_result_proxy_model)
        
        self.analysis_result_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.analysis_result_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.analysis_result_view.setSortingEnabled(True)
        self.analysis_result_view.horizontalHeader().setStretchLastSection(True)
        self.analysis_result_view.setAlternatingRowColors(True)
        self.analysis_result_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.analysis_result_view.customContextMenuRequested.connect(self._show_analysis_context_menu)
        
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

    def _on_custom_analyze_data(self):
        """获取自定义分析语句并发出信号。"""
        query = self.custom_analysis_input.text()
        if not query:
            QMessageBox.warning(self, "警告", "自定义分析语句不能为空。")
            return
        self.custom_analysis_requested.emit(query)

    def populate_analysis_columns(self, columns):
        """填充可用字段列表。"""
        self.available_fields_list.clear()
        self.available_fields_list.addItems(columns)

    def clear_pivot_config_fields(self):
        """清空所有用于透视表配置的字段列表。"""
        self.rows_fields_list.clear()
        self.columns_fields_list.clear()
        self.values_fields_list.clear()

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

    def _show_analysis_context_menu(self, position):
        """显示分析结果表格的右键菜单。"""
        menu = QMenu()
        index = self.analysis_result_view.indexAt(position)

        if not index.isValid():
            return

        # 传递当前点击的索引
        copy_cell_action = QAction("复制单元格内容", self)
        copy_cell_action.triggered.connect(lambda: self._copy_selected_cell(index))
        menu.addAction(copy_cell_action)

        # 复制行的逻辑保持不变，因为它依赖于行选择
        if self.analysis_result_view.selectionModel().hasSelection():
            copy_row_action = QAction("复制整行内容", self)
            copy_row_action.triggered.connect(self._copy_selected_row)
            menu.addAction(copy_row_action)

        menu.exec(self.analysis_result_view.viewport().mapToGlobal(position))

    def _copy_selected_cell(self, index):
        """复制指定索引单元格的内容到剪贴板。"""
        if index.isValid():
            text = index.data()
            QGuiApplication.clipboard().setText(text)

    def _copy_selected_row(self):
        """复制选中行的所有内容到剪贴板，以制表符分隔。"""
        selected_indexes = self.analysis_result_view.selectionModel().selectedRows()
        if not selected_indexes:
            return
        
        # 我们只处理第一行选择，因为通常选择行为是SelectRows
        proxy_row_index = selected_indexes[0]
        source_row_index = self.analysis_result_proxy_model.mapToSource(proxy_row_index)
        
        row_data = []
        for col in range(self.analysis_result_model.columnCount()):
            item = self.analysis_result_model.item(source_row_index.row(), col)
            if item:
                row_data.append(item.text())
        
        QGuiApplication.clipboard().setText("\t".join(row_data))