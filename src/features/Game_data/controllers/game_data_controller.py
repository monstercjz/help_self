# src/features/game_data/controllers/game_data_controller.py

import logging
from src.core.context import ApplicationContext
from src.features.Game_data.models.game_data_model import GameDataModel
from src.features.Game_data.views.game_data_view import GameDataView
from src.features.Game_data.services.game_data_service import GameDataService

class GameDataController:
    """
    控制器，用于连接GameData的Model和View。
    """
    def __init__(self, model: GameDataModel, view: GameDataView, context: ApplicationContext):
        self.model = model
        self.view = view
        self.context = context
        
        # 从模型获取数据库路径，并初始化service
        db_path = self.model.db_path
        self.service = GameDataService(db_path=db_path)
        
        self._connect_signals()
        self._update_view_from_model()

    def _connect_signals(self):
        """连接视图的信号到控制器的槽函数。"""
        self.view.browse_button.clicked.connect(self._on_browse_path)
        self.view.db_browse_button.clicked.connect(self._on_browse_db_path)
        self.view.load_config_button.clicked.connect(self._on_load_config_file)
        self.view.extract_button.clicked.connect(self._on_extract_data)
        self.view.aggregate_button.clicked.connect(self._on_aggregate_files)
        self.view.distribute_button.clicked.connect(self._on_distribute_files)
        
        # 当文本框内容改变时，自动更新模型
        self.view.path_line_edit.textChanged.connect(self._on_path_changed)
        self.view.db_path_line_edit.textChanged.connect(self._on_db_path_changed)
        # 不再需要监听config_text_edit的变化，因为它是由文件加载的
        # self.view.config_text_edit.textChanged.connect(self._on_config_changed)

    def _update_view_from_model(self):
        """用模型的数据初始化视图。"""
        self.view.set_root_path(self.model.root_path)
        self.view.set_db_path(self.model.db_path)
        self.view.set_config_path_display(self.model.config_path) # 更新路径显示
        self.view.set_config_text(self.model.config_text)
        self.view.append_log("游戏数据工具已就绪。")

    def _on_browse_path(self):
        """处理浏览按钮点击事件。"""
        directory = self.view.select_directory()
        if directory:
            self.view.set_root_path(directory)

    def _on_browse_db_path(self):
        """处理数据库浏览按钮点击事件。"""
        db_file = self.view.select_db_file()
        if db_file:
            self.view.set_db_path(db_file)

    def _on_path_changed(self, text: str):
        """处理路径文本框变化事件，并立即保存。"""
        self.model.root_path = text
        self.model.save_settings()

    def _on_db_path_changed(self, text: str):
        """处理数据库路径文本框变化事件，并立即保存。"""
        self.model.db_path = text
        # 同步更新 service 中的 db_path，确保数据源一致
        if self.service:
            self.service.db_path = text
            logging.info(f"GameDataService 的数据源已更新为: {text}")
        self.model.save_settings()

    def _on_load_config_file(self):
        """处理加载配置文件按钮点击事件，并立即保存。"""
        config_file = self.view.select_config_file()
        if config_file:
            self.model.config_path = config_file
            # 模型setter会自动调用load_config_from_file，我们只需更新视图
            self.view.set_config_path_display(config_file) # 更新路径显示
            self.view.set_config_text(self.model.config_text)
            self.model.save_settings()

    def _execute_service_action(self, action, action_name: str):
        """通用服务执行模板。"""
        self.view.clear_log()
        self.view.append_log(f"开始执行 '{action_name}' 操作...")
        logging.info(f"开始执行 '{action_name}' 操作...")
        
        try:
            # 设置已在变更时保存，此处无需重复保存
            root_path = self.model.root_path
            config = self.model.get_parsed_config()
            
            if not root_path or not config:
                self.view.append_log("错误：根目录或配置信息不能为空。")
                logging.error("根目录或配置信息为空，操作中止。")
                return
            
            # 调用具体的服务方法
            if action_name == "提取账号信息":
                db_config = {
                    'table_name': self.model.db_table_name,
                    'member_col': self.model.db_member_col,
                    'account_col': self.model.db_account_col
                }
                action(root_path, config, db_config)
            else:
                action(root_path, config)
            
            self.view.append_log(f"'{action_name}' 操作成功完成。")
            logging.info(f"'{action_name}' 操作成功完成。")
            
        except Exception as e:
            self.view.append_log(f"错误：'{action_name}' 操作失败。详情请查看日志。")
            logging.error(f"执行 '{action_name}' 操作时发生异常: {e}", exc_info=True)

    def _on_extract_data(self):
        """处理提取数据按钮点击事件。"""
        self._execute_service_action(self.service.extract_data, "提取账号信息")

    def _on_aggregate_files(self):
        """处理汇总文件按钮点击事件。"""
        self._execute_service_action(self.service.aggregate_files, "汇总角色配置")

    def _on_distribute_files(self):
        """处理分发文件按钮点击事件。"""
        self._execute_service_action(self.service.distribute_files, "分发角色配置")
