"""Typed application configuration loaded from config.yaml."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_SOURCES = {"wechat_mp", "xiaohongshu", "zhihu"}
LoginType = Literal["qrcode", "cookie", "phone"]
BrowserMode = Literal["auto", "visible", "headless"]


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


class WechatMpConfig(BaseModel):
    accounts: list[str] = Field(default_factory=list)
    max_articles_per_account: int = Field(10, ge=1)
    lookback_days: int = Field(7, ge=1)
    login_timeout_seconds: int = Field(180, ge=30)
    browser_mode: BrowserMode = "auto"
    fetch_detail_page: bool = True
    raw_output_dir: str = "./raw_data/wechat_mp"
    storage_state: str = "./browser_data/wechat_mp_state.json"
    rhythm: RhythmConfig = Field(default_factory=RhythmConfig)


class MediaCrawlerConfig(BaseModel):
    dir: str = "./MediaCrawler"
    python_bin: str = ""
    timeout_seconds: int = Field(900, ge=60)
    max_notes_count: int = Field(20, ge=1)
    login_type: LoginType = "qrcode"


class KeywordSourceConfig(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    max_results_per_keyword: int = Field(20, ge=1)
    login_type: LoginType = "qrcode"


class OutputConfig(BaseModel):
    dir: str = "./output"
    filename_pattern: str = "教育热点日报_{date}.md"
    longxia_candidate_export_enabled: bool = False
    longxia_candidate_export_dir: str = "./output/longxia_trend_candidates"
    longxia_candidate_content_max_chars: int = Field(5000, ge=500)
    longxia_candidate_timezone: str = "Asia/Shanghai"


class AppConfig(BaseModel):
    enabled_sources: list[str] = Field(
        default_factory=lambda: ["wechat_mp", "xiaohongshu", "zhihu"]
    )
    collection: CollectionConfig = Field(default_factory=CollectionConfig)
    selection: SelectionConfig = Field(default_factory=SelectionConfig)
    wechat_mp: WechatMpConfig = Field(default_factory=WechatMpConfig)
    media_crawler: MediaCrawlerConfig = Field(default_factory=MediaCrawlerConfig)
    xiaohongshu: KeywordSourceConfig = Field(default_factory=KeywordSourceConfig)
    zhihu: KeywordSourceConfig = Field(default_factory=KeywordSourceConfig)
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
        if "wechat_mp" in self.enabled_sources and not self.wechat_mp.accounts:
            raise ValueError("wechat_mp enabled but wechat_mp.accounts is empty")
        if "xiaohongshu" in self.enabled_sources and not self.xiaohongshu.keywords:
            raise ValueError("xiaohongshu enabled but xiaohongshu.keywords is empty")
        if "zhihu" in self.enabled_sources and not self.zhihu.keywords:
            raise ValueError("zhihu enabled but zhihu.keywords is empty")
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
