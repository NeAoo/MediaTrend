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


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
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
SCORE_WORKERS = max(1, _env_int("SCORE_WORKERS", 5))

# ==================== 采集配置 ====================
INITIAL_COLLECT_COUNT = _env_int("INITIAL_COLLECT_COUNT", 30)
TOP_N_SELECT_COUNT = _env_int("TOP_N_SELECT_COUNT", 10)

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
WECHAT_SEARCH_KEYWORDS = _env_list("WECHAT_SEARCH_KEYWORDS", [])
SOGOU_WECHAT_COOKIE = os.getenv("SOGOU_WECHAT_COOKIE", "").strip()
WECHAT_MAX_RESULTS_PER_KEYWORD = _env_int("WECHAT_MAX_RESULTS_PER_KEYWORD", 8)
WECHAT_USE_PLAYWRIGHT = _env_bool("WECHAT_USE_PLAYWRIGHT", True)
WECHAT_FETCH_DETAIL_PAGE = _env_bool("WECHAT_FETCH_DETAIL_PAGE", False)

# 微信公众平台后台采集：按固定公众号名称抓取最近文章，需要扫码登录公众号后台。
WECHAT_MP_ACCOUNTS = _env_list("WECHAT_MP_ACCOUNTS", [])
WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT = _env_int("WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT", 10)
WECHAT_MP_LOOKBACK_DAYS = _env_int("WECHAT_MP_LOOKBACK_DAYS", 7)
WECHAT_MP_LOGIN_TIMEOUT_SECONDS = _env_int("WECHAT_MP_LOGIN_TIMEOUT_SECONDS", 180)
WECHAT_MP_HEADLESS = _env_bool("WECHAT_MP_HEADLESS", False)
WECHAT_MP_FETCH_DETAIL_PAGE = _env_bool("WECHAT_MP_FETCH_DETAIL_PAGE", True)
WECHAT_MP_SLOW_MO_MS = max(0, _env_int("WECHAT_MP_SLOW_MO_MS", 300))
WECHAT_MP_ACTION_DELAY_SECONDS = max(0.0, _env_float("WECHAT_MP_ACTION_DELAY_SECONDS", 1.5))
WECHAT_MP_ARTICLE_DELAY_SECONDS = max(0.0, _env_float("WECHAT_MP_ARTICLE_DELAY_SECONDS", 3.0))
WECHAT_MP_PAGE_DELAY_SECONDS = max(0.0, _env_float("WECHAT_MP_PAGE_DELAY_SECONDS", 4.0))
WECHAT_MP_ACCOUNT_DELAY_SECONDS = max(0.0, _env_float("WECHAT_MP_ACCOUNT_DELAY_SECONDS", 8.0))
WECHAT_MP_RAW_OUTPUT_DIR = os.getenv("WECHAT_MP_RAW_OUTPUT_DIR", "./raw_data/wechat_mp").strip()
WECHAT_MP_STORAGE_STATE = os.getenv(
    "WECHAT_MP_STORAGE_STATE",
    str(PROJECT_ROOT / "browser_data" / "wechat_mp_state.json"),
).strip()

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
XIAOHONGSHU_SEARCH_KEYWORDS = _env_list("XIAOHONGSHU_SEARCH_KEYWORDS", [])
XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD = _env_int(
    "XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD",
    TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT,
)
XIAOHONGSHU_COOKIE = os.getenv("XIAOHONGSHU_COOKIE", "").strip()

ZHIHU_LOGIN_TYPE = (
    os.getenv("ZHIHU_LOGIN_TYPE", TREND_CRAWLER_RUNTIME_LOGIN_TYPE).strip()
    or TREND_CRAWLER_RUNTIME_LOGIN_TYPE
)
ZHIHU_SEARCH_KEYWORDS = _env_list("ZHIHU_SEARCH_KEYWORDS", [])
ZHIHU_MAX_RESULTS_PER_KEYWORD = _env_int(
    "ZHIHU_MAX_RESULTS_PER_KEYWORD",
    TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT,
)
ZHIHU_COOKIE = os.getenv("ZHIHU_COOKIE", "").strip()

# ==================== 通用资讯配置 ====================
GENERAL_SEARCH_KEYWORDS = _env_list("GENERAL_SEARCH_KEYWORDS", [])
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

SOURCE_KEYWORDS = {
    "wechat": WECHAT_SEARCH_KEYWORDS,
    "wechat_mp": WECHAT_MP_ACCOUNTS,
    "xiaohongshu": XIAOHONGSHU_SEARCH_KEYWORDS,
    "zhihu": ZHIHU_SEARCH_KEYWORDS,
    "general": GENERAL_SEARCH_KEYWORDS,
    "demo": [],
}

SOURCE_RESULT_LIMITS = {
    "wechat": WECHAT_MAX_RESULTS_PER_KEYWORD,
    "wechat_mp": WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT,
    "xiaohongshu": XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD,
    "zhihu": ZHIHU_MAX_RESULTS_PER_KEYWORD,
    "general": GENERAL_MAX_LINKS_PER_SITE,
}


def get_source_keywords(source_name: str) -> list[str]:
    """Return configured keywords for one source."""
    return SOURCE_KEYWORDS.get(source_name, [])
