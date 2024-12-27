
import sys
import os

# 添加父目录到路径以允许导入
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.robot import Robot
from dsl.parser import DSLParser

def main():
    """测试桩主函数，创建Robot和Parser实例并处理用户输入"""
    robot = Robot()
    parser = DSLParser(robot)
    
    print("机器人测试桩已启动。输入命令或输入'exit'退出。")
    print("输入'help'查看可用命令。")
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n请输入命令> ").strip()
            
            # 检查退出命令
            if user_input.lower() in ['exit', 'quit', '退出']:
                print("正在退出测试桩...")
                break
            
            # 解析命令并获取响应
            response = parser.parse_command(user_input)
            
            # 打印响应
            print(f"机器人: {response}")
            
        except KeyboardInterrupt:
            print("\n正在退出测试桩...")
            break
        except Exception as e:
            print(f"错误: {str(e)}")

if __name__ == "__main__":
    main()