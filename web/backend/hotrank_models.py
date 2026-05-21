from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HotrankChannelItem(BaseModel):
    id: int | None = None
    channel_id: int
    channel_name: str
    rank: int
    title: str
    url: str = ""
    hot: str = ""
    hot_value: float | None = None
    hot_tag: str = ""
    summary: str = ""
    created_at: str | None = None


class HotrankFetchResult(BaseModel):
    channel_id: int
    channel_name: str
    ok: bool
    items: list[HotrankChannelItem] = Field(default_factory=list)
    balance: int | None = None
    error: str = ""
    raw_response: dict[str, Any] = Field(default_factory=dict)


class HotrankTrendEvidence(BaseModel):
    channel_id: int
    channel_name: str
    rank: int
    title: str
    url: str = ""
    hot: str = ""
    hot_value: float | None = None
    hot_tag: str = ""
    summary: str = ""
    created_at: str | None = None


class HotrankTrendTopic(BaseModel):
    id: str
    title: str
    category: str
    trend_score: float
    platform_count: int
    evidence_count: int
    total_hot_value: float
    latest_created_at: str | None = None
    channels: list[str]
    score_parts: dict[str, float]
    evidence: list[HotrankTrendEvidence]


class HotrankThemeSearch(BaseModel):
    id: str
    title: str
    trend_score: float
    platform_count: int
    evidence_count: int
    total_hot_value: float


class HotrankThemeSummary(BaseModel):
    category: str
    total_score: float
    topic_count: int
    evidence_count: int
    top_searches: list[HotrankThemeSearch]


class HotrankSnapshot(BaseModel):
    run_id: str
    created_at: str
    source: str = "cimidata_hotrank"
    channels_requested: list[int]
    channels_succeeded: list[int]
    channels_failed: list[int]
    raw_item_count: int
    top_trends: list[HotrankTrendTopic]
    theme_summaries: list[HotrankThemeSummary] = Field(default_factory=list)
    category_counts: dict[str, int]
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class HotrankRunRequest(BaseModel):
    channel_ids: list[int] | None = None
    limit: int = 10


class HotrankLatestResponse(BaseModel):
    snapshot: HotrankSnapshot | None = None


class HotrankRunResponse(BaseModel):
    snapshot: HotrankSnapshot


HotrankRunStatusValue = Literal[
    "queued",
    "fetching",
    "classifying",
    "saving",
    "succeeded",
    "failed",
]


class HotrankRunStatus(BaseModel):
    run_id: str
    status: HotrankRunStatusValue
    message: str = ""
    progress: float = Field(0.0, ge=0.0, le=1.0)
    channel_ids: list[int] = Field(default_factory=list)
    limit: int = 10
    total_topics: int = 0
    classified_topics: int = 0
    estimated_seconds_remaining: float | None = None
    snapshot: HotrankSnapshot | None = None
    error: str = ""
    warnings: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
