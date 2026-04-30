"""
项目配置文件

推荐做法：
- 优先通过 `.env` 覆盖配置，不要直接改代码里的常量。
- 本地第一次运行建议先只开 `wechat`。
- `run` 需要 `LLM_API_KEY`；只验证采集链路可先用 `search`。
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "y", "on", "enabled"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ==================== API 配置 ====================
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.4").strip() or "gpt-5.4"

# ==================== 采集配置 ====================
INITIAL_COLLECT_COUNT = _env_int("INITIAL_COLLECT_COUNT", 30)
TOP_N_SELECT_COUNT = _env_int("TOP_N_SELECT_COUNT", 10)

KEYWORDS = _env_list(
    "SEARCH_KEYWORDS",
    [
        "教育改革",
        "中考",
    ],
)

TIME_RANGE_MIN = _env_int("TIME_RANGE_MIN", 0)
TIME_RANGE_MAX = _env_int("TIME_RANGE_MAX", 24)

# ==================== 数据源配置 ====================
# 本地第一次运行建议先只开 wechat，确认采集链路正常后再加 xiaohongshu / zhihu / general。
ENABLED_SOURCES = _env_list(
    "ENABLED_SOURCES",
    [
        "wechat",
    ],
)

# ==================== 微信配置 ====================
SOGOU_WECHAT_COOKIE = os.getenv("SOGOU_WECHAT_COOKIE", "").strip()
WECHAT_MAX_RESULTS_PER_KEYWORD = _env_int("WECHAT_MAX_RESULTS_PER_KEYWORD", 8)
WECHAT_USE_PLAYWRIGHT = _env_bool("WECHAT_USE_PLAYWRIGHT", True)
WECHAT_FETCH_DETAIL_PAGE = _env_bool("WECHAT_FETCH_DETAIL_PAGE", False)

# ==================== TrendCrawlerRuntime 配置 ====================
TREND_CRAWLER_RUNTIME_DIR = Path(
    os.getenv("TREND_CRAWLER_RUNTIME_DIR", str(PROJECT_ROOT / "TrendCrawlerRuntime"))
).expanduser().resolve()
TREND_CRAWLER_RUNTIME_PYTHON_BIN = os.getenv("TREND_CRAWLER_RUNTIME_PYTHON_BIN", sys.executable).strip() or sys.executable
TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT = _env_int("TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT", 20)
TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS = _env_int("TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS", 900)
TREND_CRAWLER_RUNTIME_LOGIN_TYPE = os.getenv("TREND_CRAWLER_RUNTIME_LOGIN_TYPE", "qrcode").strip() or "qrcode"

XIAOHONGSHU_LOGIN_TYPE = (
    os.getenv("XIAOHONGSHU_LOGIN_TYPE", TREND_CRAWLER_RUNTIME_LOGIN_TYPE).strip()
    or TREND_CRAWLER_RUNTIME_LOGIN_TYPE
)
XIAOHONGSHU_COOKIE = os.getenv("XIAOHONGSHU_COOKIE", "").strip()

ZHIHU_LOGIN_TYPE = (
    os.getenv("ZHIHU_LOGIN_TYPE", TREND_CRAWLER_RUNTIME_LOGIN_TYPE).strip()
    or TREND_CRAWLER_RUNTIME_LOGIN_TYPE
)
ZHIHU_COOKIE = os.getenv("ZHIHU_COOKIE", "").strip()

# ==================== 通用资讯配置 ====================
GENERAL_MAX_LINKS_PER_SITE = _env_int("GENERAL_MAX_LINKS_PER_SITE", 30)
GENERAL_NEWS_SITES = [
    {
        "name": "教育部",
        "url": "https://www.moe.gov.cn/jyb_xwfb/",
        "type": "official",
    },
    {
        "name": "中国教育新闻网",
        "url": "https://www.jyb.cn/",
        "type": "news",
    },
    {
        "name": "新华网教育",
        "url": "http://education.news.cn/",
        "type": "news",
    },
]

# ==================== 输出配置 ====================
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output").strip() or "./output"
OUTPUT_FORMAT = "markdown"

# ==================== 调度配置 ====================
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "08:00").strip() or "08:00"

METRICS_DIR = "./metrics"
HEALTH_CHECK_INTERVAL = 3600

# ==================== 日志配置 ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip() or "INFO"
LOG_FILE = os.getenv("LOG_FILE", "./logs/agent.log").strip() or "./logs/agent.log"
