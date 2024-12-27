# client.py

import sys
import os
import socket
import threading
import pyttsx3
import json
import logging
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QMovie, QPainter, QIcon
from src.history import HistoryView
import random


class Client(QWidget):
    """
    客户端主窗口类，负责与服务器通信、处理用户输入、显示消息和状态，
    并通过语音合成技术读取服务器回复。
    """
    # 定义自定义信号，用于在接收到回复和状态时将消息传递到主线程
    reply_received = pyqtSignal(str)
    state_received = pyqtSignal(str)
    speed_received = pyqtSignal(int)  # 新增信号，用于接收语速设置

    def __init__(self, server_host: str, server_port: int):
        """
        初始化客户端窗口，设置UI、日志、语音引擎，并建立与服务器的连接。
        
        :param server_host: 服务器主机地址
        :param server_port: 服务器监听端口
        """
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.is_closing = False  # 标志位，跟踪客户端是否正在关闭
        self.init_logging()  # 初始化日志系统
        self.logger.info("初始化用户界面")
        self.init_ui()

        # 初始化文本动画相关变量
        self.current_text = ""
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_animated_text)
        self.animation_index = 0
        self.is_animating = False

        # 初始化语音控制相关变量
        self.speech_thread = None
        self.engine_lock = threading.Lock()  # 线程锁，确保引擎访问的线程安全
        self.current_engine = None  # 当前正在使用的语音引擎实例

        # 连接语速信号到调整语速的槽函数
        self.speed_received.connect(self.adjust_speech_rate)

        # 连接自定义信号到相应的处理槽
        self.reply_received.connect(self.display_reply)
        self.state_received.connect(self.display_state)

        # 初始化历史记录视图
        self.history_view = HistoryView()
        self.history_button.clicked.connect(self.show_history)

        # 初始化套接字连接和监听线程
        self.socket = None
        self.listener_thread = None
        self.connect_to_server()

    def init_logging(self):
        """
        初始化日志记录配置，设置日志级别、格式和处理器。
        """
        self.logger = logging.getLogger("ClientLogger")
        self.logger.setLevel(logging.DEBUG)

        # 创建控制台日志处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # 定义日志输出格式
        formatter = logging.Formatter(
            '[%(levelname)s] %(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        # 将处理器添加到日志记录器
        self.logger.addHandler(console_handler)

    def init_ui(self):
        """
        初始化用户界面，设置窗口属性、布局及各个控件。
        """
        self.setWindowTitle("邮小食——U Shall Eat")
        self.setGeometry(600, 300, 1440, 1080)
        self.setStyleSheet("background-color: white;")

        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resources", "logo_2")
        window_icon = QIcon(icon_path)
        self.setWindowIcon(window_icon)

        # 添加左上角logo
        self.add_logo_top_left("logo_1", x=50, y=-50, width=300, height=300)  # 参数可调整

        # 创建背景标签，用于显示GIF动画
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, 1440, 1080)
        self.background_label.setStyleSheet("background-color: transparent;")

        # 设置并启动GIF动画
        gif_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resources", "background.gif")
        if not os.path.exists(gif_path):
            self.logger.error(f"GIF文件未找到: {gif_path}")
            sys.exit(1)

        self.movie = QMovie(gif_path)
        self.background_label.setMovie(self.movie)
        self.movie.start()

        # 创建消息提示标签
        self.message_label = QLabel("请输入消息:", self)
        self.message_label.move(100, 100)
        self.message_label.setStyleSheet("""
            color: white;
            font-size: 24px;
            background: transparent;
            padding: 10px;
        """)
        self.message_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.message_label.setAttribute(Qt.WA_TranslucentBackground)

        # 创建圆角输入框，用于用户输入消息
        self.input_box = QLineEdit(self)
        self.input_box.setFixedSize(1000, 80)
        self.input_box.setStyleSheet("""
            QLineEdit {
                font-size: 28px;
                font-family: 微软雅黑;
                border-radius: 40px;
                border: 3px solid rgba(204, 204, 204, 0.8);
                padding: 22px;
                background-color: rgba(255, 255, 255, 0.8);
                color: #333;
            }
        """)
        self.input_box.move(120, 940)
        self.input_box.setAttribute(Qt.WA_TranslucentBackground)
        # 连接回车键到发送消息的槽函数
        self.input_box.returnPressed.connect(self.send_message)

        # 定义统一按钮的基础样式
        button_base_style = """
            border-radius: 40px;
            font-family: 微软雅黑;
            border: 3px solid rgba(204, 204, 204, 0.8);
            font-weight: bold;
            color: white;
            font-size: 24px;
        """

        # 创建发送按钮
        self.send_button = QPushButton("发送", self)
        self.send_button.setFixedSize(86, 86)
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                {button_base_style}
                background-color: #ffa400;
            }}
            QPushButton:hover {{
                background-color: #c2ccd0;
            }}
        """)
        self.send_button.move(1140, 937)
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setAttribute(Qt.WA_TranslucentBackground)

        # 创建历史记录按钮
        self.history_button = QPushButton("历史", self)
        self.history_button.setFixedSize(86, 86)
        self.history_button.setStyleSheet(f"""
            QPushButton {{
                {button_base_style}
                background-color: #229ea7;
            }}
            QPushButton:hover {{
                background-color: #c2ccd0;
            }}
        """)
        self.history_button.move(1240, 937)
        self.history_button.setAttribute(Qt.WA_TranslucentBackground)

        # 添加机器人图片到界面顶部居中位置
        self.add_image_top_center("robot.png")

        # 创建用于显示服务器回复的标签
        self.reply_label = QLabel("", self)
        self.reply_label.setStyleSheet("""
            color: Black;
            font-size: 32px;
            background: transparent;
            padding: 0px;
            font-family: 微软雅黑;
        """)
        self.reply_label.setAlignment(Qt.AlignCenter)
        self.reply_label.setWordWrap(True)
        self.reply_label.setFixedWidth(800)
        self.reply_label.setAttribute(Qt.WA_TranslucentBackground)
        self.update_reply_position()

        # 创建用于显示状态信息的标签
        self.state_label = QLabel("", self)
        self.state_label.setStyleSheet("""
            color: #555;
            font-size: 20px;
            background: transparent;
            padding: 0px;
            font-family: 微软雅黑;
        """)
        self.state_label.setAlignment(Qt.AlignCenter)
        self.state_label.setWordWrap(True)
        self.state_label.setFixedWidth(800)
        self.state_label.setAttribute(Qt.WA_TranslucentBackground)
        self.update_state_position()

        # 确保所有控件位于背景之上
        self.raise_widgets()

        # 安装事件过滤器，监听窗口大小变化
        self.installEventFilter(self)

    def add_logo_top_left(self, image_filename: str, x: int, y: int, width: int, height: int):
        """
        在窗口左上角添加logo图片
        
        :param image_filename: 图片文件名，位于资源目录中
        :param x: 水平位置
        :param y: 垂直位置
        :param width: 图片宽度
        :param height: 图片高度
        """
        image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resources", "logo_3.png")
        if not os.path.exists(image_path):
            self.logger.error(f"Logo图片未找到: {image_path}")
            return

        self.logo_label = QLabel(self)
        pixmap = QPixmap(image_path)
        
        # 按指定尺寸缩放图片
        scaled_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        self.logo_label.setPixmap(scaled_pixmap)
        self.logo_label.move(x, y)
        self.logo_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.logo_label.setAttribute(Qt.WA_TranslucentBackground)

    def raise_widgets(self):
        """
        确保所有控件位于背景标签之上，以防止被遮挡。
        仅提升已创建的控件。
        """
        widgets = [
            self.message_label, 
            self.input_box, 
            self.send_button, 
            self.history_button, 
            self.reply_label, 
            self.image_label, 
            self.state_label
        ]
        
        # 只有在 logo_label 存在时才添加到提升列表
        if hasattr(self, 'logo_label'):
            widgets.append(self.logo_label)
        
        # 提升所有存在的控件
        for widget in widgets:
            if widget is not None:  # 确保控件存在
                widget.raise_()

    def add_image_top_center(self, image_filename: str):
        """
        加载并显示居中的圆形图片，垂直位置位于窗口上方三分之一处。

        :param image_filename: 图片文件名，位于资源目录中
        """
        image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resources", image_filename)
        if not os.path.exists(image_path):
            self.logger.error(f"图片文件未找到: {image_path}")
            return

        self.image_label = QLabel(self)
        pixmap = QPixmap(image_path)

        # 设置图片大小为宽度240，高度自动调整以保持比例
        pixmap = pixmap.scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # 创建圆形遮罩，使图片呈现圆形
        mask = QPixmap(pixmap.size())
        mask.fill(Qt.transparent)

        painter = QPainter(mask)
        painter.setBrush(Qt.white)
        painter.setPen(Qt.transparent)
        painter.drawEllipse(0, 0, pixmap.width(), pixmap.height())
        painter.end()

        pixmap.setMask(mask.createMaskFromColor(Qt.transparent))

        self.image_label.setPixmap(pixmap)

        # 计算图片的水平和垂直位置，使其居中显示
        image_width, image_height = pixmap.width(), pixmap.height()
        window_width, window_height = self.width(), self.height()

        # 水平居中
        x_position = (window_width - image_width) // 2
        # 垂直位置为窗口高度的三分之一处
        y_position = window_height // 3 - image_height // 2

        self.image_label.move(x_position, y_position)
        self.image_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.image_label.setAttribute(Qt.WA_TranslucentBackground)

    def change_image(self, new_image_filename: str):
        """
        更改界面上的图片，实现动态切换不同的图片。

        :param new_image_filename: 新的图片文件名
        """
        self.image_label.clear()  # 清除当前图片
        self.add_image_top_center(new_image_filename)  # 重新加载并居中显示新的图片

    def connect_to_server(self):
        """
        建立持久连接到服务器，并启动一个独立线程监听服务器消息。
        """
        self.logger.info("尝试连接到服务器...")
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            self.logger.info(f"已连接到服务器 {self.server_host}:{self.server_port}")

            # 启动监听线程，接收服务器消息
            self.listener_thread = threading.Thread(target=self.listen_to_server, daemon=True)
            self.listener_thread.start()
        except ConnectionRefusedError:
            self.logger.error("无法连接到服务器，请确保服务器正在运行。")
            self.reply_received.emit("无法连接到服务器，请确保服务器正在运行。")
            self.state_received.emit("")
        except Exception as e:
            self.logger.error(f"连接服务器时发生错误: {e}")
            self.reply_received.emit(f"连接服务器时发生错误: {e}")
            self.state_received.emit("")

    def listen_to_server(self):
        """
        监听来自服务器的消息，处理接收到的数据，并通过信号传递给主线程。
        """
        buffer = ""
        try:
            while True:
                data = self.socket.recv(4096)
                if not data:
                    self.logger.warning("服务器关闭了连接。")
                    self.reply_received.emit("服务器关闭了连接。")
                    self.state_received.emit("")
                    break
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        self.logger.debug(f"接收到原始数据: {line}")
                        try:
                            response = json.loads(line)
                            reply_message = response.get("reply", "")
                            state_message = response.get("state", "")
                            self.speed = response.get("speed", None)  # 获取语速设置
                            self.logger.debug(f"解析后的回复: {reply_message}")
                            self.logger.debug(f"解析后的状态: {state_message}")
                            if self.speed is not None:
                                self.speed_received.emit(self.speed)  # 发送语速信号
                            self.reply_received.emit(reply_message)
                            self.state_received.emit(state_message)
                        except json.JSONDecodeError:
                            self.logger.error("无法解析服务器发送的JSON消息。")
                            self.reply_received.emit("收到无法解析的消息。")
                            self.state_received.emit("")
        except ConnectionResetError:
            self.logger.error("与服务器的连接被重置。")
            if not self.is_closing:
                self.reply_received.emit("与服务器的连接被重置。")
                self.state_received.emit("")
        except Exception as e:
            self.logger.error(f"监听服务器时发生错误: {e}")
            if not self.is_closing:
                self.reply_received.emit(f"监听服务器时发生错误: {e}")
                self.state_received.emit("")

    def send_message(self):
        """
        处理用户发送消息的逻辑，将消息发送到服务器，并在UI中显示发送的消息。
        """
        message = self.input_box.text().strip()
        if not message:
            return  # 不发送空消息

        # 显示用户输入的消息
        self.message_label.setText(f"输入的消息: {message}")

        # 发送消息到服务器
        self.logger.info(f"准备发送消息到服务器: {message}")
        try:
            if self.socket:
                self.socket.sendall((message + '\n').encode('utf-8'))  # 添加换行符作为消息分隔
                self.logger.info(f"已发送消息到服务器: {message}")
            else:
                self.logger.error("未连接到服务器。")
                self.reply_received.emit("未连接到服务器。")
                self.state_received.emit("")
        except BrokenPipeError:
            self.logger.error("与服务器的连接丢失。")
            self.reply_received.emit("与服务器的连接丢失。")
            self.state_received.emit("")
        except Exception as e:
            self.logger.error(f"发送消息时发生错误: {e}")
            self.reply_received.emit(f"发送消息时发生错误: {e}")
            self.state_received.emit("")

        # 清空输入框
        self.input_box.clear()

    def display_reply(self, reply_message: str):
        """
        处理服务器回复的显示，包括文本动画和语音播放。

        :param reply_message: 服务器回复的消息内容
        """
        if self.is_closing:
            self.logger.debug("客户端正在关闭，忽略接收到的回复。")
            return  # 忽略关闭时接收到的消息

        self.logger.info(f"display_reply 被调用，回复内容: {reply_message}")
        # 格式化回复消息
        formatted_message = self.format_reply_message(reply_message)
        self.current_text = formatted_message

        # 重置动画状态
        self.animation_index = 0
        self.reply_label.setText("")
        self.reply_label.show()
        self.update_reply_position()

        # 如果当前有动画在进行，停止它
        if self.is_animating:
            self.display_timer.stop()

        # 开始新的文本动画
        self.is_animating = True
        self.display_timer.start(50)  # 每50毫秒更新一次文本

        # 停止当前语音播放并开始播放新的回复内容
        self.stop_current_speech()
        self.speak_reply(formatted_message)

    def format_reply_message(self, message: str) -> str:
        """
        格式化回复消息，使其每行最多64个字符，最多四行，
        超过部分在第四行显示前62个字符并添加省略号。

        :param message: 原始回复消息
        :return: 格式化后的回复消息
        """
        max_lines = 4
        max_chars_per_line = 64
        result_lines = []
        current_pos = 0
        for i in range(max_lines):
            if current_pos >= len(message):
                break
            remaining_chars = len(message) - current_pos
            if i < max_lines - 1:
                # 前三行，每行最多64个字符
                line = message[current_pos:current_pos + max_chars_per_line]
                result_lines.append(line)
                current_pos += max_chars_per_line
            else:
                # 第四行
                if remaining_chars > max_chars_per_line:
                    # 截断到62个字符并添加省略号
                    line = message[current_pos:current_pos + 62] + "..."
                else:
                    line = message[current_pos:]
                result_lines.append(line)
        return "\n".join(result_lines)

    def update_animated_text(self):
        """
        更新回复文本的动画效果，每次显示更多的字符。
        """
        if self.animation_index <= len(self.current_text):
            animated_text = self.current_text[:self.animation_index]
            self.reply_label.setText(animated_text)
            self.update_reply_position()
            self.animation_index += 1
        else:
            self.display_timer.stop()
            self.is_animating = False

    def stop_current_speech(self):
        """
        停止当前正在播放的语音，如果有的话。
        """
        with self.engine_lock:
            if self.current_engine is not None:
                try:
                    self.current_engine.stop()  # 停止语音播放
                    self.logger.debug("已停止当前语音播放。")
                except Exception as e:
                    self.logger.error(f"停止语音播放时发生错误: {e}")
                finally:
                    self.current_engine = None  # 清理当前引擎

            # 等待当前语音线程结束
            if self.speech_thread and self.speech_thread.is_alive():
                self.speech_thread.join(timeout=0.1)
                self.speech_thread = None

    def speak_reply(self, message: str):
        """
        在一个新线程中播放回复消息的语音。

        :param message: 要播放的消息内容
        """
        self.speech_thread = threading.Thread(target=self._speak_message, args=(message,), daemon=True)
        self.speech_thread.start()

    def _speak_message(self, message: str):
        """
        实际执行语音播放的方法，使用 pyttsx3 进行语音合成。

        :param message: 要播放的消息内容
        """
        try:
            # 创建新的语音引擎实例
            engine = pyttsx3.init()
            with self.engine_lock:
                self.current_engine = engine
                # 设置当前语速，如果有调整过
                current_speed = self.speed
                engine.setProperty('rate', current_speed)
                self.logger.info(f"当前说话语速为{current_speed}")

            engine.say(message)
            engine.runAndWait()
        except Exception as e:
            self.logger.error(f"语音合成时发生错误: {e}")
        finally:
            with self.engine_lock:
                self.current_engine = None  # 清理当前引擎

    def display_state(self, state_message: str):
        """
        显示机器人当前的状态信息，根据不同的状态选择随机提示语句。

        :param state_message: 当前状态的标识符
        """
        if self.is_closing:
            self.logger.debug("客户端正在关闭，忽略接收到的状态消息。")
            return  # 忽略关闭时接收到的状态消息

        self.logger.info(f"display_state 被调用，状态内容: {state_message}")
        # 定义不同状态下的提示信息
        self.state_messages = {
            "默认状态": [
                "试着问我：推荐食堂 | 推荐美食 | 口味设置 | 种类设置",
                "你可以问我：当前时间 | 天气怎么样",
                "如果你犹豫吃什么或者去哪个食堂，可以问我：推荐食堂 | 推荐美食"
            ],
            "口味设置": [
                "你可以告诉我：喜欢辣 | 不喜欢辣",
                "这里有四种口味可以设置：酸，甜，苦，咸（每次只能设置一种哦）",
                "告诉我你喜欢的口味吧！可以对我说：喜欢酸 | 讨厌甜"
            ],
            "种类设置": [
                "你可以告诉我：喜欢米 | 不喜欢面",
                "这里有三种类型可以设置：米，面，其他（每次只能设置一种哦）",
                "告诉我你喜欢的类型吧！可以对我说：喜欢其他 | 不吃米"
            ],
            "食堂推荐": [
                "不合适吗，可以对我说：换一个！",
                "怎样，如果不合适可以告诉我：换一个！",
                "这个食堂怎么样？如果不想去可以告诉我：换一个吧"
            ],
            "美食推荐": [
                "可以试着对我说：设置口味 | 设置类型",
                "可以试着对我说：喜欢酸 | 讨厌咸",
                "可以告诉我你喜欢的口味或者类型：设置口味 | 设置类型"
            ],
            "音乐播放": [
                "可以试着对我说：暂停播放 | 换一首 | 停止播放",
                "目前暂不支持点歌，可以试着对我说：换一首",
                "喜欢这首歌吗，可以试着对我说：换一首 | 停止播放"
            ]
        }

        # 根据状态选择随机提示语句
        if state_message in self.state_messages:
            message = random.choice(self.state_messages[state_message])
        else:
            message = "未知状态，请重新设置。"

        # 设置状态标签的显示内容
        self.state_label.setText(message)
        self.update_state_position()

    def adjust_speech_rate(self, speed: int):
        """
        根据服务器发送的语速设置，调整语音引擎的语速属性。

        :param speed: 新的语速值
        """
        self.logger.info(f"接收到新的语速设置: {self.speed}")
        with self.engine_lock:
            if self.current_engine is not None:
                try:
                    self.current_engine.setProperty('rate', self.speed)
                    self.logger.debug(f"已调整语音引擎语速为: {self.speed}")
                except Exception as e:
                    self.logger.error(f"调整语速时发生错误: {e}")

    def update_reply_position(self):
        """
        更新回复标签的位置，确保其始终位于窗口的正中央。
        """
        window_width, window_height = self.width(), self.height()
        label_width, label_height = self.reply_label.width(), self.reply_label.height()
        # 计算文本高度，最多四行
        font_metrics = self.reply_label.fontMetrics()
        text_height = font_metrics.lineSpacing() * 4
        self.reply_label.setFixedHeight(text_height)
        self.reply_label.move(
            (window_width - self.reply_label.width()) // 2,
            (window_height - text_height) // 2 + 50  # 上移一些，以留出状态显示空间
        )

    def update_state_position(self):
        """
        更新状态标签的位置，确保其始终位于窗口下方正中央。
        """
        window_width, window_height = self.width(), self.height()
        label_width, label_height = self.state_label.width(), self.state_label.height()

        # 计算文本高度
        font_metrics = self.state_label.fontMetrics()
        text_height = font_metrics.lineSpacing()
        self.state_label.setFixedHeight(text_height)

        # 设置标签位置，水平居中，垂直位置固定在900像素处
        self.state_label.move(
            (window_width - label_width) // 2,
            900
        )

    def eventFilter(self, source, event):
        """
        事件过滤器，用于处理窗口大小变化事件，动态调整控件位置。

        :param source: 事件源
        :param event: 事件对象
        :return: 是否过滤该事件
        """
        if event.type() == event.Resize:
            self.update_reply_position()
            self.update_state_position()
            # 重新定位图片以适应新窗口大小
            self.add_image_top_center("robot.png")
        return super().eventFilter(source, event)

    def closeEvent(self, event):
        """
        处理窗口关闭事件，确保所有资源正确释放，包括关闭服务器连接和停止语音引擎。

        :param event: 关闭事件对象
        """
        self.logger.info("关闭应用程序...")
        self.is_closing = True  # 设置关闭标志
        self.movie.stop()  # 停止GIF动画
        self.stop_current_speech()  # 确保停止所有语音播放
        if self.socket:
            try:
                self.socket.close()
                self.logger.info("套接字已关闭。")
            except Exception as e:
                self.logger.error(f"关闭套接字时发生错误: {e}")
        event.accept()  # 接受关闭事件

    def show_history(self):
        """
        显示历史记录界面，并隐藏主界面。
        """
        self.history_view.load_history()  # 加载历史记录
        self.history_view.back_button.clicked.connect(self.show_main)
        self.hide()
        self.history_view.show()

    def show_main(self):
        """
        返回主界面，隐藏历史记录界面。
        """
        self.history_view.hide()
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 初始化服务器信息，确保与 server.py 中的服务器一致
    SERVER_HOST = '127.0.0.1'
    SERVER_PORT = 65432  # 确保与 server.py 中的端口一致

    # 创建并显示客户端窗口
    client = Client(server_host=SERVER_HOST, server_port=SERVER_PORT)
    client.show()

    sys.exit(app.exec_())
