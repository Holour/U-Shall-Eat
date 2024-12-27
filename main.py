# main.py
import sys
import os
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from src.server import Server
from src.client import Client

def main():
    # 设置 AppUserModelID，确保程序在任务栏中具有唯一标识
    app_id = 'ushalleat.client.app.1.0'  # 使用你自己的应用唯一ID
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

    # 创建 QApplication 实例
    app = QApplication(sys.argv)

    # 获取程序所在路径
    base_path = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_path, "resources", "logo_2.ico")

    # 检查图标文件是否存在
    if not os.path.exists(icon_path):
        print(f"Warning: Icon file not found at {icon_path}")
        return

    # 设置应用图标
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    # 初始化服务器并启动
    server = Server()
    server.start()

    # 初始化客户端窗口并设置相关属性
    client_window = Client(server_host='127.0.0.1', server_port=65432)
    client_window.setWindowIcon(app_icon)  # 确保客户端窗口图标一致
    client_window.setWindowTitle("邮小食——U Small Eat")  # 设置客户端窗口标题
    client_window.show()

    # 启动应用事件循环
    exit_code = app.exec()
    
    # 停止服务器并退出应用
    server.stop()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
