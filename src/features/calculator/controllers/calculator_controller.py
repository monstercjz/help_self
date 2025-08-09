from PySide6.QtCore import QObject
from src.features.calculator.models.calculator_model import CalculatorModel
from src.features.calculator.views.calculator_view import CalculatorView
import logging

class CalculatorController(QObject):
    """
    计算器控制器，连接模型和视图，处理用户交互。
    """
    def __init__(self, model: CalculatorModel, view: CalculatorView, notification_service):
        super().__init__()
        self.model = model
        self.view = view
        self.notification_service = notification_service
        self._connect_signals()
        logging.info("CalculatorController: 初始化完成。")

    def _connect_signals(self):
        """连接视图和模型的信号槽。"""
        self.view.button_clicked.connect(self._handle_button_click)
        self.model.history_updated.connect(self.view.update_history)
        logging.debug("CalculatorController: 信号已连接。")

    def _handle_button_click(self, button_text: str):
        """处理计算器按钮点击事件。"""
        logging.debug(f"CalculatorController: 按钮 '{button_text}' 被点击。")
        if button_text == "=":
            self.model.calculate_result()
        elif button_text == "C":
            self.model.clear_all()
        elif button_text == "DEL":
            self.model.delete_last_char()
        elif button_text == "CLEAR_HISTORY":
            self.model.clear_history()
            self.notification_service.show("历史记录", "历史记录已清空。", level="info")
        else:
            self.model.append_input(button_text)
        
        # 每次按钮点击后更新显示
        self.view.set_expression(self.model.get_current_expression())
        self.view.set_result(self.model.get_current_result())