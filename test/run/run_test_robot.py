# test/run/run_test_parser.py

import os
import sys
import unittest
import subprocess
from datetime import datetime
from collections import defaultdict

# 获取项目根目录的绝对路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))
sys.path.insert(0, PROJECT_ROOT)

from src.robot import Robot
from dsl.parser import DSLParser

class CustomTestResult(unittest.TextTestResult):
    """
    自定义的测试结果类，用于收集测试用例的详细信息。
    """
    def __init__(self, *args, **kwargs):
        super(CustomTestResult, self).__init__(*args, **kwargs)
        self.test_details = []  # 存储详细的测试信息

    def addSuccess(self, test):
        super().addSuccess(test)
        self.test_details.append({
            "class_name": test.__class__.__name__,
            "test_name": test._testMethodName,
            "status": "通过",
            "input": getattr(test, 'command', ''),
            "output": getattr(test, 'response', '')
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.test_details.append({
            "class_name": test.__class__.__name__,
            "test_name": test._testMethodName,
            "status": "失败",
            "input": getattr(test, 'command', ''),
            "output": self._exc_info_to_string(err, test)
        })

    def addError(self, test, err):
        super().addError(test, err)
        self.test_details.append({
            "class_name": test.__class__.__name__,
            "test_name": test._testMethodName,
            "status": "错误",
            "input": getattr(test, 'command', ''),
            "output": self._exc_info_to_string(err, test)
        })

class CustomTestRunner(unittest.TextTestRunner):
    """
    自定义的测试运行器，使用 CustomTestResult 来收集测试结果。
    """
    def _makeResult(self):
        return CustomTestResult(self.stream, self.descriptions, self.verbosity)

def add_test_methods():
    """
    动态为 TestRobot 类添加测试方法，每个方法对应一个测试命令。
    """
    test_cases_file = os.path.join(PROJECT_ROOT, 'test', 'cases', 'test_cases.txt')
    if not os.path.exists(test_cases_file):
        raise FileNotFoundError(f"找不到测试用例文件 {test_cases_file}")

    with open(test_cases_file, 'r', encoding='utf-8') as file:
        for index, line in enumerate(file, 1):
            command = line.strip()
            if not command or command.startswith('#'):
                continue
            test_name = f'test_command_{index}'

            def test_method(self, cmd=command, idx=index):
                """
                动态生成的测试方法，用于执行单个命令的测试。
                """
                self.command = cmd  # 用于报告
                try:
                    response = self.parser.parse_command(cmd)
                    self.response = response  # 用于报告
                    if "错误" in response.lower() or "error" in response.lower():
                        self.fail(f"响应包含错误信息: {response}")
                except Exception as e:
                    self.fail(f"执行命令时发生异常: {str(e)}")

            setattr(TestRobot, test_name, test_method)

def run_tests():
    """
    运行测试用例并生成详细的测试报告。
    报告将保存到 'test/reports' 目录，并在控制台上打印。
    """
    # 动态添加测试方法
    add_test_methods()

    # 测试报告目录
    report_dir = os.path.join(PROJECT_ROOT, 'test', 'reports')
    os.makedirs(report_dir, exist_ok=True)

    # 设置报告文件路径，报告文件名包含时间戳
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = os.path.join(report_dir, f'test_report_{timestamp}.txt')

    # 创建测试运行器
    runner = CustomTestRunner(verbosity=2)

    # 加载所有测试用例
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestRobot)
    # 添加 TestRobotStub 测试
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TestRobotStub))

    # 运行测试用例
    result = runner.run(suite)

    # 收集测试结果
    total_commands = len([t for t in result.test_details if t['class_name'] == 'TestRobot'])
    passed_commands = len([t for t in result.test_details if t['status'] == '通过' and t['class_name'] == 'TestRobot'])
    pass_rate = (passed_commands / total_commands * 100) if total_commands else 0.0

    # 按测试用例类分组结果
    grouped_results = defaultdict(list)
    for detail in result.test_details:
        class_name = detail['class_name']
        grouped_results[class_name].append(detail)

    # 构建报告内容
    report_content = []
    report_content.append("=== 解析器测试报告 ===")
    report_content.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_content.append(f"测试用例文件数: {len(grouped_results)}")
    report_content.append(f"总命令数: {total_commands}")
    report_content.append(f"通过命令数: {passed_commands}")
    report_content.append(f"通过率: {pass_rate:.2f}%\n")

    for class_name, details in grouped_results.items():
        if class_name == 'TestRobot':
            report_content.append(f"测试用例: Robot DSL 命令解析")
        elif class_name == 'TestRobotStub':
            report_content.append(f"测试用例: Robot 测试桩功能")
        else:
            report_content.append(f"测试用例: {class_name}")
        report_content.append("-" * 50 + "\n")
        for detail in details:
            if class_name == "TestRobot":
                # 提取命令编号
                try:
                    test_num = int(detail['test_name'].split('_')[-1])
                except ValueError:
                    test_num = detail['test_name']
                report_content.append(f"命令 {test_num}:")
                report_content.append(f"状态: {detail['status']}")
                report_content.append(f"输入: {detail['input']}")
                report_content.append(f"输出: {detail['output']}\n")
            elif class_name == "TestRobotStub":
                report_content.append(f"测试桩功能测试:")
                report_content.append(f"状态: {detail['status']}")
                report_content.append(f"输出: {detail['output']}\n")

    # 将报告内容写入报告文件
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_content))

    # 在控制台打印报告内容
    print("\n=== 解析器测试报告 ===")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试用例文件数: {len(grouped_results)}")
    print(f"总命令数: {total_commands}")
    print(f"通过命令数: {passed_commands}")
    print(f"通过率: {pass_rate:.2f}%\n")

    for class_name, details in grouped_results.items():
        if class_name == 'TestRobot':
            print(f"测试用例: Robot DSL 命令解析")
        elif class_name == 'TestRobotStub':
            print(f"测试用例: Robot 测试桩功能")
        else:
            print(f"测试用例: {class_name}")
        print("-" * 50)
        for detail in details:
            if class_name == "TestRobot":
                try:
                    test_num = int(detail['test_name'].split('_')[-1])
                except ValueError:
                    test_num = detail['test_name']
                print(f"\n命令 {test_num}:")
                print(f"状态: {detail['status']}")
                print(f"输入: {detail['input']}")
                print(f"输出: {detail['output']}\n")
            elif class_name == "TestRobotStub":
                print(f"\n测试桩功能测试:")
                print(f"状态: {detail['status']}")
                print(f"输出: {detail['output']}\n")

    print(f"详细报告已保存至: {report_path}")

