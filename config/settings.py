"""Application settings facade.

Business configuration is loaded from config.yaml. Secrets and machine-local
overrides are loaded from .env.
"""

import os
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv

from config.app_config import load_app_config

if os.getenv("PYTHON_DOTENV_DISABLED", "").strip().lower() not in {
    "1",
    "true",
    "yes",
    "on",
}:
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


MIGRATED_CONFIG_ENV_KEYS = {
    "ENABLED_SOURCES",
    "INITIAL_COLLECT_COUNT",
    "TOP_N_SELECT_COUNT",
    "TIME_RANGE_MIN",
    "TIME_RANGE_MAX",
    "WECHAT_MP_ACCOUNTS",
    "WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT",
    "WECHAT_MP_LOOKBACK_DAYS",
    "WECHAT_MP_LOGIN_TIMEOUT_SECONDS",
    "WECHAT_MP_HEADLESS",
    "WECHAT_MP_BROWSER_MODE",
    "WECHAT_MP_FETCH_DETAIL_PAGE",
    "WECHAT_MP_SLOW_MO_MS",
    "WECHAT_MP_ACTION_DELAY_SECONDS",
    "WECHAT_MP_ARTICLE_DELAY_SECONDS",
    "WECHAT_MP_PAGE_DELAY_SECONDS",
    "WECHAT_MP_ACCOUNT_DELAY_SECONDS",
    "WECHAT_MP_RAW_OUTPUT_DIR",
    "WECHAT_MP_STORAGE_STATE",
    "WECHAT_SEARCH_KEYWORDS",
    "WECHAT_MAX_RESULTS_PER_KEYWORD",
    "WECHAT_USE_PLAYWRIGHT",
    "WECHAT_FETCH_DETAIL_PAGE",
    "TREND_CRAWLER_RUNTIME_DIR",
    "TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT",
    "TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS",
    "TREND_CRAWLER_RUNTIME_LOGIN_TYPE",
    "XIAOHONGSHU_LOGIN_TYPE",
    "XIAOHONGSHU_SEARCH_KEYWORDS",
    "XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD",
    "XIAOHONGSHU_CREATOR_URLS",
    "XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT",
    "ZHIHU_LOGIN_TYPE",
    "ZHIHU_SEARCH_KEYWORDS",
    "ZHIHU_MAX_RESULTS_PER_KEYWORD",
    "ZHIHU_CREATOR_URLS",
    "ZHIHU_MAX_RESULTS_PER_ACCOUNT",
    "GOOGLE_NEWS_KEYWORDS",
    "GOOGLE_NEWS_MAX_RESULTS_PER_KEYWORD",
    "GOOGLE_NEWS_PERIOD",
    "GOOGLE_NEWS_LANGUAGE",
    "GOOGLE_NEWS_COUNTRY",
    "OUTPUT_DIR",
    "OUTPUT_FILENAME_PATTERN",
    "LONGXIA_CANDIDATE_EXPORT_ENABLED",
    "LONGXIA_CANDIDATE_EXPORT_DIR",
    "LONGXIA_CANDIDATE_CONTENT_MAX_CHARS",
    "LONGXIA_CANDIDATE_TIMEZONE",
}


