# src/features/multidim_table/views/statistics_tab_view.py
from PySide6.QtWidgets import QVBoxLayout, QWidget, QTableView, QHeaderView, QPushButton, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
import pandas as pd

class PandasTableModel(QAbstractTableModel):
    """
    一个用于将 Pandas DataFrame 显示在 QTableView 中的模型。
    """
    def __init__(self, dataframe: pd.DataFrame = pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._dataframe = dataframe

    def rowCount(self, parent=QModelIndex()):
        return self._dataframe.shape[0]

    def columnCount(self, parent=QModelIndex()):
        return self._dataframe.shape[1]

    def data(self, index: QModelIndex, role: int):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return str(self._dataframe.iloc[index.row(), index.column()])
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._dataframe.columns[section])
            elif orientation == Qt.Vertical:
                # 如果有行索引，可以显示行索引
                # return str(self._dataframe.index[section])
                return str(section + 1) # 默认显示行号
        return None

    def set_dataframe(self, dataframe: pd.DataFrame):
        self.beginResetModel()
        self._dataframe = dataframe
        self.endResetModel()

class StatisticsTabView(QWidget):
    """
    用于显示统计结果的标签页。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- 顶部控制区 ---
        top_control_layout = QHBoxLayout()
        
        self.config_path_label = QLabel("当前配置: (默认)")
        self.config_path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        self.load_config_button = QPushButton("加载配置")
        self.edit_config_button = QPushButton("编辑当前配置")
        self.calculate_button = QPushButton("执行计算")

        top_control_layout.addWidget(self.config_path_label)
        top_control_layout.addStretch()
        top_control_layout.addWidget(self.load_config_button)
        top_control_layout.addWidget(self.edit_config_button)
        top_control_layout.addWidget(self.calculate_button)

        self.table_view = QTableView()
        self.table_model = PandasTableModel()
        self.table_view.setModel(self.table_model)

        # 调整列宽以适应内容
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        layout.addLayout(top_control_layout)
        layout.addWidget(self.table_view)

    def set_config_path(self, path: str):
        """更新显示的配置文件路径。"""
        self.config_path_label.setText(f"当前配置: {path}")
        self.config_path_label.setToolTip(path) # 完整路径作为提示

    def display_statistics_data(self, dataframe: pd.DataFrame):
        """
        设置并显示统计数据。
        """
        self.table_model.set_dataframe(dataframe)