class TestRobot(unittest.TestCase):
    """
    机器人与DSL解析器集成测试类。
    用于验证机器人能否正确解析DSL命令并响应正确的结果。
    """
    
    def setUp(self):
        """
        在每个测试方法执行之前，设置测试环境。
        初始化 Robot 和 DSLParser 实例。
        """
        self.robot = Robot()
        self.parser = DSLParser(self.robot)

class TestRobotStub(unittest.TestCase):
    """
    机器人测试桩功能测试类。
    用于验证测试桩程序是否能够正确响应DSL命令并输出正确结果。
    """
    
    def setUp(self):
        """
        设置测试环境，初始化测试桩的路径。
        """
        self.stub_path = os.path.join(PROJECT_ROOT, 'test', 'run_robot.py')
        self.test_output = []  # 用来收集每个测试的输出内容

    def test_stub_basic_functionality(self):
        """
        测试测试桩的基本功能。
        启动测试桩进程并通过标准输入发送命令，检查标准输出是否符合预期。
        """
        # 从测试用例文件读取第一个有效命令用于测试
        test_cases_file = os.path.join(PROJECT_ROOT, 'test', 'cases', 'test_cases.txt')
        
        if not os.path.exists(test_cases_file):
            self.fail(f"找不到测试用例文件 {test_cases_file}")
        
        with open(test_cases_file, 'r', encoding='utf-8') as file:
            try:
                test_command = next(line.strip() for line in file if line.strip() and not line.startswith('#'))
            except StopIteration:
                self.fail("测试用例文件中没有有效的命令")

        # 启动测试桩进程
        try:
            process = subprocess.Popen(
                [sys.executable, self.stub_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
        except Exception as e:
            self.fail(f"无法启动测试桩进程: {str(e)}")

        # 发送测试命令和退出命令
        try:
            out, err = process.communicate(input=f'{test_command}\n退出\n', timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            out, err = process.communicate()
            self.fail("测试桩进程超时未响应")

        # 检查响应
        if "错误" not in out.lower() and "error" not in out.lower():
            self.response = out.strip()
            self.assertEqual(process.returncode, 0, msg=f"测试桩返回码不为0: {process.returncode}")
        else:
            self.fail(f"测试桩输出错误信息: {out}")

if __name__ == '__main__':
    run_tests()
