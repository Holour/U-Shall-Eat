# test/test_parser.py

import sys
import os

# 获取项目根目录的绝对路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from dsl.parser import DSLParser
from src.robot import Robot

class MockRobot:
    """模拟Robot类的行为"""
    def __init__(self):
        self.current_state = ""
        self.flavor_preferences = {}
        self.kind_preferences = {}
    
    def greet(self):
        return "你好！"
        
    def recommend_canteen(self):
        return "这是食堂推荐"
        
    def recommend_food(self):
        return "这是美食推荐"
        
    def set_flavor_preference(self, preference, flavor=None):
        if flavor:
            return f"设置口味偏好：{preference} {flavor}"
        return f"设置口味偏好：{preference}"
        
    def set_kind_preference(self, preference, kind=None):
        if kind:
            return f"设置种类偏好：{preference} {kind}"
        return f"设置种类偏好：{preference}"
        
    def query_time(self):
        return "现在是12:00"
        
    def query_weather(self):
        return "今天天气晴朗"
        
    def adjust_speed(self, speed):
        return f"语速已调整为：{speed}"
        
    def exit(self):
        return "再见！"
        
    def change_canteen(self):
        return "已为您更换推荐"
        
    def help(self):
        return "这是帮助信息"
        
    def play_music(self):
        return "开始播放音乐"
        
    def stop_music(self):
        return "停止播放音乐"
        
    def pause_music(self):
        return "暂停播放音乐"
        
    def resume_music(self):
        return "继续播放音乐"
        
    def change_song(self):
        return "已切换到下一首"

def process_command(text):
    """处理用户输入的命令"""
    robot = MockRobot()
    parser = DSLParser(robot)
    return parser.parse_command(text)

if __name__ == "__main__":
    while True:
        try:
            user_input = input("请输入命令(输入'exit'退出)：")
            if user_input.lower() == 'exit':
                break
            result = process_command(user_input)
            print(f"输出: {result}")
        except KeyboardInterrupt:
            print("\n程序已退出")
            break
        except Exception as e:
            print(f"错误: {str(e)}")