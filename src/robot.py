# src/robot.py

import requests
import random
import csv
import os
import sys
import pygame
import threading
from datetime import datetime
from typing import List, Dict, Optional


class Robot:
    def __init__(self):
        # 口味偏好，仅支持“酸”、“甜”、“辣”、“咸”
        self.flavor_pref = {
            "酸": None,
            "甜": None,
            "辣": None,
            "咸": None
        }
        # 种类偏好，仅支持“米”、“面”、“其他”
        self.kind_pref = {
            "米": None,
            "面": None,
            "其他": None
        }
        self.speed = 200  # 默认语速
        self.current_state = "默认状态"
        self.food_list = self.load_food_data()
        
        # 音乐播放相关属性
        self.music_directory = self.resource_path("resources/music")
        self.music_files = self.load_music_files()
        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.music_thread = None
        self.music_lock = threading.Lock()

        # 初始化 pygame mixer
        pygame.mixer.init()

    def resource_path(self, relative_path):
        """
        获取资源文件的绝对路径，适用于开发环境和打包后的应用程序。
        
        参数:
            relative_path (str): 资源文件的相对路径。
        
        返回:
            str: 资源文件的绝对路径。
        """
        try:
            # PyInstaller 创建临时文件夹，并将路径存储在 _MEIPASS 中
            base_path = sys._MEIPASS
        except AttributeError:
            # 正常运行环境
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)

    def load_food_data(self) -> List[Dict]:
        """加载食物数据"""
        food_list = []
        csv_path = self.resource_path('resources/food_list.csv')  # 使用 resource_path 获取路径
        try:
            with open(csv_path, encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader, None)  # 跳过表头
                for row in reader:
                    if len(row) < 3:
                        continue  # 跳过不完整的行
                    name = row[0].strip()
                    kind = row[1].strip()
                    flavors_raw = row[2].strip()
                    # 首先按'/'分割，然后将每个部分拆分为单个字符
                    flavors = [ch for s in flavors_raw.split('/') for ch in s] if flavors_raw else []
                    food = {
                        "name": name,
                        "flavors": flavors,
                        "kind": kind
                    }
                    food_list.append(food)
        except FileNotFoundError:
            print("错误：找不到 'resources/food_list.csv' 文件。")
        except Exception as e:
            print(f"加载食物数据时发生错误：{e}")
        return food_list

    def load_music_files(self) -> List[str]:
        """加载音乐文件列表"""
        supported_formats = ('.mp3', '.ogg')
        try:
            files = [
                os.path.join(self.music_directory, f)
                for f in os.listdir(self.music_directory)
                if f.endswith(supported_formats)
            ]
            if not files:
                print(f"警告：'resources/music' 目录下没有找到支持的音乐文件（.mp3 或 .ogg）。")
            return files
        except FileNotFoundError:
            print(f"错误：找不到 '{self.music_directory}' 目录。")
            return []
        except Exception as e:
            print(f"加载音乐文件时发生错误：{e}")
            return []

    def play_music_thread(self, song_path: str):
        """后台线程播放音乐"""
        try:
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play()
            pygame.mixer.music.set_volume(1.0)  # 设置音量为最大

            # 等待音乐播放结束
            while pygame.mixer.music.get_busy():
                if not self.is_playing:
                    pygame.mixer.music.stop()
                    break
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"播放音乐时发生错误：{e}")
            self.is_playing = False

    def play_music(self) -> str:
        """播放随机音乐"""
        self.current_state = "音乐播放"
        with self.music_lock:
            if self.is_playing:
                return self.get_random_response([
                    "音乐已经在播放中啦，如果想更换歌曲，可以说'换一首'。",
                    "目前正在播放音乐，您可以继续享受或者说'换一首'来更换歌曲。",
                    "音乐正在播放中哦，想要更换歌曲吗？说'换一首'试试。",
                    "我已经在播放音乐啦，如果需要更换歌曲，请说'换一首'。",
                    "音乐已经开始播放啦，您可以说'换一首'来更换歌曲。"
                ])

            if not self.music_files:
                return self.get_random_response([
                    "抱歉，我没有找到任何音乐文件哦。",
                    "目前没有可播放的音乐，请确保'music'目录下有.mp3或.ogg文件。",
                    "抱歉，音乐列表为空，请添加一些歌曲到'music'目录。",
                    "抱歉，暂时没有音乐可以播放。",
                    "抱歉，我找不到任何歌曲了。"
                ])

            # 选择随机歌曲
            self.current_song = random.choice(self.music_files)
            self.is_playing = True
            self.is_paused = False

            # 获取演唱者和歌曲名称，去除文件扩展名
            base_name = os.path.basename(self.current_song)
            name_without_ext, _ = os.path.splitext(base_name)
            try:
                artist, song = name_without_ext.split(" - ", 1)
            except ValueError:
                # 如果文件名不符合预期格式
                artist, song = "未知艺术家", name_without_ext

            # 启动播放线程
            self.music_thread = threading.Thread(target=self.play_music_thread, args=(self.current_song,))
            self.music_thread.start()

            response_templates = [
                f"正在播放{artist}的{song}。",
                f"现在播放的是{artist}的{song}，希望你喜欢！",
                f"这首{song}由{artist}演唱，希望你喜欢！",
                f"音乐开始啦！这是：{artist}的{song}。",
                f"开始播放{artist}的{song}，享受音乐吧！"
            ]
            return random.choice(response_templates)

    def stop_music(self) -> str:
        """停止音乐播放"""
        self.current_state = "音乐播放"
        with self.music_lock:
            if not self.is_playing:
                return self.get_random_response([
                    "目前没有音乐在播放。",
                    "没有音乐在播放哦。",
                    "现在没有音乐可停止。",
                    "抱歉，我现在没有在播放音乐。",
                    "音乐还没有开始播放呢。"
                ])

            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self.current_song = None
            return self.get_random_response([
                "音乐已停止。",
                "已停止播放音乐。",
                "好的，音乐已经停了。",
                "音乐停止啦。",
                "已停止音乐播放。"
            ])

    def pause_music(self) -> str:
        """暂停音乐播放"""
        self.current_state = "音乐播放"
        with self.music_lock:
            if not self.is_playing:
                return self.get_random_response([
                    "目前没有音乐在播放。",
                    "没有音乐在播放哦。",
                    "现在没有音乐可暂停。",
                    "抱歉，我现在没有在播放音乐。",
                    "音乐还没有开始播放呢。"
                ])

            if self.is_paused:
                return self.get_random_response([
                    "音乐已经暂停了。",
                    "音乐已经处于暂停状态。",
                    "音乐已经暂停，请说'继续音乐'来恢复。",
                    "音乐已经暂停中。",
                    "音乐当前已暂停。"
                ])

            pygame.mixer.music.pause()
            self.is_paused = True
            return self.get_random_response([
                "音乐已暂停。",
                "已暂停音乐播放。",
                "好的，音乐暂停了。",
                "音乐暂停啦。",
                "已暂停播放音乐。"
            ])

    def resume_music(self) -> str:
        """恢复音乐播放"""
        self.current_state = "音乐播放"
        with self.music_lock:
            if not self.is_playing:
                return self.get_random_response([
                    "目前没有音乐在播放。",
                    "没有音乐在播放哦。",
                    "现在没有音乐可继续。",
                    "抱歉，我现在没有在播放音乐。",
                    "音乐还没有开始播放呢。"
                ])

            if not self.is_paused:
                return self.get_random_response([
                    "音乐已经在播放中。",
                    "音乐已经在播放啦。",
                    "音乐没有暂停哦。",
                    "音乐已经继续播放了。",
                    "音乐已经在播放了。"
                ])

            pygame.mixer.music.unpause()
            self.is_paused = False
            return self.get_random_response([
                "音乐已继续播放。",
                "已恢复音乐播放。",
                "好的，音乐继续啦。",
                "音乐继续播放中。",
                "已继续播放音乐。"
            ])

    def change_song(self) -> str:
        """更换为另一首随机歌曲"""
        self.current_state = "音乐播放"
        with self.music_lock:
            if not self.is_playing:
                return self.get_random_response([
                    "目前没有音乐在播放。",
                    "没有音乐在播放哦。",
                    "现在没有音乐可更换。",
                    "抱歉，我现在没有在播放音乐。",
                    "音乐还没有开始播放呢。"
                ])

            if not self.music_files:
                return self.get_random_response([
                    "抱歉，我没有找到任何音乐文件哦。",
                    "目前没有可播放的音乐，请确保'music'目录下有.mp3或.ogg文件。",
                    "抱歉，音乐列表为空，请添加一些歌曲到'music'目录。",
                    "抱歉，暂时没有音乐可以播放。",
                    "抱歉，我找不到任何歌曲了。"
                ])

            # 停止当前音乐
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False

            # 选择另一首随机歌曲
            new_song = random.choice(self.music_files)
            # 确保新歌不同于当前歌
            attempts = 0
            while new_song == self.current_song and len(self.music_files) > 1 and attempts < 10:
                new_song = random.choice(self.music_files)
                attempts += 1
            self.current_song = new_song
            self.is_playing = True
            self.is_paused = False

            # 获取演唱者和歌曲名称，去除文件扩展名
            base_name = os.path.basename(self.current_song)
            name_without_ext, _ = os.path.splitext(base_name)
            try:
                artist, song = name_without_ext.split(" - ", 1)
            except ValueError:
                # 如果文件名不符合预期格式
                artist, song = "未知艺术家", name_without_ext

            # 启动播放线程
            self.music_thread = threading.Thread(target=self.play_music_thread, args=(self.current_song,))
            self.music_thread.start()

            response_templates = [
                f"更换歌曲，现在播放的是{artist}的{song}。",
                f"现在播放新的歌曲：{artist}的{song}。",
                f"为你更换了新歌{song}，由{artist}演唱。",
                f"开始播放下一首：{artist}的{song}。",
                f"已更换为{artist}演唱的{song}，希望你喜欢！"
            ]
            return random.choice(response_templates)

    def get_random_response(self, templates: List[str]) -> str:
        """从模板列表中随机选择一个回复"""
        return random.choice(templates)

    def greet(self) -> str:
        """生成不同时段的问候语"""
        current_hour = datetime.now().hour

        # 定义不同时段的问候语模板
        morning_greetings = [
            "早安！阳光明媚的早晨，需要我为您服务吗？",
            "早上好！新的一天开始啦，有什么我可以帮您的？",
            "早安！精神焕发地开始今天吧，需要什么帮助吗？",
            "早上好！希望您度过愉快的一天，我能为您做些什么？",
            "早安！今天也要元气满满哦，让我来协助您吧！"
        ]

        noon_greetings = [
            "中午好！累了吗？要不要休息一下？",
            "午安！想来点美食，还是需要其他帮助？",
            "中午好！享用午餐了吗？有什么我可以帮忙的？",
            "午安！休息时间到啦，需要我为您做些什么？",
            "中午好！阳光正好，我可以为您效劳吗？"
        ]

        afternoon_greetings = [
            "下午好！需要来杯下午茶提提神吗？",
            "午后问好！工作累了吧，有什么我能帮您的？",
            "下午好！还在努力工作吗？让我来协助您吧！",
            "美好的下午！需要我为您做些什么吗？",
            "下午好！阳光正暖，有什么可以帮到您的？"
        ]

        evening_greetings = [
            "晚上好！今天过得怎么样？需要我的帮助吗？",
            "晚安！繁忙的一天即将结束，有什么我可以为您做的？",
            "晚上好！来聊聊天放松一下吧，或者需要其他帮助？",
            "美好的夜晚！今天辛苦了，让我来为您服务吧！",
            "晚上好！享受轻松的夜晚时光，需要什么帮助吗？"
        ]

        night_greetings = [
            "深夜好！这么晚还没休息啊，需要帮忙吗？",
            "夜深了！注意休息哦，有什么我可以协助的吗？",
            "深夜问候！熬夜工作吗？让我来帮您分担一些吧！",
            "夜深了！感谢您的付出，需要什么帮助吗？",
            "深夜好！记得照顾好自己，有什么我能为您做的？"
        ]

        # 根据当前时间选择合适的问候语列表
        if 6 <= current_hour < 12:
            greeting = random.choice(morning_greetings)
        elif 12 <= current_hour < 14:
            greeting = random.choice(noon_greetings)
        elif 14 <= current_hour < 18:
            greeting = random.choice(afternoon_greetings)
        elif 18 <= current_hour < 22:
            greeting = random.choice(evening_greetings)
        else:
            greeting = random.choice(night_greetings)

        return greeting

    def recommend_canteen(self) -> str:
        """推荐食堂"""
        self.current_state = "食堂推荐"
        canteens = [
            {"name": "风味餐厅", "location": "综合食堂一楼", "prob": 1},
            {"name": "学宜餐厅", "location": "综合食堂二楼", "prob": 1},
            {"name": "民族餐厅", "location": "综合食堂四楼", "prob": 1},
            {"name": "学苑风味餐厅", "location": "学生餐厅对面", "prob": 1},
            {"name": "老食堂", "location": "学生餐厅一层", "prob": 1},
            {"name": "清真餐厅", "location": "学生餐厅二层", "prob": 1},
            {"name": "楼上楼餐厅", "location": "学生餐厅三层", "prob": 0.2},
            {"name": "麦当劳", "location": "综合食堂对面", "prob": 0.1},
            {"name": "金谷园饺子", "location": "学校东北角北侧", "prob": 0.1}
        ]
        canteen = self.random_canteen(canteens)

        # 准备多个话语模板
        templates = [
            f"推荐你去{canteen['name']}，它位于{canteen['location']}，想试试看吗？",
            f"今天不妨去{canteen['name']}，在{canteen['location']}，怎么样？",
            f"你可以去{canteen['name']}，位置在{canteen['location']}，感觉如何？",
            f"我推荐你去{canteen['name']}，它就在{canteen['location']}，可以去尝尝哦！",
            f"不妨试试{canteen['name']}，在{canteen['location']}，很不错哦！"
        ]

        # 随机选择一个模板
        return random.choice(templates)

    def random_canteen(self, canteens: List[Dict]) -> Dict:
        """根据概率随机选择一个食堂"""
        choices = []
        for canteen in canteens:
            choices.extend([canteen] * int(canteen["prob"] * 100))
        return random.choice(choices)

    def recommend_food(self) -> str:
        """推荐美食"""
        self.current_state = "美食推荐"
        filtered_food = self.filter_food()

        if not filtered_food:
            return "你的口味太挑剔了，我暂时找不到合适的美食哦。你可以告诉我“随便”来重置偏好。"

        recommendations = random.sample(filtered_food, min(3, len(filtered_food)))

        # 准备多个推荐模板（去除换行符）
        templates = [
            "为你精选了以下美食，快来看看吧： {}",
            "不妨试试： {}",
            "这些美食可能会符合你的口味： {}",
            "试试这些美食，满足你的味蕾： {}",
            "要不要试试这几个： {}"
        ]

        # 构造推荐的食物列表字符串，按照“1 宫保鸡丁盖饭，2.清汤牛肉面，3.皮蛋瘦肉粥”格式
        food_list = "，".join([f"{i + 1} {food['name']}" for i, food in enumerate(recommendations)])

        # 随机选择一个模板并填入食物列表
        response = random.choice(templates).format(food_list)

        return response

    def filter_food(self) -> List[Dict]:
        """根据用户偏好过滤食物"""
        filtered = self.food_list
        # 过滤口味
        for flavor, pref in self.flavor_pref.items():
            if pref == "喜欢":
                filtered = [f for f in filtered if flavor in f['flavors']]
            elif pref == "不喜欢":
                filtered = [f for f in filtered if flavor not in f['flavors']]
        # 过滤种类
        for kind, pref in self.kind_pref.items():
            if pref == "喜欢":
                filtered = [f for f in filtered if f['kind'] == kind]
            elif pref == "不喜欢":
                filtered = [f for f in filtered if f['kind'] != kind]
        return filtered

    def set_flavor_preference(self, preference: str, flavor: Optional[str] = None) -> str:
        """设置口味偏好"""
        self.current_state = "口味设置"
        # 喜欢的回复模板
        like_responses = [
            "好的，我记住了！您喜欢{}呢～",
            "明白了，您对{}的喜爱已经记录下来啦！",
            "收到！看来您很喜欢{}呢，我会记住的～",
            "了解！{} 确实很棒，已经记录您的喜好啦～",
            "好的，已经将{} 加入您的喜好清单中！"
        ]

        # 不喜欢的回复模板
        dislike_responses = [
            "明白了，我会记住您不喜欢{}的～",
            "好的，已经记录您对{}的偏好，以后会避免推荐～",
            "收到！我会注意避免向您推荐{}的～",
            "了解！已将{} 记录为不喜欢，会为您注意的！",
            "好的，已经记住您对{}的偏好啦，不会再推荐啦～"
        ]

        # 随便的回复模板
        any_responses = [
            "好的，已将所有口味偏好设置为随便。",
            "明白了，所有口味偏好已重置为随便。",
            "收到！已将口味偏好全部重置。",
            "了解，口味偏好现在随便啦。",
            "好的，口味偏好已设置为随便。"
        ]

        if preference == "喜欢" and flavor:
            if flavor in self.flavor_pref:
                self.flavor_pref[flavor] = "喜欢"
                response = random.choice(like_responses).format(flavor)
            else:
                response = f"抱歉，我没有识别到'{flavor}'这种口味。"
        elif preference == "不喜欢" and flavor:
            if flavor in self.flavor_pref:
                self.flavor_pref[flavor] = "不喜欢"
                response = random.choice(dislike_responses).format(flavor)
            else:
                response = f"抱歉，我没有识别到'{flavor}'这种口味。"
        elif preference == "随便":
            for key in self.flavor_pref.keys():
                self.flavor_pref[key] = None
            response = random.choice(any_responses)
        else:
            response = f"抱歉，我只能处理'喜欢'、'不喜欢'或'随便'的选项哦～"

        return response

    def set_kind_preference(self, preference: str, kind: Optional[str] = None) -> str:
        """设置种类偏好，并确保只有一个种类被标记为“喜欢”"""
        self.current_state = "种类设置"
        # 喜欢的回复模板
        like_responses = [
            "太好了！原来您喜欢{}啊，这个分类下有很多美味呢～",
            "好的，已经记住您喜欢{}啦！要不要看看这个分类下的推荐？",
            "明白！{}确实是个很棒的选择，已经记录下来啦～",
            "收到！看来您是{}的粉丝呢，我会多关注相关推荐的～",
            "好的！{}是个很好的选择，已经添加到您的偏好中啦！"
        ]

        # 不喜欢的回复模板
        dislike_responses = [
            "明白了，我会避免向您推荐{}相关的内容～",
            "好的，已经记住您不太喜欢{}啦，会注意的！",
            "收到！之后会减少{}类的推荐的～",
            "了解！已将{}加入避免推荐的列表啦～",
            "好的，我会记住您对{}的偏好，调整推荐方向～"
        ]

        # 随便的回复模板
        any_responses = [
            "好的，已将所有种类偏好设置为随便。",
            "明白了，所有种类偏好已重置为随便。",
            "收到！已将种类偏好全部重置。",
            "了解，种类偏好现在随便啦。",
            "好的，种类偏好已设置为随便。"
        ]

        if preference == "喜欢" and kind:
            if kind in self.kind_pref:
                # 将所有种类设为“未标注”
                for k in self.kind_pref.keys():
                    self.kind_pref[k] = None
                # 将选定种类设为“喜欢”
                self.kind_pref[kind] = "喜欢"
                response = random.choice(like_responses).format(kind)
            else:
                response = f"抱歉，我没有识别到'{kind}'这种种类。"
        elif preference == "不喜欢" and kind:
            if kind in self.kind_pref:
                self.kind_pref[kind] = "不喜欢"
                response = random.choice(dislike_responses).format(kind)
            else:
                response = f"抱歉，我没有识别到'{kind}'这种种类。"
        elif preference == "随便":
            for key in self.kind_pref.keys():
                self.kind_pref[key] = None
            response = random.choice(any_responses)
        else:
            response = f"抱歉，我只能处理'喜欢'、'不喜欢'或'随便'的选项哦～"

        return response

    def query_time(self) -> str:
        """查询当前时间"""
        current = datetime.now()
        full_time = current.strftime("%Y-%m-%d %H:%M:%S")
        date = current.strftime("%Y年%m月%d日")
        time_str = current.strftime("%H:%M:%S")
        weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][current.weekday()]

        # 定义多个天气回复模板
        time_templates = [
            f"现在是 {full_time}",
            f"当前时间：{full_time}",
            f"目前是 {date} {weekday} {time_str}",
            f"现在是 {date} {weekday}，时间 {time_str}",
            f"时间来到了 {date} {time_str}",
            f"{weekday}好！现在是 {time_str}",
            f"当前日期是 {date}，时间 {time_str}",
            f"现在是 {weekday} {time_str}",
            f"报时服务：现在是 {full_time}",
            f"当前时刻：{date} {weekday} {time_str}"
        ]

        # 根据不同时间段添加特殊问候
        hour = current.hour
        if 5 <= hour < 9:
            time_templates.extend([
                f"早安！现在时间是 {time_str}",
                f"早上好！{date} {time_str}"
            ])
        elif 11 <= hour < 14:
            time_templates.extend([
                f"午好！当前时间 {time_str}",
                f"中午好！现在是 {date} {time_str}"
            ])
        elif 17 <= hour < 19:
            time_templates.extend([
                f"傍晚好！时间是 {time_str}",
                f"快到晚饭时间啦！现在是 {time_str}"
            ])
        elif 22 <= hour or hour < 5:
            time_templates.extend([
                f"夜深了，现在是 {time_str}",
                f"深夜了，当前时间 {time_str}，要注意休息哦"
            ])

        return random.choice(time_templates)

    def query_weather(self) -> str:
        """查询北京天气信息"""
        self.current_state = "默认状态"
        # OpenWeather API URL
        url = f"http://api.openweathermap.org/data/2.5/weather?q=BEIJING&appid=5af7f8db2727027fdb8abe6510b4203e&units=metric&lang=zh_cn"

        try:
            # 发送请求
            response = requests.get(url)

            # 如果请求成功，处理返回的数据
            if response.status_code == 200:
                data = response.json()

                # 提取天气信息
                temperature = round(data['main']['temp'], 1)  # 保留一位小数
                weather_description = data['weather'][0]['description']
                humidity = data['main']['humidity']
                wind_speed = data['wind']['speed']
                pressure = data['main']['pressure']
                temp_min = round(data['main']['temp_min'], 1)
                temp_max = round(data['main']['temp_max'], 1)

                # 根据温度范围给出着装建议
                def get_clothing_advice(temp: float) -> str:
                    if temp < 5:
                        return "要穿厚厚的羽绒服哦"
                    elif temp < 12:
                        return "适合穿外套加毛衣"
                    elif temp < 18:
                        return "可以穿薄外套"
                    elif temp < 25:
                        return "穿件衬衫就很舒适"
                    else:
                        return "可以穿清凉的夏装"

                clothing_advice = get_clothing_advice(temperature)

                # 定义多个天气回复模板
                weather_templates = [
                    # 基础天气信息
                    f"北京现在{temperature}°C，{weather_description}，{clothing_advice}。",
                    
                    # 详细天气信息
                    f"北京天气实况：气温{temperature}°C，{weather_description}。空气湿度{humidity}%，风速{wind_speed}米/秒。{clothing_advice}！",
                    
                    # 简洁版本
                    f"北京现在{weather_description}，气温{temperature}°C哦～",
                    
                    # 关心版本
                    f"亲，北京现在{temperature}°C，{weather_description}呢。{clothing_advice}～",
                    
                    # 温馨提示版本
                    f"北京天气：{temperature}°C，{weather_description}。温馨提示：{clothing_advice}。",
                    
                    # 预测版本
                    f"北京目前{temperature}°C，{weather_description}。{clothing_advice}。"
                ]

                # 根据天气状况添加特殊提醒
                if "雨" in weather_description:
                    weather_templates.extend([
                        f"北京正在下雨，气温{temperature}°C。记得带伞出门哦！",
                        f"外面在下雨呢，气温{temperature}°C。出门记得带伞～"
                    ])
                elif "雪" in weather_description:
                    weather_templates.extend([
                        f"北京正在下雪，气温{temperature}°C。注意保暖，小心路滑！",
                        f"外面下雪啦！气温{temperature}°C，注意保暖哦～"
                    ])
                elif temperature > 30:
                    weather_templates.extend([
                        f"北京现在气温{temperature}°C，{weather_description}。天气炎热，记得防晒降温哦！",
                        f"今天太热啦！气温已经{temperature}°C了，记得多喝水～"
                    ])
                elif temperature < 5:
                    weather_templates.extend([
                        f"北京气温{temperature}°C，{weather_description}。天气寒冷，要注意保暖哦！",
                        f"今天真冷！气温只有{temperature}°C，要穿得暖暖的～"
                    ])

                return random.choice(weather_templates)
                
            # 如果请求失败，返回随机的错误提示
            error_messages = [
                "抱歉，天气信息暂时获取不到，要不待会再试试看？",
                "哎呀，网络有点小问题，没能获取到天气信息呢。",
                "天气服务暂时不可用，请稍后再查询哦～",
                "获取天气信息失败啦，检查一下网络再试试吧！",
                "sorry，天气数据出了点小问题，晚点再来看看吧～"
            ]
            return random.choice(error_messages)
            
        except Exception as e:
            return "抱歉，查询天气时出现了意外错误，请稍后重试。"

    def adjust_speed(self, speed: str) -> str:
        """调整语速"""
        self.current_state = "默认状态"
        # 语速映射表
        speed_map = {
            "快": 240,
            "正常": 200,
            "慢": 160
        }

        # 设置语速
        self.speed = speed_map.get(speed, 200)

        # 快速模式的回复模板
        fast_responses = [
            f"好的，已经切换到快速模式啦！",
            f"语速已调整为快速，我会说得更快一些～",
            f"明白，已加快语速！",
            f"好的，这就帮您加快语速。",
            f"语速已调至较快，如果觉得太快可以随时调整哦！"
        ]

        # 正常模式的回复模板
        normal_responses = [
            f"已将语速调整到正常水平",
            f"好的，使用正常语速为您服务",
            f"语速已恢复正常啦～",
            f"已切换到正常语速，这样听起来舒服吗？",
            f"好的，使用标准语速为您服务"
        ]

        # 慢速模式的回复模板
        slow_responses = [
            f"已经放慢语速啦，这样听起来清晰一些",
            f"好的，我会说得再慢一些～",
            f"语速已调整，我会特别注意放慢语速",
            f"明白，已切换到慢速模式",
            f"已将语速调慢，希望这样您听得更清楚"
        ]

        # 无效输入的回复模板
        invalid_responses = [
            f"抱歉，没有找到对应的语速设置，已自动调整为正常语速",
            f"不太理解您想要的语速呢，已切换到正常模式",
            f"这个语速设置我不太明白，先用正常语速为您服务吧",
            f"看起来语速设置有点问题，已使用默认的正常语速",
            f"没能识别您想要的语速，已使用标准语速继续为您服务"
        ]

        # 根据设置选择对应的回复模板
        if speed == "快":
            response = random.choice(fast_responses)
        elif speed == "正常":
            response = random.choice(normal_responses)
        elif speed == "慢":
            response = random.choice(slow_responses)
        else:
            response = random.choice(invalid_responses)

        return response

    def get_current_speed(self) -> str:
        """获取当前语速状态的辅助方法"""
        speed_value_map = {
            240: "快速",
            200: "正常",
            160: "慢速"
        }
        current_speed = speed_value_map.get(self.speed, "正常")

        # 当前语速状态的回复模板
        status_responses = [
            f"当前语速设置为{current_speed}",
            f"我现在正使用{current_speed}模式",
            f"目前的语速是{current_speed}哦",
            f"语速状态：{current_speed}",
            f"我正以{current_speed}的语速为您服务"
        ]

        return random.choice(status_responses)

    def exit(self) -> str:
        """退出当前功能"""
        self.current_state = "默认状态"
        return "退出当前功能。"

    def change_canteen(self) -> str:
        """更换食堂推荐"""
        return self.recommend_canteen()

    def help(self) -> str:
        """提供帮助信息"""
        help_messages = [
            "我可以帮助您完成以下操作：打招呼、推荐食堂、推荐美食、设置口味、设置种类、查询时间、查询天气、调整语速、播放音乐、暂停音乐、继续音乐、换一首、停止音乐、退出。",
            "您可以说：'打招呼'、'推荐食堂'、'推荐美食'、'设置口味 喜欢辣'、'设置种类 喜欢米'、'查询时间'、'查询天气'、'调整语速 快'、'播放音乐'、'暂停音乐'、'继续音乐'、'换一首'、'停止音乐' 或 '退出'。",
            "需要帮助吗？我能做的事情包括打招呼、推荐食堂和美食、设置您的口味和种类偏好、查询时间和天气、调整语速、播放音乐、暂停音乐、继续音乐、换一首歌曲，以及退出程序。",
            "我能为您做的事情有：打招呼、推荐食堂和美食、设置口味和种类偏好、查询时间和天气、调整语速、播放音乐、暂停音乐、继续音乐、换一首歌曲、停止音乐、退出程序。如果有需要，请随时告诉我！",
            "您可以向我发送以下命令：打招呼、推荐食堂、推荐美食、设置口味、设置种类、查询时间、查询天气、调整语速、播放音乐、暂停音乐、继续音乐、换一首、停止音乐、退出等。如果有疑问，随时问我哦！"
        ]
        return random.choice(help_messages)
