# dsl/grammar.py

from pyparsing import (
    Word, Literal, Keyword, OneOrMore, Optional, Combine, Group,
    alphas, alphanums, nums, Suppress, CaselessKeyword, Forward, ZeroOrMore, Or
)

# 定义命令关键词
打招呼 = Keyword("打招呼")
推荐食堂 = Keyword("推荐食堂")
推荐美食 = Keyword("推荐美食")
设置口味 = Keyword("设置口味")
设置种类 = Keyword("设置种类")
查询时间 = Keyword("查询时间")
查询天气 = Keyword("查询天气")
调整语速 = Keyword("调整语速")
退出 = Keyword("退出")
进入美食推荐 = Keyword("进入美食推荐")
进入食堂推荐 = Keyword("进入食堂推荐")
换一个 = Keyword("换一个")
帮助 = Keyword("帮助")
播放音乐 = Keyword("播放音乐")
停止音乐 = Keyword("停止音乐")
暂停音乐 = Keyword("暂停音乐")
继续音乐 = Keyword("继续音乐")
换一首 = Keyword("换一首")

# 定义参数关键词
喜欢 = Keyword("喜欢")
不喜欢 = Keyword("不喜欢")
随便 = Keyword("随便")
快 = Keyword("快")
中 = Keyword("中")
慢 = Keyword("慢")
酸 = Keyword("酸")
甜 = Keyword("甜")
辣 = Keyword("辣")
咸 = Keyword("咸")
米 = Keyword("米")
面 = Keyword("面")
其他 = Keyword("其他")
歌曲名称 = Word(alphas + "中文字符")  # 假设歌曲名称由字母和中文字符组成

# 定义语法结构
command = Forward()

# 设置口味偏好语法
设置口味 = 设置口味 + (喜欢 | 不喜欢 | 随便) + Optional((酸 | 甜 | 辣 | 咸))

# 设置种类偏好语法
设置种类 = 设置种类 + (喜欢 | 不喜欢 | 随便) + Optional((米 | 面 | 其他))

# 调整语速语法
设置速度 = 调整语速 + Optional((快 | 中 | 慢))

# 播放音乐语法
播放音乐 = 播放音乐 + Optional(歌曲名称)

# 暂停音乐语法
暂停音乐 = 暂停音乐

# 继续音乐语法
恢复播放 = 继续音乐

# 更换歌曲语法
切换音乐 = 换一首

# 定义完整的命令语法
command <<= (
    打招呼 |
    推荐食堂 |
    推荐美食 |
    设置口味 |
    设置种类 |
    查询时间 |
    查询天气 |
    设置速度 |
    退出 |
    换一个 |
    帮助 |
    播放音乐 |
    停止音乐 |
    暂停音乐 |
    恢复播放 |
    切换音乐
)
