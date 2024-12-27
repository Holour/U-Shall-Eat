# test/run/run_test_parser.py

import os
import sys
import json
from datetime import datetime

# 获取项目根目录的绝对路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))
sys.path.insert(0, PROJECT_ROOT)

from test.test_parser import process_command

def run_tests():
    """运行测试用例"""
    # 测试用例目录在项目根目录的 test/cases 下
    test_dir = os.path.join(PROJECT_ROOT, 'test', 'cases')
    results = []
    total_cases = 0
    total_commands = 0
    passed_commands = 0

    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"测试用例目录: {test_dir}")

    # 确保测试目录存在
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        print(f"创建测试目录: {test_dir}")
        print("请在test/cases目录下添加测试用例文件")
        return

    # 创建测试报告目录
    report_dir = os.path.join(PROJECT_ROOT, 'test', 'reports')
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    # 初始化详细报告内容
    detailed_report = []
    detailed_report.append("=== 解析器测试报告 ===\n")
    detailed_report.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    detailed_report.append(f"测试用例文件数: {total_cases}\n")
    detailed_report.append(f"总命令数: {total_commands}\n")
    detailed_report.append(f"通过命令数: {passed_commands}\n")
    detailed_report.append(f"通过率: {(passed_commands/total_commands*100 if total_commands else 0):.2f}%\n")

    # 遍历测试用例文件
    for filename in os.listdir(test_dir):
        if filename.endswith('.txt'):
            total_cases += 1
            case_path = os.path.join(test_dir, filename)
            case_name = os.path.splitext(filename)[0]
            case_results = []

            print(f"\n处理测试用例: {filename}")

            # 添加测试用例标题到详细报告
            detailed_report.append(f"\n测试用例: {case_name}\n")
            detailed_report.append("-" * 50 + "\n")

            try:
                with open(case_path, 'r', encoding='utf-8') as f:
                    commands = f.readlines()

                for i, command in enumerate(commands, 1):
                    command = command.strip()
                    if not command:  # 跳过空行
                        continue

                    total_commands += 1
                    print(f"  执行命令 {i}: {command}")

                    try:
                        # 执行测试
                        output = process_command(command)

                        # 检查结果 - 只要不包含error就算通过
                        passed = 'error' not in output.lower()
                        if passed:
                            passed_commands += 1
                            status = "通过"
                        else:
                            status = "失败"

                        result = {
                            "command_no": i,
                            "status": status,
                            "input": command,
                            "output": output
                        }
                        case_results.append(result)
                        print(f"    状态: {status}")
                        print(f"    输出: {output}")

                        # 添加命令结果到详细报告
                        detailed_report.append(f"\n命令 {result['command_no']}:\n")
                        detailed_report.append(f"状态: {result['status']}\n")
                        detailed_report.append(f"输入: {result['input']}\n")
                        detailed_report.append(f"输出: {result['output']}\n")

                    except Exception as e:
                        result = {
                            "command_no": i,
                            "status": "错误",
                            "input": command,
                            "output": f"执行出错: {str(e)}"
                        }
                        case_results.append(result)
                        print(f"    执行出错: {str(e)}")

                        # 添加错误信息到详细报告
                        detailed_report.append(f"\n命令 {result['command_no']}:\n")
                        detailed_report.append(f"状态: {result['status']}\n")
                        detailed_report.append(f"输入: {result['input']}\n")
                        detailed_report.append(f"输出: {result['output']}\n")

                results.append({
                    "case": case_name,
                    "results": case_results
                })

            except Exception as e:
                error_msg = f"错误: 处理测试用例文件 {filename} 时出错: {str(e)}"
                print(error_msg)
                # 可以选择将错误写入详细报告
                detailed_report.append(f"\n{error_msg}\n")

    # 更新详细报告中的统计信息
    # 由于统计信息在处理测试用例前初始化，此时需要更新
    # 可以重构代码以在最后生成统计信息
    # 这里重新生成统计信息
    summary_report = [
        "=== 解析器测试报告 ===\n",
        f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"测试用例文件数: {total_cases}\n",
        f"总命令数: {total_commands}\n",
        f"通过命令数: {passed_commands}\n",
        f"通过率: {(passed_commands/total_commands*100 if total_commands else 0):.2f}%\n"
    ]

    # 生成测试报告内容
    report_content = "\n".join(summary_report) + "\n"

    for case in results:
        report_content += f"\n测试用例: {case['case']}\n"
        report_content += "-" * 50 + "\n"

        for result in case['results']:
            report_content += f"\n命令 {result['command_no']}:\n"
            report_content += f"状态: {result['status']}\n"
            report_content += f"输入: {result['input']}\n"
            report_content += f"输出: {result['output']}\n"

    # 将统计信息和详细命令结果合并
    # 这里使用 report_content 作为最终报告内容

    # 生成测试报告文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = os.path.join(report_dir, f'test_report_{timestamp}.txt')

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    # 在控制台输出详细报告
    print("\n=== 解析器测试报告 ===")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试用例文件数: {total_cases}")
    print(f"总命令数: {total_commands}")
    print(f"通过命令数: {passed_commands}")
    print(f"通过率: {(passed_commands/total_commands*100 if total_commands else 0):.2f}%\n")

    for case in results:
        print(f"测试用例: {case['case']}")
        print("-" * 50)
        for result in case['results']:
            print(f"\n命令 {result['command_no']}:")
            print(f"状态: {result['status']}")
            print(f"输入: {result['input']}")
            print(f"输出: {result['output']}\n")

    print(f"详细报告已保存至: {report_path}")

if __name__ == "__main__":
    run_tests()