def _warn_ignored_migrated_env_keys() -> None:
    ignored = sorted(key for key in MIGRATED_CONFIG_ENV_KEYS if key in os.environ)
    if not ignored:
        return
    warnings.warn(
        "Ignoring environment keys that moved to config.yaml: "
        f"{', '.join(ignored)}. Edit the file pointed to by AI_TREND_CONFIG instead.",
        RuntimeWarning,
        stacklevel=2,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
_warn_ignored_migrated_env_keys()
CONFIG_PATH = os.getenv("AI_TREND_CONFIG", "config.yaml").strip() or "config.yaml"
APP_CONFIG = load_app_config(CONFIG_PATH)


def _time_range_hours(time_range_config) -> tuple[int, int]:
    return (time_range_config.min, time_range_config.max)


# ==================== API 配置 ====================
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.4").strip() or "gpt-5.4"
LLM_TIMEOUT_SECONDS = max(10.0, _env_float("LLM_TIMEOUT_SECONDS", 120.0))
LLM_MAX_RETRIES = max(0, _env_int("LLM_MAX_RETRIES", 1))
LLM_MAX_COMPLETION_TOKENS = max(0, _env_int("LLM_MAX_COMPLETION_TOKENS", 0))
LLM_REASONING_EFFORT = os.getenv("LLM_REASONING_EFFORT", "").strip()
SCORE_WORKERS = max(1, _env_int("SCORE_WORKERS", 5))
SCORING_PARSE_FAILURE_SCORE = max(
    1.0,
    min(10.0, _env_float("SCORING_PARSE_FAILURE_SCORE", 1.0)),
)
SCORING_RANDOM_FALLBACK_ON_ALL_PARSE_FAILURES = _env_bool(
    "SCORING_RANDOM_FALLBACK_ON_ALL_PARSE_FAILURES",
    True,
)

# ==================== 采集配置 ====================
INITIAL_COLLECT_COUNT = APP_CONFIG.collection.initial_collect_count
TOP_N_SELECT_COUNT = APP_CONFIG.selection.top_n
TIME_RANGE_MIN = APP_CONFIG.collection.time_range_hours.min
TIME_RANGE_MAX = APP_CONFIG.collection.time_range_hours.max

# ==================== 数据源配置 ====================
ENABLED_SOURCES = APP_CONFIG.enabled_sources

# ==================== 搜狗微信关键词搜索 ====================
WECHAT_SEARCH_KEYWORDS = APP_CONFIG.wechat.keyword_search.keywords
SOGOU_WECHAT_COOKIE = os.getenv("SOGOU_WECHAT_COOKIE", "").strip()
WECHAT_MAX_RESULTS_PER_KEYWORD = (
    APP_CONFIG.wechat.keyword_search.max_results_per_keyword
)
WECHAT_KEYWORD_TIME_RANGE_HOURS = _time_range_hours(
    APP_CONFIG.wechat.keyword_search.time_range_hours
)
WECHAT_USE_PLAYWRIGHT = APP_CONFIG.wechat.keyword_search.use_playwright
WECHAT_FETCH_DETAIL_PAGE = APP_CONFIG.wechat.keyword_search.fetch_detail_page

# ==================== 微信公众平台后台采集 ====================
WECHAT_MP_ACCOUNTS = APP_CONFIG.wechat.account_crawl.accounts
WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT = (
    APP_CONFIG.wechat.account_crawl.max_results_per_account
)
WECHAT_ACCOUNT_TIME_RANGE_HOURS = _time_range_hours(
    APP_CONFIG.wechat.account_crawl.time_range_hours
)
WECHAT_MP_TIME_RANGE_HOURS = WECHAT_ACCOUNT_TIME_RANGE_HOURS
WECHAT_MP_LOOKBACK_DAYS = max(1, (WECHAT_ACCOUNT_TIME_RANGE_HOURS[1] + 23) // 24)
WECHAT_MP_LOGIN_TIMEOUT_SECONDS = (
    APP_CONFIG.wechat.account_crawl.login_timeout_seconds
)
WECHAT_MP_BROWSER_MODE = APP_CONFIG.wechat.account_crawl.browser_mode
WECHAT_MP_HEADLESS = WECHAT_MP_BROWSER_MODE == "headless"
WECHAT_MP_FETCH_DETAIL_PAGE = APP_CONFIG.wechat.account_crawl.fetch_detail_page
WECHAT_MP_SLOW_MO_MS = APP_CONFIG.wechat.account_crawl.rhythm.slow_mo_ms
WECHAT_MP_ACTION_DELAY_SECONDS = (
    APP_CONFIG.wechat.account_crawl.rhythm.action_delay_seconds
)
WECHAT_MP_ARTICLE_DELAY_SECONDS = (
    APP_CONFIG.wechat.account_crawl.rhythm.article_delay_seconds
)
WECHAT_MP_PAGE_DELAY_SECONDS = (
    APP_CONFIG.wechat.account_crawl.rhythm.page_delay_seconds
)
WECHAT_MP_ACCOUNT_DELAY_SECONDS = (
    APP_CONFIG.wechat.account_crawl.rhythm.account_delay_seconds
)
WECHAT_MP_RAW_OUTPUT_DIR = str(
    APP_CONFIG.resolve_path(APP_CONFIG.wechat.account_crawl.raw_output_dir)
)
WECHAT_MP_STORAGE_STATE = str(
    APP_CONFIG.resolve_path(APP_CONFIG.wechat.account_crawl.storage_state)
)

# ==================== TrendCrawlerRuntime 配置 ====================
TREND_CRAWLER_RUNTIME_DIR = APP_CONFIG.resolve_path(APP_CONFIG.trend_crawler_runtime.dir)
TREND_CRAWLER_RUNTIME_PYTHON_BIN = (
    os.getenv("TREND_CRAWLER_RUNTIME_PYTHON_BIN", "").strip()
    or APP_CONFIG.trend_crawler_runtime.python_bin
    or sys.executable
)
TREND_CRAWLER_RUNTIME_MAX_NOTES_COUNT = APP_CONFIG.trend_crawler_runtime.max_notes_count
TREND_CRAWLER_RUNTIME_TIMEOUT_SECONDS = APP_CONFIG.trend_crawler_runtime.timeout_seconds
TREND_CRAWLER_RUNTIME_LOGIN_TYPE = APP_CONFIG.trend_crawler_runtime.login_type

XIAOHONGSHU_LOGIN_TYPE = APP_CONFIG.xiaohongshu.login_type
XIAOHONGSHU_SEARCH_KEYWORDS = APP_CONFIG.xiaohongshu.keyword_search.keywords
XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD = (
    APP_CONFIG.xiaohongshu.keyword_search.max_results_per_keyword
)
XIAOHONGSHU_KEYWORD_TIME_RANGE_HOURS = _time_range_hours(
    APP_CONFIG.xiaohongshu.keyword_search.time_range_hours
)
XIAOHONGSHU_CREATOR_URLS = APP_CONFIG.xiaohongshu.account_crawl.creator_urls
XIAOHONGSHU_MAX_RESULTS_PER_ACCOUNT = (
    APP_CONFIG.xiaohongshu.account_crawl.max_results_per_account
)
XIAOHONGSHU_ACCOUNT_TIME_RANGE_HOURS = _time_range_hours(
    APP_CONFIG.xiaohongshu.account_crawl.time_range_hours
)
XIAOHONGSHU_COOKIE = os.getenv("XIAOHONGSHU_COOKIE", "").strip()

ZHIHU_LOGIN_TYPE = APP_CONFIG.zhihu.login_type
ZHIHU_SEARCH_KEYWORDS = APP_CONFIG.zhihu.keyword_search.keywords
ZHIHU_MAX_RESULTS_PER_KEYWORD = (
    APP_CONFIG.zhihu.keyword_search.max_results_per_keyword
)
ZHIHU_KEYWORD_TIME_RANGE_HOURS = _time_range_hours(
    APP_CONFIG.zhihu.keyword_search.time_range_hours
)
ZHIHU_CREATOR_URLS = APP_CONFIG.zhihu.account_crawl.creator_urls
ZHIHU_MAX_RESULTS_PER_ACCOUNT = (
    APP_CONFIG.zhihu.account_crawl.max_results_per_account
)
ZHIHU_ACCOUNT_TIME_RANGE_HOURS = _time_range_hours(
    APP_CONFIG.zhihu.account_crawl.time_range_hours
)
ZHIHU_COOKIE = os.getenv("ZHIHU_COOKIE", "").strip()

# ==================== Google News 通用关键词搜索 ====================
GOOGLE_NEWS_KEYWORDS = APP_CONFIG.google_news.keywords
GOOGLE_NEWS_MAX_RESULTS_PER_KEYWORD = (
    APP_CONFIG.google_news.max_results_per_keyword
)
GOOGLE_NEWS_PERIOD = APP_CONFIG.google_news.period
GOOGLE_NEWS_LANGUAGE = APP_CONFIG.google_news.language
GOOGLE_NEWS_COUNTRY = APP_CONFIG.google_news.country
GOOGLE_NEWS_PROXY_URL = os.getenv("GOOGLE_NEWS_PROXY_URL", "").strip()

# ==================== 通用资讯配置（保留为可选 legacy source） ====================
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
OUTPUT_DIR = str(APP_CONFIG.resolve_path(APP_CONFIG.output.dir))
OUTPUT_FILENAME_PATTERN = APP_CONFIG.output.filename_pattern
OUTPUT_FORMAT = "markdown"

# ==================== longxia 候选投放配置（默认关闭） ====================
LONGXIA_CANDIDATE_EXPORT_ENABLED = (
    APP_CONFIG.output.longxia_candidate_export_enabled
)
LONGXIA_CANDIDATE_EXPORT_DIR = str(
    APP_CONFIG.resolve_path(APP_CONFIG.output.longxia_candidate_export_dir)
)
LONGXIA_CANDIDATE_CONTENT_MAX_CHARS = (
    APP_CONFIG.output.longxia_candidate_content_max_chars
)
LONGXIA_CANDIDATE_TIMEZONE = APP_CONFIG.output.longxia_candidate_timezone
LONGXIA_SSH_TARGET = os.getenv("LONGXIA_SSH_TARGET", "longxia").strip() or "longxia"
LONGXIA_REMOTE_CANDIDATE_ROOT = (
    os.getenv(
        "LONGXIA_REMOTE_CANDIDATE_ROOT",
        "/home/admin/neo/auto_gongzhonghao/edu_renjiao/research/trend_candidates",
    ).strip()
    or "/home/admin/neo/auto_gongzhonghao/edu_renjiao/research/trend_candidates"
)

# ==================== 调度配置 ====================
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "08:00").strip() or "08:00"

METRICS_DIR = "./metrics"
HEALTH_CHECK_INTERVAL = 3600

# ==================== 日志配置 ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip() or "INFO"
LOG_FILE = os.getenv("LOG_FILE", "./logs/agent.log").strip() or "./logs/agent.log"
LOG_ROTATION = os.getenv("LOG_ROTATION", "00:00").strip() or "00:00"
LOG_RETENTION = os.getenv("LOG_RETENTION", "30 days").strip() or "30 days"
LOG_COMPRESSION = os.getenv("LOG_COMPRESSION", "").strip() or None

SOURCE_KEYWORDS = {
    "wechat": WECHAT_SEARCH_KEYWORDS,
    "wechat_mp": WECHAT_MP_ACCOUNTS,
    "xiaohongshu": XIAOHONGSHU_SEARCH_KEYWORDS,
    "zhihu": ZHIHU_SEARCH_KEYWORDS,
    "google_news": GOOGLE_NEWS_KEYWORDS,
    "general": GENERAL_SEARCH_KEYWORDS,
    "demo": [],
}

SOURCE_CREATOR_URLS = {
    "xiaohongshu": XIAOHONGSHU_CREATOR_URLS,
    "zhihu": ZHIHU_CREATOR_URLS,
}

SOURCE_KEYWORD_TIME_RANGES = {
    "wechat": WECHAT_KEYWORD_TIME_RANGE_HOURS,
    "xiaohongshu": XIAOHONGSHU_KEYWORD_TIME_RANGE_HOURS,
    "zhihu": ZHIHU_KEYWORD_TIME_RANGE_HOURS,
    "google_news": (TIME_RANGE_MIN, TIME_RANGE_MAX),
    "general": (TIME_RANGE_MIN, TIME_RANGE_MAX),
    "demo": (TIME_RANGE_MIN, TIME_RANGE_MAX),
}

SOURCE_ACCOUNT_TIME_RANGES = {
    "wechat_mp": WECHAT_ACCOUNT_TIME_RANGE_HOURS,
    "xiaohongshu": XIAOHONGSHU_ACCOUNT_TIME_RANGE_HOURS,
    "zhihu": ZHIHU_ACCOUNT_TIME_RANGE_HOURS,
}

SOURCE_RESULT_LIMITS = {
    "wechat": WECHAT_MAX_RESULTS_PER_KEYWORD,
    "wechat_mp": WECHAT_MP_MAX_ARTICLES_PER_ACCOUNT,
    "xiaohongshu": XIAOHONGSHU_MAX_RESULTS_PER_KEYWORD,
    "zhihu": ZHIHU_MAX_RESULTS_PER_KEYWORD,
    "google_news": GOOGLE_NEWS_MAX_RESULTS_PER_KEYWORD,
    "general": GENERAL_MAX_LINKS_PER_SITE,
}


def get_source_keywords(source_name: str) -> list[str]:
    """Return configured keywords for one source."""
    return SOURCE_KEYWORDS.get(source_name, [])


def get_source_creator_urls(source_name: str) -> list[str]:
    """Return configured creator account URLs for one source."""
    return SOURCE_CREATOR_URLS.get(source_name, [])


def get_source_keyword_time_range(source_name: str) -> tuple[int, int]:
    """Return configured keyword-search time range for one source."""
    return SOURCE_KEYWORD_TIME_RANGES.get(source_name, (TIME_RANGE_MIN, TIME_RANGE_MAX))


def get_source_account_time_range(source_name: str) -> tuple[int, int]:
    """Return configured account-crawl time range for one source."""
    return SOURCE_ACCOUNT_TIME_RANGES.get(source_name, (TIME_RANGE_MIN, TIME_RANGE_MAX))
