# desktop_center/src/features/window_arranger/views/arranger_page_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                   QGroupBox, QFormLayout, QLabel,
                                   QListWidget, QListWidgetItem, QLineEdit,
                                   QAbstractItemView)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon

class ArrangerPageView(QWidget):
    """
    桌面窗口排列功能的主UI页面。
    """
    detect_windows_requested = Signal()
    open_settings_requested = Signal()
    toggle_monitoring_requested = Signal(bool)
    arrange_grid_requested = Signal()
    arrange_cascade_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("窗口排列器")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 0, 15, 15)
        main_layout.setSpacing(10)
        
        toolbar_container = QWidget()
        toolbar_container.setObjectName("ToolbarContainer")
        toolbar_container.setStyleSheet("#ToolbarContainer { background-color: #F8F8F8; border-top: 1px solid #E0E0E0; border-bottom: 1px solid #E0E0E0; }")
        toolbar_container.setContentsMargins(15, 10, 15, 10)
        toolbar_container.setFixedHeight(60)

        header_layout = QHBoxLayout(toolbar_container)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # header_layout = QHBoxLayout()
        title_label = QLabel("桌面窗口排列")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; ")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.monitor_toggle_button = QPushButton(" 启动自动监控 ")
        # try:
        #     monitor_toggle_button_icon = self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay)
        #     self.monitor_toggle_button.setIcon(monitor_toggle_button_icon)
        # except:
        #     pass
        self.monitor_toggle_button.setCheckable(True)
        self.monitor_toggle_button.setMinimumHeight(30)
        self.monitor_toggle_button.toggled.connect(self.toggle_monitoring_requested.emit)
        self.set_monitoring_status(False)
        header_layout.addWidget(self.monitor_toggle_button)
        
        self.settings_button = QPushButton(" 排列设置 ")
        try:
            settings_icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView)
            self.settings_button.setIcon(settings_icon)
        except:
            pass
        self.settings_button.setMinimumHeight(30)
        self.settings_button.clicked.connect(self.open_settings_requested.emit)
        header_layout.addWidget(self.settings_button)
        main_layout.addWidget(toolbar_container)
        
        filter_group = QGroupBox("设置窗口进程名字及过滤条件")
        filter_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #CE13F3; /* 这是组内文本颜色 */
                margin-top: 10px;

                /* --- 以下是新增的边框设置 --- */
                border: 2px solid #E0E0E0; /* 设置2px实线边框，颜色为#eea00f */
                border-radius: 5px; /* 可选：设置圆角 */
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                left: 10px;
                /* 如果您想让标题背景也与边框颜色一致，可以给title设置background-color */
                /* background-color: #eea00f; */
            }
        """)
        filter_layout = QFormLayout(filter_group)
        filter_layout.setSpacing(0)
        filter_layout.setVerticalSpacing(2)
        filter_layout.setContentsMargins(20, 30, 20, 20)
        target_height = 30
        fixed_label_width = 100
        self.process_name_input = QLineEdit()
        self.process_name_input.setPlaceholderText("输入进程名, 用逗号分隔多个")
        self.process_name_input.setFixedHeight(target_height)
        placeholder_color = "#CE13F3"

        self.process_name_input.setStyleSheet(f"""
            QLineEdit {{
                color: #ffffff;
                background-color: #3498db;
                /* 移除或将所有边框设置为none */
                border: none;
                /* 或者具体设置每个边的边框为none */
                /* border-top: none; */
                /* border-left: none; */
                /* border-right: none; */

                /* 只设置底部边框 */
                /* border-bottom: 0.5px solid #ffffff;  边框样式 */
                
                padding: 1px; /* 内边距，让文本不贴着边框 */
                selection-background-color: #aaddff;
                selection-color: #000000;
                border-top-left-radius: 0px;    /* 左上角圆角 */
                border-bottom-left-radius: 0px; /* 左下角圆角 */
                border-top-right-radius: 5px;   /* 右上角直角 */
                border-bottom-right-radius: 5px;/* 右下角直角 */
            }}
            /* PlaceholderText 样式 (注意，这个伪元素在旧版本Qt上可能不支持或支持不全) */
            QLineEdit::placeholder {{
                color: {placeholder_color};
            }}
        """)

        process_name_label = QLabel("进程名称: ")
        
        process_name_label.setFixedWidth(fixed_label_width)
        process_name_label.setFixedHeight(target_height)
        process_name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                /* 移除或将所有边框设置为none */
                border: none;
                /* 或者具体设置每个边的边框为none */
                /* border-top: none; */
                /* border-left: none; */
                /* border-right: none; */

                /* 只设置底部边框 */
                /* border-bottom: 0.5px solid #ffffff;  边框样式 */
                font-weight: bold;
                font-style: normal;
                font-family: "Microsoft YaHei UI";
                text-decoration: none;
                background-color: #3498db;
                padding: 4px 8px;
                border-top-left-radius: 5px;    /* 左上角圆角 */
                border-bottom-left-radius: 5px; /* 左下角圆角 */
                border-top-right-radius: 0px;   /* 右上角直角 */
                border-bottom-right-radius: 0px;/* 右下角直角 */
            }
        """)

        # 将样式化后的 QLabel 添加到 QFormLayout
        filter_layout.addRow(process_name_label, self.process_name_input)

        # filter_layout.addRow("进程名称:", self.process_name_input)

        self.filter_keyword_input = QLineEdit()
        self.filter_keyword_input.setPlaceholderText("输入标题关键词, 用逗号分隔多个")
        self.filter_keyword_input.setFixedHeight(target_height)
        self.filter_keyword_input.setStyleSheet(f"""
            QLineEdit {{
                
                color: #ffffff;
                background-color: #3b5998;
                /* 移除或将所有边框设置为none */
                border: none;
                /* 或者具体设置每个边的边框为none */
                /* border-top: none; */
                /* border-left: none; */
                /* border-right: none; */

                /* 只设置底部边框 */
                /* border-bottom: 0.5px solid #ffffff;  边框样式 */
                
                padding: 1px; /* 内边距，让文本不贴着边框 */
                selection-background-color: #aaddff;
                selection-color: #000000;
                border-top-left-radius: 0px;    /* 左上角圆角 */
                border-bottom-left-radius: 0px; /* 左下角圆角 */
                border-top-right-radius: 5px;   /* 右上角直角 */
                border-bottom-right-radius: 5px;/* 右下角直角 */
            }}
            /* PlaceholderText 样式 (注意，这个伪元素在旧版本Qt上可能不支持或支持不全) */
            QLineEdit::placeholder {{
                color: {placeholder_color};
            }}
        """)

        filter_keyword_label = QLabel("标题关键词:")
        filter_keyword_label.setFixedWidth(fixed_label_width)
        filter_keyword_label.setFixedHeight(target_height)
        filter_keyword_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                /* 移除或将所有边框设置为none */
                border: none;
                /* 或者具体设置每个边的边框为none */
                /* border-top: none; */
                /* border-left: none; */
                /* border-right: none; */

                /* 只设置底部边框 */
                /* border-bottom: 0.5px solid #ffffff;  边框样式 */
                font-weight: bold;
                font-style: normal;
                font-family: "Microsoft YaHei UI";
                text-decoration: none;
                background-color: #3b5998;
                padding: 4px 8px;
                border-top-left-radius: 5px;    /* 左上角圆角 */
                border-bottom-left-radius: 5px; /* 左下角圆角 */
                border-top-right-radius: 0px;   /* 右上角直角 */
                border-bottom-right-radius: 0px;/* 右下角直角 */
            }
        """)

        # 将样式化后的 QLabel 添加到 QFormLayout
        filter_layout.addRow(filter_keyword_label, self.filter_keyword_input)
        # filter_layout.addRow("标题关键词:", self.filter_keyword_input)
        
        
        self.exclude_title_input = QLineEdit()
        self.exclude_title_input.setPlaceholderText("输入要排除的标题关键词，用逗号分隔")
        self.exclude_title_input.setFixedHeight(target_height)
        self.exclude_title_input.setStyleSheet(f"""
            QLineEdit {{
                
                color: #ffffff;
                background-color: #e74c3c;
                /* 移除或将所有边框设置为none */
                border: none;
                /* 或者具体设置每个边的边框为none */
                /* border-top: none; */
                /* border-left: none; */
                /* border-right: none; */

                /* 只设置底部边框 */
                /* border-bottom: 0.5px solid #ffffff;  边框样式 */
                
                padding: 1px; /* 内边距，让文本不贴着边框 */
                selection-background-color: #aaddff;
                selection-color: #000000;
                border-top-left-radius: 0px;    /* 左上角圆角 */
                border-bottom-left-radius: 0px; /* 左下角圆角 */
                border-top-right-radius: 5px;   /* 右上角直角 */
                border-bottom-right-radius: 5px;/* 右下角直角 */                               
            }}
            /* PlaceholderText 样式 (注意，这个伪元素在旧版本Qt上可能不支持或支持不全) */
            QLineEdit::placeholder {{
                color: {placeholder_color};
            }}
        """)
        exclude_title_label = QLabel("排除标题包含: ")
        exclude_title_label.setFixedWidth(fixed_label_width)
        exclude_title_label.setFixedHeight(target_height)
        exclude_title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                /* 移除或将所有边框设置为none */
                border: none;
                /* 或者具体设置每个边的边框为none */
                /* border-top: none; */
                /* border-left: none; */
                /* border-right: none; */

                /* 只设置底部边框 */
                /* border-bottom: 0.5px solid #ffffff;  边框样式 */                      
                font-weight: bold;
                font-style: normal;
                font-family: "Microsoft YaHei UI";
                text-decoration: none;
                background-color: #e74c3c;
                padding: 4px 8px;
                border-top-left-radius: 5px;    /* 左上角圆角 */
                border-bottom-left-radius: 5px; /* 左下角圆角 */
                border-top-right-radius: 0px;   /* 右上角直角 */
                border-bottom-right-radius: 0px;/* 右下角直角 */
            }
        """)

        # 将样式化后的 QLabel 添加到 QFormLayout
        filter_layout.addRow(exclude_title_label, self.exclude_title_input)

        # filter_layout.addRow("排除标题包含:", self.exclude_title_input)
        
        main_layout.addWidget(filter_group)

        self.windows_list_group = QGroupBox()
        self.windows_list_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #eea00f; /* 这是组内文本颜色 */
                margin-top: 10px;
                /* --- 以下是新增的边框设置 --- */
                border: 2px solid #E0E0E0; /* 设置2px实线边框，颜色为#eea00f */
                border-radius: 5px; /* 可选：设置圆角 */
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                left: 10px;
                /* 如果您想让标题背景也与边框颜色一致，可以给title设置background-color */
                /* background-color: #eea00f; */
            }
        """)
        # self.windows_list_group.setStyleSheet("QGroupBox { margin-top: 10px; }")
        windows_list_layout = QVBoxLayout(self.windows_list_group)
        windows_list_layout.setContentsMargins(15, 15, 15, 15)

        self.summary_label = QLabel("请先点击检测窗口")
        self.summary_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f50f6f; margin-bottom: 5px;")
        windows_list_layout.addWidget(self.summary_label)

        self.detected_windows_list_widget = QListWidget()
        self.detected_windows_list_widget.setMinimumHeight(250)
        self.detected_windows_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # self.detected_windows_list_widget.setStyleSheet("QListWidget { border: 1px solid #E0E0E0; border-radius: 5px; padding: 5px; } QListWidget::item { padding: 5px; } QListWidget::indicator { width: 16px; height: 16px; }")
        self.detected_windows_list_widget.setStyleSheet(
            "QListWidget {"
            "   border: 2px solid #E0E0E0;"
            "   border-radius: 5px;"
            "   padding: 5px;"
            #"   background-color: #444444;"
            #"   color: #ffffff;"
            "}"
            "QListWidget::item {"
            "   padding: 5px;"
            "}"
            "QListWidget::indicator {"
            "   width: 16px;"
            "   height: 16px;"
            "}"
        )
        windows_list_layout.addWidget(self.detected_windows_list_widget)
        
        detect_button = QPushButton("检测桌面窗口")
        detect_button.setMinimumHeight(30)
        detect_button.setStyleSheet("QPushButton { font-size: 14px; background-color: #5cb85c; color: white; border: none; border-radius: 5px; padding: 5px 15px; } QPushButton:hover { background-color: #4cae4c; } QPushButton:pressed { background-color: #449d44; }")
        detect_button.clicked.connect(self.detect_windows_requested.emit)
        windows_list_layout.addWidget(detect_button)
        main_layout.addWidget(self.windows_list_group)

        action_buttons_layout = QHBoxLayout()
        self.arrange_cascade_button = QPushButton("级联排列")
        self.arrange_cascade_button.setMinimumHeight(35)
        self.arrange_cascade_button.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; background-color: #17a2b8; color: white; border: none; border-radius: 5px; padding: 0 20px; } QPushButton:hover { background-color: #138496; } QPushButton:pressed { background-color: #117a8b; }")
        self.arrange_cascade_button.clicked.connect(self.arrange_cascade_requested.emit)
        action_buttons_layout.addWidget(self.arrange_cascade_button)
        main_layout.addLayout(action_buttons_layout)

        self.arrange_grid_button = QPushButton("网格排列")
        self.arrange_grid_button.setMinimumHeight(35)
        self.arrange_grid_button.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; background-color: #007bff; color: white; border: none; border-radius: 5px; padding: 0 20px; } QPushButton:hover { background-color: #0056b3; } QPushButton:pressed { background-color: #004085; }")
        self.arrange_grid_button.clicked.connect(self.arrange_grid_requested.emit)
        action_buttons_layout.addWidget(self.arrange_grid_button)
        
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("color: #666; font-style: italic; margin-top: 5px;")
        self.status_label.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.status_label)

        main_layout.addStretch(1)
        
    def set_monitoring_status(self, is_monitoring: bool):
        """更新监控按钮的视觉状态。"""
        # Block signals to prevent emitting toggled signal when we set state programmatically
        self.monitor_toggle_button.blockSignals(True)
        self.monitor_toggle_button.setChecked(is_monitoring)
        self.monitor_toggle_button.blockSignals(False)

        if is_monitoring:
            self.monitor_toggle_button.setText("停止自动监控")
            try:
                monitor_toggle_button_icon = self.style().standardIcon(self.style().StandardPixmap.SP_MediaStop)
                self.monitor_toggle_button.setIcon(monitor_toggle_button_icon)
            except:
                pass
            self.monitor_toggle_button.setStyleSheet("background-color: transparent; color: red; font-weight: bold;")
        else:
            self.monitor_toggle_button.setText("启动自动监控")
            try:
                monitor_toggle_button_icon = self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay)
                self.monitor_toggle_button.setIcon(monitor_toggle_button_icon)
            except:
                pass
            self.monitor_toggle_button.setStyleSheet("") # 恢复默认样式
    
    def update_detected_windows_list(self, window_infos: list[object]):
        """更新UI上的检测到的窗口列表，并为每个项目添加复选框。"""
        self.detected_windows_list_widget.clear()
        if not window_infos:
            self.detected_windows_list_widget.addItem("未检测到符合条件的窗口。")
        else:
            for win_info in window_infos:
                # 【重构】使用模型中的新属性来获取显示文本，将显示逻辑从视图中剥离
                display_text = f"{win_info.title} (进程: {win_info.display_process_name})"
                item = QListWidgetItem(display_text)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                item.setData(Qt.UserRole, win_info)
                self.detected_windows_list_widget.addItem(item)
    
    def get_selected_window_infos(self) -> list[object]:
        """获取当前列表中所有被勾选的窗口的 WindowInfo 对象。"""
        selected_windows = []
        for i in range(self.detected_windows_list_widget.count()):
            item = self.detected_windows_list_widget.item(i)
            if item.checkState() == Qt.Checked:
                window_info = item.data(Qt.UserRole)
                if window_info:
                    selected_windows.append(window_info)
        return selected_windows

    def get_filter_keyword(self) -> str:
        """获取当前设置的窗口标题过滤关键词。"""
        return self.filter_keyword_input.text().strip()

    def get_process_name_filter(self) -> str:
        """获取当前设置的进程名过滤关键词。"""
        return self.process_name_input.text().strip()
    
    def get_exclude_keywords(self) -> str:
        """获取排除关键词字符串。"""
        return self.exclude_title_input.text().strip()