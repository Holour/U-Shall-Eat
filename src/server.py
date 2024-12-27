# server.py

import socket
import threading
import json
import os
import datetime
import logging
from PyQt5.QtCore import QObject, pyqtSignal

# 导入Robot和DSLParser
from src.robot import Robot
from dsl.parser import DSLParser


class Server(QObject):
    """
    服务器类，负责监听客户端连接，处理消息，并与机器人进行交互。
    """
    # 定义一个信号，用于将接收到的消息发送到主线程
    message_received = pyqtSignal(str)

    def __init__(self, host: str = '127.0.0.1', port: int = 65432):
        """
        初始化服务器对象，设置主机和端口，初始化机器人和解析器，
        配置日志，并准备启动服务器线程。
        
        :param host: 服务器主机地址
        :param port: 服务器监听端口
        """
    def __init__(self, host: str = '127.0.0.1', port: int = 65432):
        """
        初始化服务器对象，设置主机和端口，初始化机器人和解析器，
        配置日志，并准备启动服务器线程。
        
        :param host: 服务器主机地址
        :param port: 服务器监听端口
        """
        super().__init__()
        self.host = host
        self.port = port
        self.is_running = False  # 标志位，指示服务器是否正在运行
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)

        # 初始化机器人和DSL解析器
        self.robot = Robot()
        self.parser = DSLParser(self.robot)

        # 设置日志相关
        self.log_directory = "logs"
        self.log_file_path = os.path.join(self.log_directory, "chat.log")
        self.log_lock = threading.Lock()  # 日志文件访问锁
        self.ensure_log_directory()

        # 配置调试日志（终端输出）
        self.setup_debug_logging()
    def ensure_log_directory(self):
        """
        确保日志目录存在，如果不存在则创建。
        """
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)
            self.debug_logger.info(f"日志目录已创建: {self.log_directory}")

    def setup_debug_logging(self):
        """
        配置调试日志，仅输出到终端。
        """
        self.debug_logger = logging.getLogger("ServerDebugLogger")
        self.debug_logger.setLevel(logging.DEBUG)  # 设置最低日志级别

        # 创建控制台日志处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # 定义日志输出格式
        formatter = logging.Formatter(
            fmt='[%(levelname)s] %(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        # 添加处理器到记录器
        self.debug_logger.addHandler(console_handler)

    def log_message(self, speaker: str, message: str):
        """
        将对话消息记录到日志文件中。

        :param speaker: 消息发送者，如“机器人”或“用户”
        :param message: 消息内容
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"{speaker},{timestamp},{message}\n"
        with self.log_lock:
            with open(self.log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write(log_entry)
        self.debug_logger.debug(f"已记录消息: {log_entry.strip()}")

    def start(self):
        """
        启动服务器线程，开始监听客户端连接。
        """
        self.is_running = True
        self.server_thread.start()
        self.debug_logger.info("服务器线程已启动。")

    def stop(self):
        """
        停止服务器，关闭监听套接字，并重命名日志文件以保存当前会话。
        """
        self.is_running = False
        # 通过连接自身来中断服务器的 accept 阻塞
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as interrupt_socket:
                interrupt_socket.connect((self.host, self.port))
                interrupt_socket.close()
                self.debug_logger.info("已发送中断信号以停止服务器。")
        except Exception as e:
            self.debug_logger.warning(f"发送中断信号时发生异常: {e}")

        # 等待服务器线程结束
        self.server_thread.join(timeout=1)
        self.debug_logger.info("服务器线程已停止。")

        # 重命名日志文件
        if os.path.exists(self.log_file_path):
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            new_log_file = os.path.join(self.log_directory, f"{timestamp}.log")
            try:
                os.rename(self.log_file_path, new_log_file)
                self.debug_logger.info(f"日志文件已重命名为: {new_log_file}")
            except Exception as e:
                self.debug_logger.error(f"重命名日志文件时发生错误: {e}")

    def start_server(self):
        """
        服务器主循环，监听并接受客户端连接。
        为每个客户端连接启动一个新的处理线程。
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            # 允许地址重用
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            self.debug_logger.info(f"服务器已启动，监听 {self.host}:{self.port}")
            while self.is_running:
                try:
                    connection, address = server_socket.accept()
                    self.debug_logger.info(f"接收到来自 {address} 的连接请求。")
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(connection, address), 
                        daemon=True
                    )
                    client_thread.start()
                except socket.error as e:
                    if self.is_running:
                        self.debug_logger.error(f"套接字错误: {e}")
                    break  # 当服务器关闭时，跳出循环
                except Exception as e:
                    self.debug_logger.error(f"服务器主循环中发生异常: {e}")
                    break

    def handle_client(self, connection: socket.socket, address):
        """
        处理单个客户端连接，接收消息并回复机器人响应。

        :param connection: 客户端的套接字连接
        :param address: 客户端的地址
        """
        self.debug_logger.info(f"开始处理来自 {address} 的客户端连接。")
        with connection:
            # 自动发送“欢迎”指令
            welcome_command = "打招呼"
            try:
                welcome_reply = self.parser.parse_command(welcome_command)
                if not welcome_reply:
                    welcome_reply = "抱歉，我无法理解您的指令。"
                self.debug_logger.debug(f"执行欢迎指令，回复: {welcome_reply}")
            except Exception as e:
                welcome_reply = "抱歉，处理欢迎指令时发生错误。"
                self.debug_logger.error(f"处理欢迎指令时发生异常: {e}")

            # 记录机器人回复（不记录用户发送的欢迎指令）
            self.log_message("机器人", welcome_reply)
            self.debug_logger.debug(f"已记录机器人回复: {welcome_reply}")

            # 获取当前机器人状态
            current_state = self.robot.current_state
            state_message = f"{current_state}"
            self.debug_logger.debug(f"当前机器人状态: {state_message}")

            # 获取当前语速
            current_speed = self.robot.speed
            self.debug_logger.debug(f"当前语速设置: {current_speed}")

            # 构建JSON响应
            response = {
                "reply": welcome_reply,
                "state": state_message,
                "speed": current_speed  # 新增语速字段
            }
            response_str = json.dumps(response, ensure_ascii=False) + '\n'  # 添加换行符作为分隔符

            # 发送欢迎消息给客户端
            try:
                connection.sendall(response_str.encode('utf-8'))
                self.debug_logger.info(f"已发送欢迎回复给 {address}: {response_str.strip()}")
                # self.message_received.emit(welcome_reply)  # 移除这一行
            except socket.error as e:
                self.debug_logger.error(f"发送欢迎消息时发生错误: {e}")
                return

            while self.is_running:
                try:
                    data = connection.recv(4096)  # 增加接收缓冲区大小
                    if not data:
                        self.debug_logger.info(f"连接关闭来自 {address}")
                        break
                    messages = data.decode('utf-8').split('\n')
                    for message in messages:
                        if not message.strip():
                            continue
                        self.debug_logger.info(f"收到来自 {address} 的消息: {message}")

                        if message:
                            # 记录用户消息
                            self.log_message("用户", message)
                            self.debug_logger.debug(f"已记录用户消息: {message}")

                            # 使用DSLParser解析指令并生成机器人回复
                            try:
                                reply = self.parser.parse_command(message)
                                self.debug_logger.debug(f"解析指令 '{message}' 得到回复: {reply}")
                            except Exception as e:
                                reply = "抱歉，处理您的指令时发生错误。"
                                self.debug_logger.error(f"解析指令时发生异常: {e}")

                            # 获取当前机器人状态
                            current_state = self.robot.current_state
                            state_message = f"{current_state}"
                            self.debug_logger.debug(f"当前机器人状态: {state_message}")

                            # 获取当前语速
                            current_speed = self.robot.speed
                            self.debug_logger.debug(f"当前语速设置: {current_speed}")

                            # 构建JSON响应
                            response = {
                                "reply": reply,
                                "state": state_message,
                                "speed": current_speed  # 新增语速字段
                            }
                            response_str = json.dumps(response, ensure_ascii=False) + '\n'  # 添加换行符作为分隔符
                            self.debug_logger.debug(f"构建响应: {response_str.strip()}")

                            # 发送JSON响应给客户端
                            try:
                                connection.sendall(response_str.encode('utf-8'))
                                self.debug_logger.info(f"已发送回复给 {address}: {response_str.strip()}")
                                # self.message_received.emit(reply)  # 移除这一行
                            except socket.error as e:
                                self.debug_logger.error(f"发送回复时发生错误: {e}")
                                break

                            # 记录机器人回复
                            self.log_message("机器人", reply)
                            self.debug_logger.debug(f"已记录机器人回复: {reply}")
                except socket.error as e:
                    self.debug_logger.error(f"与 {address} 的连接发生错误: {e}")
                    break
                except Exception as e:
                    self.debug_logger.error(f"处理来自 {address} 的消息时发生异常: {e}")
                    break


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    # 创建应用程序实例
    app = QApplication(sys.argv)

    # 创建并启动服务器
    server = Server(host='127.0.0.1', port=65432)
    server.start()

    # 运行应用程序
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        server.stop()
