"""
项目配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ==================== API 配置 ====================
# 大模型 API 配置（根据实际使用的服务商修改）
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.4")

# ==================== 采集配置 ====================
# 采集数量配置
INITIAL_COLLECT_COUNT = 30  # 首轮采集数量（去重后送入LLM打分的数量）
TOP_N_SELECT_COUNT = 10     # LLM打分后最终筛选的Top N数量

# TrendCrawlerRuntime 每个关键词爬取的数量
TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT = 20  # 设置为20的倍数（20、40、60...）

# 搜索关键词列表（针对家长群体的教育热点）
KEYWORDS = [
    # === 核心政策与改革 ===
    "教育改革",
    "中考"

    # # === 升学考试（家长最关注）===
    # "小升初",
    # "中考",
    #
    # # === 家庭教育方法 ===
    # "家庭教育",
    # "学习习惯培养",
    # "亲子沟通",
    # "孩子注意力训练",
    #
    # # === 学科学习技巧 ===
    # "数学思维",
    # "英语启蒙",
    # "语文阅读",
    # "作文写作",
    #
    # # === 教育产品与资源 ===
    # "课外班选择",
    # "教辅资料推荐",
    # "在线教育",
    #
    # # === 教育焦虑与社会话题 ===
    # "内卷教育",
    # "心理健康",
    # "青春期教育",
]

# 时间范围配置（小时）- 采集最近N小时内的内容
TIME_RANGE_MIN = 0          # 最小时间范围（0表示包含最新发布）
TIME_RANGE_MAX = 48        # 最大时间范围（扩大到30天，测试用）

# ==================== 数据源配置 ====================
# 启用的数据源列表，可选值：
# - "wechat": 微信公众号（搜狗微信搜索）
# - "xiaohongshu": 小红书（使用 TrendCrawlerRuntime，需配置浏览器）
# - "zhihu": 知乎（使用 TrendCrawlerRuntime，需配置浏览器）
# - "general": 通用资讯（可扩展）
# - "demo": 演示采集器（使用示例数据，测试用）
ENABLED_SOURCES = [
    # "demo",        # 演示采集器（使用示例数据）
    "wechat",      # 公众号（搜狗微信搜索）
    "xiaohongshu", # 小红书（使用 TrendCrawlerRuntime）
    # "zhihu",       # 知乎（使用 TrendCrawlerRuntime）
    # "general",     # 通用资讯（可扩展）
]

# ==================== 输出配置 ====================
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
OUTPUT_FORMAT = "markdown"

# ==================== 调度配置 ====================
SCHEDULE_TIME = "08:00"  # 每日执行时间（24小时制，建议早上8点）

# 监控配置
METRICS_DIR = "./metrics"  # 监控数据存储目录
HEALTH_CHECK_INTERVAL = 3600  # 健康检查间隔（秒）

# ==================== 日志配置 ====================
LOG_LEVEL = "INFO"
LOG_FILE = "./logs/agent.log"