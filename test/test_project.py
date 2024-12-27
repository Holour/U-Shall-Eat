import sys
import os
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, QTimer
import logging
import threading

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.client import Client
from src.server import Server

class ClientTester:
    """
    客户端测试类，用于自动化测试客户端的输入功能
    """
    def __init__(self):
        """
        初始化测试器
        """
        # 首先设置日志目录
        self.log_dir = os.path.join(project_root, 'test', 'logs')
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(os.path.join(self.log_dir, 'cases'), exist_ok=True)
        
        # 设置日志记录器
        self.setup_logging()
        
        # 设置测试用例路径并确保目录存在
        self.test_cases_dir = os.path.join(project_root, 'test', 'cases')
        os.makedirs(self.test_cases_dir, exist_ok=True)
        self.test_file_path = os.path.join(self.test_cases_dir, 'test_cases.txt')
        
        # 如果测试文件不存在，创建一个包含示例测试用例的文件
        if not os.path.exists(self.test_file_path):
            self.logger.info(f"测试文件不存在，创建示例测试文件: {self.test_file_path}")
            with open(self.test_file_path, 'w', encoding='utf-8') as f:
                f.write("Hello\n")  # 示例测试用例
                f.write("Test message\n")
                f.write("你好，服务器\n")
        
        # 服务器配置
        self.SERVER_HOST = os.getenv('SERVER_HOST', '127.0.0.1')
        self.SERVER_PORT = int(os.getenv('SERVER_PORT', '65432'))
        
        # 初始化服务器和客户端实例
        self.server = None
        self.client = None
        
    def setup_logging(self):
        """
        设置日志记录
        """
        self.logger = logging.getLogger("ClientTester")
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '[%(levelname)s] %(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        log_file = os.path.join(self.log_dir, 'project_test.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def start_server(self):
        """
        在单独的线程中启动服务器
        """
        try:
            self.server = Server()
            server_thread = threading.Thread(target=self.server.start)
            server_thread.daemon = True  # 设置为守护线程，随主线程退出而退出
            server_thread.start()
            self.logger.info("服务器启动成功")
            time.sleep(1)  # 等待服务器完全启动
        except Exception as e:
            self.logger.error(f"启动服务器时出错: {e}")
            raise

    def load_test_cases(self) -> list:
        """
        从文件加载测试样例
        
        :return: 测试样例列表
        """
        try:
            if not os.path.exists(self.test_file_path):
                self.logger.error(f"测试文件不存在: {self.test_file_path}")
                return []
                
            with open(self.test_file_path, 'r', encoding='utf-8') as f:
                test_cases = [line.strip() for line in f.readlines() if line.strip()]
            self.logger.info(f"成功加载 {len(test_cases)} 条测试样例")
            return test_cases
        except Exception as e:
            self.logger.error(f"加载测试样例时出错: {e}")
            return []

    def run_tests(self):
        """
        运行测试用例
        """
        try:
            # 创建QApplication实例
            app = QApplication(sys.argv)
            
            # 启动服务器
            self.start_server()
            
            # 创建客户端实例
            self.client = Client(server_host=self.SERVER_HOST, server_port=self.SERVER_PORT)
            self.client.show()
            
            # 加载测试样例
            test_cases = self.load_test_cases()
            if not test_cases:
                self.logger.error("没有可用的测试样例")
                return
            
            # 创建定时器来执行测试用例
            self.current_test_index = 0
            self.test_cases = test_cases
            self.test_results = []
            
            def execute_next_test():
                if self.current_test_index < len(self.test_cases):
                    test_case = self.test_cases[self.current_test_index]
                    self.logger.info(f"执行测试样例 {self.current_test_index + 1}/{len(self.test_cases)}: {test_case}")
                    
                    try:
                        # 清空输入框并记录发送时间
                        self.client.input_box.clear()
                        self.client.input_box.setText(test_case)
                        send_time = time.strftime("%H:%M:%S")
                        QTest.mouseClick(self.client.send_button, Qt.LeftButton)
                        
                        # 等待并检查chat.log
                        chat_log_path = os.path.join(project_root, 'logs', 'chat.log')
                        start_time = time.time()
                        found_response = False
                        
                        while time.time() - start_time < 5 and not found_response:
                            if os.path.exists(chat_log_path):
                                with open(chat_log_path, 'r', encoding='utf-8') as f:
                                    lines = f.readlines()
                                    # 从后往前查找
                                    for i in range(len(lines)-1, 0, -1):
                                        line = lines[i]
                                        if "机器人" in line and "ERROR" not in line:
                                            prev_line = lines[i-1]
                                            if "用户" in prev_line and test_case in prev_line:
                                                # 计算响应时间
                                                prev_time = time.strptime(prev_line.split(',')[1].strip(), "%H:%M:%S")
                                                curr_time = time.strptime(line.split(',')[1].strip(), "%H:%M:%S")
                                                 
                                                response_seconds = (curr_time.tm_hour * 3600 + curr_time.tm_min * 60 + curr_time.tm_sec) - \
                                                                 (prev_time.tm_hour * 3600 + prev_time.tm_min * 60 + prev_time.tm_sec)
                                                 
                                                result = {
                                                    'case': test_case,
                                                    'reply': line.split(',')[2].strip(),
                                                    'response_time': f"{response_seconds:.3f}s",
                                                    'status': 'passed' if response_seconds <= 5 else 'timeout'
                                                }
                                                
                                                if response_seconds <= 5:
                                                    self.logger.info(f"测试通过: {result}")
                                                else:
                                                    result['error'] = '服务器响应超时(>5s)'
                                                    self.logger.error(f"测试超时: {result}")
                                                    
                                                self.test_results.append(result)
                                                found_response = True
                                                break
                            

                            if not found_response:
                                QTest.qWait(100)
                                  
                        if not found_response:  # 如果未找到响应
                            result = {
                                'case': test_case,
                                'status': 'error',
                                'error': '未找到服务器响应或超过5秒未更新'
                            }
                            self.test_results.append(result)
                            self.logger.error(f"测试错误: {result}")
                        
                    except Exception as e:
                        self.logger.error(f"执行测试用例时发生错误: {e}")
                        self.test_results.append({
                            'case': test_case,
                            'error': str(e),
                            'status': 'error'
                        })
                    
                    self.current_test_index += 1
                    
                    # 等待一段时间后执行下一个测试
                    QTimer.singleShot(2000, execute_next_test)  # 2秒后执行下一个测试
                else:
                    self.logger.info("所有测试样例执行完毕")
                    self.generate_test_report()
                    
                    # 关闭服务器和客户端
                    if self.server:
                        self.server.stop()
                    if self.client:
                        self.client.close()
                    
                    app.quit()
            
            # 开始执行测试
            QTimer.singleShot(1000, execute_next_test)  # 等待1秒后开始测试
          
            # 运行事件循环
            app.exec_()
            
        except Exception as e:
            self.logger.error(f"测试过程中发生错误: {e}")
            if self.server:
                self.server.stop()
            raise

    def generate_test_report(self):
        """
        生成测试报告
        """
        try:
            # 修改报告路径，保存在 test/reports 目录下
            report_dir = os.path.join(project_root, 'test', 'reports')
            os.makedirs(report_dir, exist_ok=True)
            report_path = os.path.join(report_dir, 'test_summary.txt')
            
            with open(report_path, 'w', encoding='utf-8') as f:
                for result in self.test_results:
                    if 'error' in result:
                        f.write(f"错误测试样例：{result}\n")
                    else:
                        f.write(f"通过测试样例：{result}\n")
            self.logger.info(f"测试报告已生成：{report_path}")
        except Exception as e:
            self.logger.error(f"生成测试报告时发生错误: {e}")


if __name__ == '__main__':
    tester = ClientTester()
    tester.run_tests()
