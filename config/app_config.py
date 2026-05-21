"""Typed application configuration loaded from config.yaml."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_SOURCES = {
    "wechat",
    "wechat_mp",
    "xiaohongshu",
    "zhihu",
    "google_news",
    "aihot",
}
DEFAULT_ENABLED_SOURCES = ("google_news",)
DEFAULT_GOOGLE_NEWS_KEYWORDS = ("教育改革", "中考")
LoginType = Literal["qrcode", "cookie", "phone"]
BrowserMode = Literal["auto", "visible", "headless"]
AihotMode = Literal["selected", "all"]
AihotCategory = Literal["ai-models", "ai-products", "industry", "paper", "tip"]
RunMode = Literal["collect_only", "collect_score_report"]
ExecutionMode = Literal["serial", "parallel"]


class ConfigValidationError(ValueError):
    """Raised when config.yaml is missing or invalid."""


class TimeRangeConfig(BaseModel):
    min: int = Field(0, ge=0)
    max: int = Field(24, ge=1)

    @model_validator(mode="after")
    def validate_order(self) -> "TimeRangeConfig":
        if self.max < self.min:
            raise ValueError("time_range_hours.max must be >= min")
        return self


class CollectionConfig(BaseModel):
    initial_collect_count: int = Field(30, ge=1)
    time_range_hours: TimeRangeConfig = Field(default_factory=TimeRangeConfig)


class SelectionConfig(BaseModel):
    top_n: int = Field(10, ge=1)


class RhythmConfig(BaseModel):
    slow_mo_ms: int = Field(300, ge=0)
    action_delay_seconds: float = Field(1.5, ge=0)
    article_delay_seconds: float = Field(3.0, ge=0)
    page_delay_seconds: float = Field(4.0, ge=0)
    account_delay_seconds: float = Field(8.0, ge=0)


class TrendCrawlerRuntimeConfig(BaseModel):
    dir: str = "./TrendCrawlerRuntime"
    python_bin: str = ""
    timeout_seconds: int = Field(900, ge=60)
    max_notes_count: int = Field(20, ge=1)
    login_type: LoginType = "qrcode"


class KeywordSearchConfig(BaseModel):
    enabled: bool = True
    keywords: list[str] = Field(default_factory=list)
    max_results_per_keyword: int = Field(20, ge=1)
    expected_min_results: int = Field(3, ge=0)
    time_range_hours: TimeRangeConfig = Field(default_factory=TimeRangeConfig)


class WechatKeywordSearchConfig(KeywordSearchConfig):
    max_results_per_keyword: int = Field(8, ge=1)
    use_playwright: bool = True
    fetch_detail_page: bool = False


class WechatAccountCrawlConfig(BaseModel):
    enabled: bool = True
    accounts: list[str] = Field(default_factory=list)
    max_results_per_account: int = Field(10, ge=1)
    expected_min_results: int = Field(3, ge=0)
    time_range_hours: TimeRangeConfig = Field(
        default_factory=lambda: TimeRangeConfig(min=0, max=168)
    )
    login_timeout_seconds: int = Field(180, ge=30)
    browser_mode: BrowserMode = "auto"
    fetch_detail_page: bool = True
    raw_output_dir: str = "./raw_data/wechat_mp"
    storage_state: str = "./browser_data/wechat_mp_state.json"
    rhythm: RhythmConfig = Field(default_factory=RhythmConfig)


class CreatorAccountCrawlConfig(BaseModel):
    enabled: bool = True
    creator_urls: list[str] = Field(default_factory=list)
    max_results_per_account: int = Field(20, ge=1)
    expected_min_results: int = Field(3, ge=0)
    time_range_hours: TimeRangeConfig = Field(
        default_factory=lambda: TimeRangeConfig(min=0, max=168)
    )


class WechatConfig(BaseModel):
    keyword_search: WechatKeywordSearchConfig = Field(
        default_factory=WechatKeywordSearchConfig
    )
    account_crawl: WechatAccountCrawlConfig = Field(
        default_factory=WechatAccountCrawlConfig
    )


class CreatorSourceConfig(BaseModel):
    keyword_search: KeywordSearchConfig = Field(default_factory=KeywordSearchConfig)
    account_crawl: CreatorAccountCrawlConfig = Field(
        default_factory=CreatorAccountCrawlConfig
    )
    login_type: LoginType = "qrcode"


class GoogleNewsConfig(BaseModel):
    keywords: list[str] = Field(default_factory=lambda: list(DEFAULT_GOOGLE_NEWS_KEYWORDS))
    max_results_per_keyword: int = Field(20, ge=1)
    expected_min_results: int = Field(3, ge=0)
    period: str = "7d"
    language: str = "zh-CN"
    country: str = "CN"


class AihotConfig(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    mode: AihotMode = "selected"
    categories: list[AihotCategory] = Field(default_factory=list)
    max_results_per_query: int = Field(50, ge=1, le=100)
    expected_min_results: int = Field(3, ge=0)
    base_url: str = "https://aihot.virxact.com"
    request_timeout_seconds: int = Field(10, ge=1, le=60)
    user_agent: str = (
        "AITrend/0.1 (+https://github.com/NeAoo/MediaTrend; "
        "contact: local-user)"
    )


class OutputConfig(BaseModel):
    dir: str = "./output"
    filename_pattern: str = "热点日报_{date}.md"
    material_export_enabled: bool = False
    material_export_dir: str = "./output/materials"
    material_content_max_chars: int = Field(5000, ge=500)
    material_timezone: str = "Asia/Shanghai"


class ScoringPromptConfig(BaseModel):
    system_path: str = "./prompts/scoring_system_prompt.md"
    user_path: str = "./prompts/scoring_user_prompt.md"


class ScoringConfig(BaseModel):
    enabled: bool = False
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-5.4"
    timeout_seconds: float = Field(120.0, ge=10)
    max_retries: int = Field(1, ge=0)
    max_completion_tokens: int = Field(0, ge=0)
    reasoning_effort: str = ""
    workers: int = Field(5, ge=1)
    parse_failure_score: float = Field(1.0, ge=1.0, le=10.0)
    random_fallback_on_all_parse_failures: bool = True
    prompt: ScoringPromptConfig = Field(default_factory=ScoringPromptConfig)


class HotrankAiClassificationPromptConfig(BaseModel):
    system_path: str = "./prompts/hotrank_classification_system_prompt.md"
    user_path: str = "./prompts/hotrank_classification_user_prompt.md"


class HotrankAiClassificationConfig(BaseModel):
    enabled: bool = True
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-5.4"
    workers: int = Field(32, ge=1, le=64)
    timeout_seconds: float = Field(120.0, ge=10)
    max_retries: int = Field(1, ge=0)
    max_completion_tokens: int = Field(80, ge=0)
    reasoning_effort: str = ""
    prompt: HotrankAiClassificationPromptConfig = Field(
        default_factory=HotrankAiClassificationPromptConfig
    )


class HotrankConfig(BaseModel):
    ai_classification: HotrankAiClassificationConfig = Field(
        default_factory=HotrankAiClassificationConfig
    )


class WebConfig(BaseModel):
    default_run_mode: RunMode = "collect_only"
    default_execution_mode: ExecutionMode = "parallel"
    unit_timeout_seconds: int = Field(180, ge=30)


class AppConfig(BaseModel):
    enabled_sources: list[str] = Field(
        default_factory=lambda: list(DEFAULT_ENABLED_SOURCES)
    )
    collection: CollectionConfig = Field(default_factory=CollectionConfig)
    selection: SelectionConfig = Field(default_factory=SelectionConfig)
    wechat: WechatConfig = Field(default_factory=WechatConfig)
    trend_crawler_runtime: TrendCrawlerRuntimeConfig = Field(
        default_factory=TrendCrawlerRuntimeConfig
    )
    xiaohongshu: CreatorSourceConfig = Field(default_factory=CreatorSourceConfig)
    zhihu: CreatorSourceConfig = Field(default_factory=CreatorSourceConfig)
    google_news: GoogleNewsConfig = Field(default_factory=GoogleNewsConfig)
    aihot: AihotConfig = Field(default_factory=AihotConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    hotrank: HotrankConfig = Field(default_factory=HotrankConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    @model_validator(mode="after")
    def validate_enabled_sources_have_inputs(self) -> "AppConfig":
        unsupported = [
            source for source in self.enabled_sources if source not in SUPPORTED_SOURCES
        ]
        if unsupported:
            raise ValueError(
                "Unsupported source names: "
                f"{', '.join(unsupported)}. Supported sources: "
                f"{', '.join(sorted(SUPPORTED_SOURCES))}"
            )
        if (
            "wechat" in self.enabled_sources
            and (
                not self.wechat.keyword_search.enabled
                or not self.wechat.keyword_search.keywords
            )
        ):
            raise ValueError(
                "wechat enabled but wechat.keyword_search is disabled or keywords is empty"
            )
        if (
            "wechat_mp" in self.enabled_sources
            and (
                not self.wechat.account_crawl.enabled
                or not self.wechat.account_crawl.accounts
            )
        ):
            raise ValueError(
                "wechat_mp enabled but wechat.account_crawl is disabled or accounts is empty"
            )
        xiaohongshu_keyword_enabled = (
            self.xiaohongshu.keyword_search.enabled
            and self.xiaohongshu.keyword_search.keywords
        )
        xiaohongshu_account_enabled = (
            self.xiaohongshu.account_crawl.enabled
            and self.xiaohongshu.account_crawl.creator_urls
        )
        if (
            "xiaohongshu" in self.enabled_sources
            and not xiaohongshu_keyword_enabled
            and not xiaohongshu_account_enabled
        ):
            raise ValueError(
                "xiaohongshu enabled but both "
                "enabled keyword_search.keywords and "
                "enabled account_crawl.creator_urls are empty"
            )
        zhihu_keyword_enabled = (
            self.zhihu.keyword_search.enabled
            and self.zhihu.keyword_search.keywords
        )
        zhihu_account_enabled = (
            self.zhihu.account_crawl.enabled
            and self.zhihu.account_crawl.creator_urls
        )
        if (
            "zhihu" in self.enabled_sources
            and not zhihu_keyword_enabled
            and not zhihu_account_enabled
        ):
            raise ValueError(
                "zhihu enabled but both enabled zhihu.keyword_search.keywords and "
                "enabled zhihu.account_crawl.creator_urls are empty"
            )
        if "google_news" in self.enabled_sources and not self.google_news.keywords:
            raise ValueError("google_news enabled but google_news.keywords is empty")
        return self

    def resolve_path(self, value: str) -> Path:
        path = Path(value).expanduser()
        return path if path.is_absolute() else PROJECT_ROOT / path


def load_app_config(path: str | Path = "config.yaml") -> AppConfig:
    config_path = Path(path).expanduser()
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    if not config_path.exists():
        raise ConfigValidationError(f"Config file does not exist: {config_path}")

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigValidationError(f"Invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigValidationError(f"Config root must be a mapping: {config_path}")

    try:
        return AppConfig.model_validate(data)
    except ValidationError as exc:
        raise ConfigValidationError(str(exc)) from exc
    except ValueError as exc:
        raise ConfigValidationError(str(exc)) from exc
