# README

## 作业说明

### 题目：基于领域特定语言的客服机器人设计与实现
领域特定语言（Domain Specific Language，DSL）可以提供一种相对简单的文法，用于特定领域的业务流程定制。本作业要求定义一个领域特定脚本语言，这个语言能够描述在线客服机器人（机器人客服是目前提升客服效率的重要技术，在银行、通信和商务等领域的线上服务系统中有广泛的应用）的自动应答逻辑，完成对用户输入的理解和根据输入执行这个脚本，可以根据用户的不同输入，根据脚本的逻辑设计给出相应的应答。

**基本要求**

1. 脚本语言的语法可以自由定义，只要语义上满足描述客服机器人自动应答逻辑的要求。
2. 程序输入输出形式不限，可以简化为纯命令行界面。
3. 应该给出几种不同的脚本格式范例，对不同脚本范例解释器执行之后会有不同的行为表现。

**考核说明**

本作业考察学生规范编写代码、合理设计程序、解决工程问题等方面的综合能力。满分100分，具体评分标准如下：

**风格（15分）**

- 代码注释：6分
- 命名：6分
- 其它：3分

**设计和实现（30分）**

- 数据结构：7分
- 模块划分：7分
- 功能：8分
- 文档：8分

**接口（15分）**

- 程序间接口：8分
- 人机接口：7分

**测试（30分）**

- 测试脚本：15分
- 自动测试脚本：15分

**备注**

- 抄袭或有意被抄袭均为0分



## 项目概述

### 设计背景

生活在校园里的许多同学每天中午都会为去哪个食堂吃饭，吃什么困扰？为了解决大家的选择困难症，设计了**“邮小食（U Shall Eat）”**对话机器人为大家提供帮助。



### 核心功能

1. **打招呼功能**
   邮小食通过获取当前时间，判断是早上、中午、下午、晚上或深夜等时段，并根据不同时间段向用户打招呼。同时，邮小食人会简要介绍自己具备的其它功能，提升用户体验。
2. **食堂推荐**
   邮小食根据用户需求随机推荐一个食堂，并提供其所在位置。可推荐的食堂包括：
   - 风味餐厅：综合食堂一楼
   - 学宜餐厅：综合食堂二楼
   - 民族餐厅：综合食堂四楼
   - 学苑风味餐厅：学生餐厅对面
   - 老食堂：学生餐厅一层
   - 清真餐厅：学生餐厅二层
   - 麦当劳：综合食堂对面
   - 金谷园饺子馆：学校东北角北侧
3. **美食推荐**
   邮小食通过向用户询问不喜欢的食物种类（如米、面、麻辣烫、烤盘饭、汉堡等）和口味（如酸、甜、辣、咸等），并根据用户的选择，排除不喜欢的选项，从数据库中筛选并推荐符合喜好的美食。
4. **时间查询**
   用户可以查询当前时间，邮小食会返回准确的时间信息。
5. **天气查询**
   用户可以查询当前天气，邮小食会提供当前地区的天气状况及温度等信息。
6. **音乐播放**
   机器人可以根据用户的需求播放音乐，提供一个简洁的娱乐功能。



### 项目目录

```python
U Shall Eat
├── build/main            # 打包后的构建文件
├── dist/                 # 分发包目录，存放打包后的可执行文件或安装包
├── dsl/                  # 定义和解析领域特定语言的模块
│   ├── __init__.py       # 包初始化文件
│   ├── grammar.py        # 定义 DSL 语法规则
│   └── parser.py         # 实现 DSL 的语法解析
├── logs/                 # 日志文件目录，用于记录运行和调试信息
├── resources/            # 静态资源文件
│   ├── music/            # 音乐库目录
│   ├── food_list.csv     # 美食列表
│   ├── background.gif    # 主界面使用的背景
│   └── other images...   # 其他图片文件（如 boy.png, robot.png 等）
├── src/                  # 主应用代码目录
│   ├── __init__.py       # 包初始化文件
│   ├── client.py         # 客户端主页面代码
│   ├── history.py        # 历史记录处理模块
│   ├── robot.py          # 机器人核心逻辑模块
│   └── server.py         # 服务端代码
├── test/                 # 测试文件目录
│   ├── cases/            # 测试用例目录
│   ├── logs/             # 测试过程中生成的日志文件
│   ├── reports/          # 测试报告存储目录
│   ├── run/              # 测试运行脚本
│   │   ├── run_test_parser.py  # 测试 DSL 解析器的运行脚本
│   │   ├── run_test_robot.py   # 测试机器人功能的运行脚本
│   └── test_*.py         # 单元测试文件（如 test_parser.py, test_robot.py 等）
├── main.py               # 项目主入口文件
├── main.spec             # PyInstaller 打包配置文件
├── requirements.txt      # Python 项目依赖列表
└── README.md             # 项目文档
```

**目录说明**

1. **主应用代码**：
   位于 `src/`，核心逻辑模块包括客户端、服务端、机器人逻辑等。
2. **DSL 模块**：
   单独放置在 `dsl/`，实现领域特定语言的语法规则和解析器功能。
3. **静态资源**：
   所有图片、GIF 和数据文件集中于 `resources/`，包括音乐文件子目录。
4. **测试代码**：
   `test/` 中划分为测试用例、运行脚本、日志和报告，方便测试的组织和结果分析。
5. **依赖和配置**：
   `requirements.txt` 定义依赖，`main.spec` 用于打包配置。



### 代码风格

本项目严格遵循了Python工程实践标准，包括PEP 8（Python Enhancement Proposal 8）的编码规范。具体遵循的规范包括：

1. **代码缩进与行长度**：使用4个空格进行缩进，避免使用Tab。每行代码的长度不超过79个字符，确保代码的可读性。
2. **变量命名**：
   - 使用小写字母和下划线（snake_case）来命名变量和函数名。
   - 类名采用首字母大写的驼峰式命名（CamelCase）。
   - 常量使用全大写字母和下划线（UPPER_SNAKE_CASE）。
3. **注释**：
   - 为每个模块、类和函数编写文档字符串（docstring），详细说明功能、参数及返回值，符合PEP 257标准。
   - 使用行内注释说明复杂逻辑或重要部分，确保其他开发者或团队成员能快速理解代码意图。
   - 注释应简洁明了，避免过于冗长或不必要的解释。
4. **空行**：
   - 每个函数或类之间使用两个空行，确保代码结构清晰，便于区分不同部分。
   - 在函数内部适当使用空行分隔逻辑块，使代码更具可读性。
5. **异常处理**：
   - 遵循Python的异常处理规范，尽量避免捕获不必要的异常。
   - 在代码中明确指出可能抛出的异常，并在函数内使用`try`和`except`块进行捕获和处理。



### 程序运行

若运行原代码，请启动项目根目录内的 `main.py` ，启动前建议提前安装相关依赖：

```bash
pip install -r requirements.txt
```



### 其他附件

用户使用说明请查看 `邮小食用户使用指南.pdf`，开发与维护请查看 `邮小食开发与维护指南.pdf`

