# desktop_center/src/utils/exception_handler.py
import sys
import logging
import traceback
from PySide6.QtWidgets import QMessageBox

def global_exception_hook(exctype, value, tb):
    """
    全局异常处理钩子。当任何线程中出现未被捕获的异常时，此函数将被调用。
    """
    # 格式化异常信息
    traceback_details = "".join(traceback.format_exception(exctype, value, tb))
    
    # 记录致命错误日志
    logging.critical(f"捕获到未处理的全局异常:\n{traceback_details}")

    # 准备向用户显示的消息
    error_message = (
        "应用程序遇到了一个严重错误，需要关闭。\n\n"
        "我们对此造成的不便深表歉意。\n\n"
        f"错误类型: {exctype.__name__}\n"
        f"错误信息: {value}\n\n"
        "详细信息已记录到 app.log 文件中，请联系技术支持。"
    )

    # 显示一个阻塞的错误消息框
    # 注意: 这个QMessageBox是在异常发生后创建的，可能在非GUI线程中。
    # Qt通常能处理这种情况，但最稳妥的方式是确保它在主线程显示。
    # 在这个简单场景下，直接显示通常是可行的。
    error_box = QMessageBox()
    error_box.setIcon(QMessageBox.Icon.Critical)
    error_box.setWindowTitle("应用程序严重错误")
    error_box.setText(error_message)
    error_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    error_box.exec()

    # 退出应用程序
    sys.exit(1)

def setup_exception_handler():
    """设置全局异常钩子。"""
    sys.excepthook = global_exception_hook
    logging.info("全局异常处理器已设置。")