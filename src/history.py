# history_view.py

import os
import random
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontMetrics, QMovie, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QSizePolicy, QApplication, QLayout
)


class HistoryView(QWidget):
    """
    对话历史记录窗口类，负责显示与服务器的对话历史。
    包含加载历史记录、显示消息气泡、以及返回主界面的功能。
    """

    def __init__(self, parent: QWidget = None):
        """
        初始化对话历史记录窗口，设置UI并加载历史记录。
        
        :param parent: 父窗口对象
        """
        super().__init__(parent)
        self.init_ui()
        self.load_history()  # 加载历史记录


    def init_ui(self):
        """
        初始化用户界面，设置窗口属性、背景动画、主布局、
        标题、滚动区域以及返回按钮。
        """
        # 设置窗口属性
        self.setWindowTitle("邮小食——U Shall Eat [对话历史]")
        self.setGeometry(600, 300, 1440, 1080)
        self.setStyleSheet("background-color: white;")

        # 创建背景标签，用于显示GIF动画
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, 1440, 1080)
        self.background_label.setStyleSheet("background-color: transparent;")

        # 设置并启动GIF动画
        gif_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resources", "background_history.gif")
        if not os.path.exists(gif_path):
            print(f"GIF文件未找到: {gif_path}")
        self.movie = QMovie(gif_path)
        self.background_label.setMovie(self.movie)
        self.movie.start()

        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(50, 50, 50, 50)
        self.main_layout.setSpacing(20)  # 设置主布局的间距

        # 创建标题标签
        self.title_label = QLabel("对话历史记录", self)
        self.title_label.setStyleSheet("""
            color: #333;
            font-size: 36px;
            font-family: 微软雅黑;
            font-weight: bold;
            background: transparent;
            padding: 20px;
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.title_label)

        # 创建滚动区域
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # 确保垂直滚动条始终可见
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 隐藏水平滚动条
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)

        # 创建滚动区域的内容容器
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(20)  # 设置对话条目之间的间距
        self.scroll_layout.addStretch()  # 添加弹性空间，使消息从顶部开始显示
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area)

        # 获取垂直滚动条并设置样式
        self.vertical_scrollbar = self.scroll_area.verticalScrollBar()
        self.vertical_scrollbar.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: gray;
                min-height: 20px;
                border-radius: 2px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)

        # 定义聊天气泡的颜色和文本颜色
        self.robot_bubble_color = "rgba(255, 255, 255, 0.9)"
        self.user_bubble_color = "rgba(95, 198, 183, 0.9)"
        self.robot_text_color = "#333333"
        self.user_text_color = "#FFFFFF"

        # 创建返回按钮
        self.back_button = QPushButton("主页", self)
        self.back_button.setFixedSize(86, 86)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4966;
                border-radius: 43px;  /* 半径应为按钮高度的一半 */
                font-family: 微软雅黑;
                border: 3px solid rgba(204, 204, 204, 0.8);
                font-weight: bold;
                color: white;
                font-size: 24px;
            }
            QPushButton:hover {
                background-color: #c2ccd0;
            }
        """)
        self.back_button.setAttribute(Qt.WA_TranslucentBackground)
        self.back_button.clicked.connect(self.go_back)  # 连接返回按钮的点击事件
        # 设置按钮的固定位置
        self.back_button.move(1240, 937)

    def load_history(self):
        """
        从日志文件加载对话历史记录，并在界面上显示。
        如果日志文件不存在或读取失败，显示相应的提示信息。
        """
        # 清空现有内容，保留最后一个弹性空间
        while self.scroll_layout.count() > 1:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../logs", "chat.log")
            if not os.path.exists(log_path):
                self.add_message_element("系统提示", "暂无历史记录", "00:00:00", is_robot=True)
                return

            with open(log_path, 'r', encoding='utf-8') as log_file:
                for line in log_file:
                    parts = line.strip().split(',', 2)
                    if len(parts) == 3:
                        role, time_str, content = parts
                        is_robot = (role == "机器人")
                        self.add_message_element(role, content, time_str, is_robot)
        except Exception as e:
            self.add_message_element("系统提示", f"读取历史记录失败: {str(e)}", "00:00:00", is_robot=True)

    def wrap_text(self, text: str, max_chars: int = 24) -> str:
        """
        手动在文本中每 max_chars 个字符处插入换行符，
        前提是文本中没有已有的换行符。

        :param text: 原始文本内容
        :param max_chars: 每行的最大字符数
        :return: 处理后的文本内容
        """
        if '\n' in text:
            # 如果文本中已有换行符，则不进行处理
            return text
        else:
            # 每 max_chars 个字符插入一个换行符
            wrapped_text = '\n'.join([text[i:i+max_chars] for i in range(0, len(text), max_chars)])
            return wrapped_text

    def add_message_element(self, role: str, content: str, time_str: str, is_robot: bool):
        """
        添加一个聊天消息气泡到历史记录中。
        
        :param role: 消息发送者角色，如"机器人"或"用户"
        :param content: 消息内容
        :param time_str: 消息发送时间
        :param is_robot: 是否为机器人的消息
        """
        # 创建消息容器
        message_container = QWidget()
        container_layout = QHBoxLayout(message_container)
        container_layout.setContentsMargins(20, 0, 20, 0)
        message_container.setStyleSheet("background-color: transparent;")

        # 创建消息框架
        message_frame = QFrame()
        message_layout = QVBoxLayout(message_frame)
        message_layout.setContentsMargins(20, 15, 20, 15)
        message_layout.setSpacing(10)

        # 设置消息框的颜色和文本颜色
        bubble_color = self.robot_bubble_color if is_robot else self.user_bubble_color
        text_color = self.robot_text_color if is_robot else self.user_text_color

        message_frame.setStyleSheet("""
            QFrame {
                background: transparent;
            }
        """)

        # 创建并设置头部组件（头像、名称、时间）
        header_widget = self._create_message_header(role, time_str, is_robot)
        
        # 创建内容标签和框架
        content_frame, content_label = self._create_message_content(content, bubble_color, text_color)

        # 将头部和内容添加到消息布局中
        message_layout.addWidget(header_widget)
        message_layout.addWidget(content_frame)

        # 根据发送者调整消息框的位置
        if is_robot:
            container_layout.addWidget(message_frame, alignment=Qt.AlignLeft)
            container_layout.addStretch()
        else:
            container_layout.addStretch()
            container_layout.addWidget(message_frame, alignment=Qt.AlignRight)

        # 将消息容器添加到滚动布局中
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, message_container)

    def _create_avatar_label(self, is_robot: bool) -> QLabel:
        """
        创建用户头像标签。
        
        :param is_robot: 是否为机器人
        :return: 头像标签
        """
        avatar_label = QLabel()
        avatar_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../resources",
            "robot.png" if is_robot else "boy.png"
        )
        
        avatar_pixmap = QPixmap(avatar_path)
        if avatar_pixmap.isNull():
            avatar_pixmap = QPixmap(60, 60)
            avatar_pixmap.fill(Qt.gray)
        
        avatar_pixmap = avatar_pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        avatar_label.setPixmap(avatar_pixmap)
        avatar_label.setFixedSize(60, 60)
        avatar_label.setStyleSheet("""
            QLabel {
                border-radius: 30px;
                background: transparent;
            }
        """)
        return avatar_label

    def _create_name_time_widget(self, role: str, time_str: str) -> QWidget:
        """
        创建包含用户名和时间的组件。
        
        :param role: 用户角色
        :param time_str: 时间字符串
        :return: 名称和时间组件
        """
        name_time_widget = QWidget()
        name_time_layout = QVBoxLayout(name_time_widget)
        name_time_layout.setContentsMargins(0, 0, 0, 0)
        name_time_layout.setSpacing(2)

        # 创建名称标签
        name_label = QLabel(role)
        name_label.setStyleSheet("""
            QLabel {
                color: black; 
                font-size: 24px; 
                font-weight: bold; 
                font-family: 微软雅黑;
                background: transparent;
            }
        """)

        # 创建时间标签
        time_label = QLabel(time_str)
        time_label.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 18px;
                font-family: 微软雅黑;
                opacity: 0.8;
                background: transparent;
            }
        """)

        name_time_layout.addWidget(name_label)
        name_time_layout.addWidget(time_label)
        
        return name_time_widget

    def _create_message_header(self, role: str, time_str: str, is_robot: bool) -> QWidget:
        """
        创建消息头部组件，包含头像、用户名和时间。
        
        :param role: 用户角色
        :param time_str: 时间字符串
        :param is_robot: 是否为机器人
        :return: 头部组件
        """
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # 创建头像标签
        avatar_label = self._create_avatar_label(is_robot)
        
        # 创建名称和时间容器
        name_time_widget = self._create_name_time_widget(role, time_str)

        # 根据发送者调整布局顺序
        if is_robot:
            header_layout.addWidget(avatar_label)
            header_layout.addWidget(name_time_widget)
            header_layout.addStretch()
        else:
            header_layout.addStretch()
            header_layout.addWidget(name_time_widget, alignment=Qt.AlignRight)
            header_layout.addWidget(avatar_label)

        return header_widget

    def _create_message_content(self, content: str, bubble_color: str, text_color: str) -> tuple[QFrame, QLabel]:
        """
        创建消息内容组件。
        
        :param content: 消息内容
        :param bubble_color: 气泡背景色
        :param text_color: 文本颜色
        :return: 内容框架和标签的元组
        """
        # 设置字体和大小
        font = QFont("Microsoft YaHei")
        font.setPixelSize(28)  # 明确设置字体大小为28像素
        font_metrics = QFontMetrics(font)
        
        # 计算文本大小
        wrapped_text = self.wrap_text(content)
        text_rect = font_metrics.boundingRect(
            0, 0, font_metrics.horizontalAdvance("中") * 28, 1000,
            Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop,
            wrapped_text
        )
        
        # 创建内容标签并设置自适应大小
        content_label = QLabel(wrapped_text)
        content_label.setFont(font)
        content_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 28px;  /* 明确在样式表中也设置字体大小 */
                font-family: "Microsoft YaHei", "微软雅黑";
                line-height: 1.5;
                background-color: transparent;
                padding: 0px;
                margin: 0px;
            }}
        """)
        
        # 根据实际内容设置标签大小
        content_label.setFixedWidth(text_rect.width() + font_metrics.averageCharWidth())
        content_label.setFixedHeight(text_rect.height())
        content_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # 创建紧凑的内容框架
        content_frame = QFrame()
        content_frame_layout = QVBoxLayout(content_frame)
        content_frame_layout.setContentsMargins(20, 8, 10, 8)  # 减小边距
        content_frame_layout.setSpacing(0)  # 移除间距
        content_frame_layout.addWidget(content_label)
        content_frame_layout.setSizeConstraint(QLayout.SetFixedSize)  # 使框架适应内容大小
        
        # 设置框架样式
        content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bubble_color};
                border-radius: 20px;
                margin: 5px;
                padding: 5px;
            }}
        """)
        
        # 设置框架的大小策略
        content_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        return content_frame, content_label

    def go_back(self):
        """
        返回主页的逻辑，实现关闭当前历史记录窗口。
        """
        self.close()

    def closeEvent(self, event):
        """
        处理窗口关闭事件，停止GIF动画并接受关闭事件。
        
        :param event: 关闭事件对象
        """
        self.movie.stop()
        event.accept()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 设置全局样式为 Fusion，这有助于统一样式应用
    app.setStyle("Fusion")

    # 全局滚动条样式表（可选）
    app.setStyleSheet("""
        QScrollBar:vertical {
            border: none;
            background: transparent;
            width: 4px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: gray;
            min-height: 20px;
            border-radius: 2px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: transparent;
        }
    """)

    # 创建 HistoryView 实例并显示
    history_view = HistoryView()
    history_view.show()

    sys.exit(app.exec_())
