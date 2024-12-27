# dsl/parser.py

from pyparsing import ParseException
from dsl.grammar import command, 播放音乐, 停止音乐, 暂停音乐, 继续音乐, 换一首
from src.robot import Robot
import jieba
import jieba.posseg as pseg
import re
from typing import Dict, List, Tuple, Optional
import random


class DSLParser:
    def __init__(self, robot: Robot):
        self.robot = robot
        # 加载自定义词典（如果需要）
        # jieba.load_userdict("custom_dict.txt")

        # 初始化各类词典
        self._init_dictionaries()

    def _init_dictionaries(self):
        """初始化所有词典和映射关系"""
        # 命令同义词映射
        self.command_synonyms = {
            "打招呼": ["你好", "您好", "哈喽", "安安", "嗨", "hello", "hi", "见到你很高兴", "早上好", "下午好", "晚上好", "在"],
            "推荐食堂": ["食堂推荐", "进入食堂推荐", "推荐食堂", "推荐餐厅", "哪里吃", "哪个食堂好", "食堂怎么走", "去哪吃", "食堂建议"],
            "推荐美食": ["美食推荐", "进入美食推荐", "推荐菜品", "有什么好吃的", "吃什么", "推荐好吃的", "吃啥", "吃点什么", "什么好吃"],
            "设置口味": ["我喜欢吃", "喜欢吃", "不喜欢吃", "随便", "喜欢", "口味设置", "调整口味"],
            "设置种类": ["我想吃", "类型设置", "调整种类", "改变种类", "种类偏好"],
            "查询时间": ["现在几点", "什么时间", "几点了", "报时", "时间", "现在几点了"],
            "查询天气": ["今天天气", "天气怎么样", "会下雨吗", "温度多少", "天气预报", "天气"],
            "调整语速": ["说话速度", "语速调整", "说快点", "说慢点", "改变语速", "调快语速", "调慢语速", "语速", "说话"],
            "退出": ["再见", "结束", "拜拜", "goodbye", "bye", "关闭", "退出程序", "退出系统"],
            "换一个": ["换个推荐", "换一家", "下一个", "其他选择", "还有吗", "换一换", "再推荐一个"],
            "帮助": ["帮助", "怎么用", "使用说明", "功能介绍", "命令列表"],
            "播放音乐": ["听音乐", "我想听音乐", "播放一首歌", "来点音乐", "开始播放音乐"],
            "停止音乐": ["停止播放音乐", "停音乐", "音乐停止", "停止歌声", "停止播放", "别放了", "安静", "停下来"],
            "暂停音乐": ["暂停", "暂停播放", "暂停音乐", "停一下音乐", "音乐暂停", "停一会儿"],
            "继续音乐": ["继续播放", "继续音乐", "恢复播放", "音乐继续", "继续"],
            "换一首": ["更换歌曲", "换首歌", "下一首", "换一首音乐", "播放下一首", "换首歌"]
        }

        # 偏好词映射，包括“随便”
        self.preference_synonyms = {
            "喜欢": ["爱吃", "想吃", "偏好", "喜爱", "好吃"],
            "不喜欢": ["不爱吃", "不想吃", "讨厌", "不要", "难吃"],
            "随便": ["随意", "无所谓", "任意", "都可以"]
        }

        # 口味词映射
        self.flavor_synonyms = {
            "辣": ["麻辣", "重庆辣", "川辣", "中辣", "微辣", "辣的"],
            "甜": ["甜味", "甜口", "甜甜的", "甜的"],
            "酸": ["酸味", "酸口", "酸酸的", "酸的"],
            "咸": ["咸口", "重口", "咸咸的", "咸的"]
        }

        # 食物种类映射，仅限“米”、“面”、“其他”
        self.kind_synonyms = {
            "米": ["米", "米饭", "饭"],
            "面": ["面", "面条", "面食"],
            "其他": ["其他", "其他种类", "其他类型"]
        }

        # 语气词和修饰词词典
        self.modal_words = {
            '语气词': [
                '啊', '呢', '吧', '呀', '哇', '哦', '噢', '嘛', '呐',
                '啦', '哎', '诶', '唉', '哈', '么', '吗', '捏', '喔'
            ],
            '程度词': [
                '很', '非常', '特别', '真', '太', '好', '比较', '稍微',
                '略微', '有点', '一点', '极其', '格外', '分外'
            ],
            '时间词': [
                '现在', '马上', '立即', '立刻', '赶快', '待会', '等会',
                '一会', '稍后', '等下'
            ],
            '礼貌用语': [
                '请', '麻烦', '劳驾', '能否', '可以', '能不能', '是否',
                '谢谢', '感谢'
            ]
        }

        # 核心意图模式
        self.intention_patterns = {
            "打招呼": [
                r".*(?:你好|hello|hi).*",
                r"(?:早上|中午|下午|晚上)好"
            ],
            "推荐食堂": [
                r".*哪个.*(?:食堂|餐厅).*",
                r".*(?:食堂|餐厅).*推荐.*",
                r".*去哪.*吃.*"
            ],
            "推荐美食": [
                r".*(?:推荐|有什么).*(?:好吃的|美食).*",
                r".*今天吃什么.*",
                r".*吃.*推荐.*"
            ],
            "设置口味": [
                r".*(?:喜欢吃|不喜欢吃|随便).*"
            ],
            "设置种类": [
                r".*(?:我喜欢|不喜欢|随便).*"
            ],
            "查询时间": [
                r".*(?:现在几点|几点了|什么时间).*",
                r".*报时.*"
            ],
            "查询天气": [
                r".*(?:今天天气|天气怎么样|会下雨吗|温度多少|天气预报).*",
                r".*天气.*"
            ],
            "调整语速": [
                r".*(?:说话速度|语速调整|说快点|说慢点|改变语速|调快语速|调慢语速|语速|说话).*",
                r".*语速快一点.*",
                r".*语速慢一点.*",
                r".*调整语速.*",
                r".*改变语速.*"
            ],
            "退出": [
                r".*(?:再见|结束|拜拜|goodbye|bye|关闭|退出程序|退出系统).*"
            ],
            "换一个": [
                r".*(?:换个推荐|换一家|下一个|其他选择|还有吗|换一换|再推荐一个).*"
            ],
            "帮助": [
                r".*(?:帮助|怎么用|使用说明|功能介绍|命令列表).*"
            ],
            "播放音乐": [
                r".*(?:播放音乐|听音乐|我想听音乐|播放一首歌|来点音乐|开始播放音乐).*"
            ],
            "停止音乐": [
                r".*(?:停止音乐|停止播放音乐|停音乐|音乐停止|停止歌声).*"
            ],
            "暂停音乐": [
                r".*(?:暂停音乐|暂停播放|停一下音乐|音乐暂停).*"
            ],
            "继续音乐": [
                r".*(?:继续音乐|继续播放|恢复播放|音乐继续).*"
            ],
            "换一首": [
                r".*(?:换一首|更换歌曲|换首歌|下一首|换一首音乐|播放下一首).*"
            ]
            # 可以根据需要添加更多模式
        }

    def clean_text(self, text: str) -> str:
        """清理文本，去除语气词等干扰因素"""
        words_with_pos = pseg.cut(text)
        cleaned_words = []

        for word, pos in words_with_pos:
            # 跳过语气词
            if word in self.modal_words['语气词']:
                continue
            # 保留核心语义词
            if pos in ['n', 'v', 'a', 'r', 'q']:  # 名词、动词、形容词、代词、量词
                cleaned_words.append(word)

        return ' '.join(cleaned_words)

    def normalize_text(self, text: str) -> str:
        """标准化文本，去除标点符号和多余空格，并转换为小写"""
        text = re.sub(r'[^\w\s]', '', text)
        text = ' '.join(text.split())
        return text.lower()

    def extract_context(self, text: str) -> Dict:
        """提取上下文信息"""
        return {
            'original_text': text,
            'cleaned_text': self.clean_text(text),
            'normalized_text': self.normalize_text(text),
            'intensity': self.extract_intensity(text),
            'is_urgent': self.extract_urgency(text),
            'is_polite': self.detect_politeness(text)
        }

    def extract_intensity(self, text: str) -> float:
        """提取语气强度"""
        intensity = 1.0
        for degree_word in self.modal_words['程度词']:
            if degree_word in text:
                if degree_word in ['非常', '特别', '极其', '太', '格外', '分外']:
                    intensity *= 1.5
                elif degree_word in ['有点', '稍微', '略微', '比较']:
                    intensity *= 0.8
        return intensity

    def extract_urgency(self, text: str) -> bool:
        """提取时间紧迫度"""
        return any(word in text for word in self.modal_words['时间词'])

    def detect_politeness(self, text: str) -> bool:
        """检测是否使用礼貌用语"""
        return any(word in text for word in self.modal_words['礼貌用语'])

    def find_best_command(self, context: Dict) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        找到最匹配的命令及其参数

        Returns:
            Tuple containing (command, preference, parameter)
        """
        text = context['normalized_text']

        # 通过同义词匹配找到命令
        best_command = None
        best_score = 0

        for cmd, synonyms in self.command_synonyms.items():
            for syn in [cmd] + synonyms:
                if syn in text:
                    score = len(syn)
                    if score > best_score:
                        best_score = score
                        best_command = cmd

        if not best_command:
            # 通过模式匹配找到命令
            for cmd, patterns in self.intention_patterns.items():
                if any(re.match(pattern, text) for pattern in patterns):
                    best_command = cmd
                    break

        # 初始化返回值
        preference = None
        param = None

        # 检查是否为偏好设置
        if not best_command:
            for pref, synonyms in self.preference_synonyms.items():
                for syn in [pref] + synonyms:
                    if syn in text:
                        # 检查是否包含口味或种类词
                        flavor_found = None
                        for flavor, flavor_syns in self.flavor_synonyms.items():
                            if any(f in text for f in [flavor] + flavor_syns):
                                flavor_found = flavor
                                break
                        if flavor_found:
                            return "设置口味", pref, flavor_found
                        kind_found = None
                        for kind, kind_syns in self.kind_synonyms.items():
                            if any(k in text for k in [kind] + kind_syns):
                                kind_found = kind
                                break
                        if kind_found:
                            return "设置种类", pref, kind_found

        # 如果找到命令，进一步提取参数
        if best_command:
            if best_command == "调整语速":
                # 定义可能的语速表述
                speed_phrases = [
                    "快一点", "快点", "快些", "快速", "加快", "快一些", "说快点",
                    "慢一点", "慢点", "慢些", "慢速", "放慢", "慢一些", "说慢点",
                    "正常", "普通", "标准", "一般", "默认", "正常速度", "标准速度", "恢复正常"
                ]
                # 查找文本中是否包含语速表述
                for phrase in speed_phrases:
                    if phrase in text:
                        param = phrase
                        break
                return best_command, None, param
            elif best_command in ["设置口味", "设置种类"]:
                # 提取偏好和参数
                for pref, synonyms in self.preference_synonyms.items():
                    if any(syn in text for syn in [pref] + synonyms):
                        preference = pref
                        break

                if best_command == "设置口味":
                    for flavor, flavor_syns in self.flavor_synonyms.items():
                        if any(f in text for f in [flavor] + flavor_syns):
                            param = flavor
                            break
                elif best_command == "设置种类":
                    for kind, kind_syns in self.kind_synonyms.items():
                        if any(k in text for k in [kind] + kind_syns):
                            param = kind
                            break

                return best_command, preference, param

            else:
                # 对于其他命令，没有额外参数
                return best_command, None, None

        # 如果仍然没找到命令，返回None
        return None, None, None

    def format_response(self, response: str, context: Dict) -> str:
        """根据上下文格式化响应"""
        if context['is_polite']:
            response = f"好的，{response}"

        if context['is_urgent']:
            response = f"搞定！{response}"

        if context['intensity'] > 1.2:
            response += "！"

        return response

    def parse_command(self, text: str) -> str:
        """解析命令入口"""
        try:
            # 提取上下文
            context = self.extract_context(text)

            # 尝试使用现有的语法解析
            try:
                parsed = command.parseString(context['cleaned_text'], parseAll=True)
                result = self.execute(parsed)
                return self.format_response(result, context)
            except ParseException:
                # 如果语法解析失败，使用自然语言理解
                cmd, preference, param = self.find_best_command(context)
                if cmd:
                    # 构建一个类似于解析后的列表
                    parsed_command = [cmd]
                    if preference:
                        parsed_command.append(preference)
                    if param:
                        parsed_command.append(param)
                    result = self.execute(parsed_command)
                    return self.format_response(result, context)
                else:
                    suggestions = self.get_suggestions(text)
                    return f"抱歉，我不太理解您的意思。您是想要{suggestions}吗？"

        except Exception as e:
            error_message = f"处理命令时出错: {text}\n错误: {str(e)}"
            print(error_message)
            return error_message

    def execute(self, parsed: List[str]) -> str:
        """执行解析后的命令"""
        cmd = parsed[0] if len(parsed) > 0 else None
        if not cmd:
            return "抱歉，我没有理解您的指令"

        if cmd == "打招呼":
            return self.robot.greet()
        elif cmd == "推荐食堂":
            return self.robot.recommend_canteen()
        elif cmd == "推荐美食":
            return self.robot.recommend_food()
        elif cmd == "设置口味":
            if len(parsed) >= 3 and parsed[1]:
                preference = parsed[1]
                flavor = parsed[2]
                setting_reply = self.robot.set_flavor_preference(preference, flavor)
                # 检查当前状态，如果是美食推荐，则立即更新推荐
                if self.robot.current_state == "美食推荐":
                    recommendations = self.robot.recommend_food()
                    return f"{setting_reply} {recommendations}"
                return setting_reply
            elif len(parsed) >= 2 and parsed[1] == "随便":
                # 处理“口味随便”的情况
                setting_reply = self.robot.set_flavor_preference("随便")
                # 检查当前状态，如果是美食推荐，则立即更新推荐
                if self.robot.current_state == "美食推荐":
                    recommendations = self.robot.recommend_food()
                    return f"{setting_reply} {recommendations}"
                return setting_reply
            return "请指定您的口味偏好，例如：'设置口味 喜欢酸'，或者说'设置口味 随便'"
        elif cmd == "设置种类":
            if len(parsed) >= 3 and parsed[1]:
                preference = parsed[1]
                kind = parsed[2]
                setting_reply = self.robot.set_kind_preference(preference, kind)
                # 检查当前状态，如果是美食推荐，则立即更新推荐
                if self.robot.current_state == "美食推荐":
                    recommendations = self.robot.recommend_food()
                    return f"{setting_reply} {recommendations}"
                return setting_reply
            elif len(parsed) >= 2 and parsed[1] == "随便":
                # 处理“种类随便”的情况
                setting_reply = self.robot.set_kind_preference("随便")
                # 检查当前状态，如果是美食推荐，则立即更新推荐
                if self.robot.current_state == "美食推荐":
                    recommendations = self.robot.recommend_food()
                    return f"{setting_reply} {recommendations}"
                return setting_reply
            return "请指定您的种类偏好，例如：'设置种类 喜欢米'，或者说'设置种类 随便'"
        elif cmd == "查询时间":
            return self.robot.query_time()
        elif cmd == "查询天气":
            return self.robot.query_weather()
        elif cmd == "调整语速":
            if len(parsed) >= 2 and parsed[1]:
                # 处理各种可能的语速表述
                speed_mapping = {
                    # 快速相关表述
                    "快": "快",
                    "快点": "快",
                    "快一些": "快",
                    "快一点": "快",
                    "快些": "快",
                    "快速": "快",
                    "加快": "快",
                    "说快点": "快",

                    # 慢速相关表述
                    "慢": "慢",
                    "慢点": "慢",
                    "慢一些": "慢",
                    "慢一点": "慢",
                    "慢些": "慢",
                    "慢速": "慢",
                    "放慢": "慢",
                    "说慢点": "慢",

                    # 正常速度相关表述
                    "正常": "正常",
                    "普通": "正常",
                    "标准": "正常",
                    "一般": "正常",
                    "默认": "正常",
                    "正常速度": "正常",
                    "标准速度": "正常",
                    "恢复正常": "正常"
                }

                # 获取用户输入的速度表述
                user_speed = parsed[1].strip()
                # 转换为标准速度参数
                speed = speed_mapping.get(user_speed)

                if speed:
                    return self.robot.adjust_speed(speed)
                else:
                    # 如果输入不匹配任何预设，给出提示
                    speed_tips = [
                        "请说'快一点'、'正常'或'慢一点'来调整语速",
                        "您可以说'快点'、'正常速度'或'慢点'来设置语速",
                        "试试说'说快点'、'标准速度'或'说慢点'吧",
                        "可以使用'快速'、'普通'或'慢速'来调整语速哦",
                        "语速可以设置为'快'、'正常'或'慢'～"
                    ]
                    return random.choice(speed_tips)

            # 未提供速度参数时的提示
            help_messages = [
                "请告诉我您想要的语速，比如'调整语速 快一点'",
                "您想要调整到什么语速呢？可以说'调整语速 正常'",
                "请指定想要的语速，例如：'调整语速 慢一点'",
                "语速调整需要说明具体速度，比如'调整语速 标准'",
                "您可以这样调整语速：'调整语速 快点'"
            ]
            return random.choice(help_messages)
        elif cmd == "退出":
            return self.robot.exit()
        elif cmd == "换一个":
            return self.robot.change_canteen()
        elif cmd == "帮助":
            return self.robot.help()
        elif cmd == "播放音乐":
            return self.robot.play_music()
        elif cmd == "停止音乐":
            return self.robot.stop_music()
        elif cmd == "暂停音乐":
            return self.robot.pause_music()
        elif cmd == "继续音乐":
            return self.robot.resume_music()
        elif cmd == "换一首":
            return self.robot.change_song()
        else:
            unknown_cmd = f"未知命令: {cmd}"
            print(unknown_cmd)
            return unknown_cmd

    def get_suggestions(self, text: str) -> str:
        """获取可能的命令建议"""
        suggestions = []
        for cmd, synonyms in self.command_synonyms.items():
            for syn in synonyms:
                if syn in text:
                    suggestions.append(cmd)
                    break

        if suggestions:
            unique_suggestions = list(set(suggestions))  # 去重
            return '、'.join(unique_suggestions)
        return "打招呼、推荐食堂、推荐美食、设置口味、设置种类、查询时间、查询天气、调整语速、退出、播放音乐、暂停音乐、继续音乐、换一首等功能"
