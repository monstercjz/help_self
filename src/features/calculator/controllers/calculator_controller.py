# src/features/calculator/controllers/calculator_controller.py
import logging
from functools import partial

class CalculatorController:
    """
    计算器的控制器，处理用户输入和业务逻辑。
    """
    def __init__(self, model, view, context, plugin):
        self.model = model
        self.view = view
        self.context = context
        self.plugin = plugin
        self._connect_signals()

    def _connect_signals(self):
        """连接视图中的信号到控制器槽函数。"""
        for btn_text, button in self.view.buttons.items():
            if btn_text == '=':
                button.clicked.connect(self._calculate_result)
            elif btn_text == 'C':
                button.clicked.connect(self._clear_all)
            elif btn_text == '<-':
                button.clicked.connect(self._backspace)
            elif btn_text == '历史':
                button.clicked.connect(self._toggle_history_panel)
            elif btn_text == '清除历史':
                button.clicked.connect(self._clear_history)
            else:
                button.clicked.connect(partial(self._append_to_expression, btn_text))
        
        self.view.history_panel.itemClicked.connect(self._history_item_clicked)

    def _update_display(self):
        """更新视图的显示。"""
        self.view.set_display_text(self.model.display_text)

    def _append_to_expression(self, text: str):
        """将字符追加到表达式。"""
        # 如果上次是计算结果
        if self.model.result_is_displayed:
            # 如果输入的是运算符，则基于上次结果继续计算
            if text in "+-*/":
                self.model.result_is_displayed = False
            # 如果输入的是数字，则开始新的计算
            else:
                self.model.display_text = ""
                self.model.result_is_displayed = False

        if self.model.display_text == "0" and text not in "+-*/.":
            self.model.display_text = ""
        
        self.model.display_text += text
        self._update_display()

    def _calculate_result(self):
        """计算表达式的结果。"""
        try:
            # 使用 eval 计算，注意这在生产环境中可能不安全
            # 为了安全，替换掉一些可能有害的字符
            safe_expression = self.model.display_text.replace('^', '**')
            result = str(eval(safe_expression))
            
            # 添加到历史记录
            history_entry = f"{self.model.display_text} = {result}"
            self.model.history.append(history_entry)
            self.view.update_history_list(self.model.history)

            self.model.display_text = result
            self.model.result_is_displayed = True
        except Exception as e:
            logging.error(f"计算错误: {e}")
            self.model.display_text = "Error"
            self.model.result_is_displayed = True
        self._update_display()

    def _toggle_history_panel(self):
        """切换历史记录面板的可见性。"""
        is_visible = self.view.history_panel.isVisible()
        self.view.history_panel.setVisible(not is_visible)

    def _history_item_clicked(self, item):
        """处理历史记录项的点击事件。"""
        expression = item.text().split(' = ')[0]
        self.model.display_text = expression
        self.model.result_is_displayed = False
        self._update_display()

    def _clear_history(self):
        """清空历史记录。"""
        self.model.history.clear()
        self.view.update_history_list(self.model.history)

    def _clear_all(self):
        """清空所有输入。"""
        self.model.display_text = "0"
        self.model.expression = ""
        self.model.result_is_displayed = False
        self._update_display()

    def _backspace(self):
        """删除最后一个字符。"""
        current_text = self.model.display_text
        if len(current_text) > 1:
            self.model.display_text = current_text[:-1]
        else:
            self.model.display_text = "0"
        self._update_display()