from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


JobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]
RunMode = Literal["collect_only", "collect_score_report"]
ExecutionMode = Literal["serial", "parallel"]


class ApiError(BaseModel):
    message: str
    details: list[str] = Field(default_factory=list)


class ConfigResponse(BaseModel):
    config: dict[str, Any]
    masked_api_key: str = ""
    has_api_key: bool = False


class SaveConfigRequest(BaseModel):
    config: dict[str, Any]
    api_key: str | None = None


class PromptResponse(BaseModel):
    system_prompt: str
    user_prompt: str
    warnings: list[str] = Field(default_factory=list)


class SavePromptRequest(BaseModel):
    system_prompt: str
    user_prompt: str


class JobCreateRequest(BaseModel):
    run_mode: RunMode = "collect_score_report"
    execution_mode: ExecutionMode = "serial"


class JobEvent(BaseModel):
    job_id: str
    type: str
    message: str = ""
    source: str | None = None
    unit_type: Literal["source", "keyword", "account", "stage"] | None = None
    unit_name: str | None = None
    status: str | None = None
    current_count: int | None = None
    max_count: int | None = None
    expected_min_count: int | None = None
    progress: float | None = None
    created_at: str


class JobSnapshot(BaseModel):
    job_id: str
    status: JobStatus
    run_mode: RunMode
    execution_mode: ExecutionMode
    created_at: str
    updated_at: str
    cancel_requested: bool = False
    events_count: int = 0
    artifacts: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SystemStatus(BaseModel):
    project_root: str
    config_path: str
    env_path: str
    jobs_root: str
    has_api_key: bool
    enabled_sources: list[str]
