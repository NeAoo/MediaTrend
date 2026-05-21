from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Callable
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException

from config.app_config import load_app_config
from web.backend.config_service import (
    read_text_file,
    validate_hotrank_prompt,
    write_text_file_with_backup,
)
from web.backend.env_service import read_env_value
from web.backend.hotrank_aggregator import (
    CHANNEL_NAMES,
    DEFAULT_CHANNEL_IDS,
    aggregate_hotrank_results,
)
from web.backend.hotrank_ai_classifier import (
    DEFAULT_CLASSIFICATION_SYSTEM_PROMPT,
    DEFAULT_CLASSIFICATION_USER_PROMPT,
    HotrankAiClassifier,
    HotrankAiClassifierConfig,
)
from web.backend.hotrank_client import CimiDataError, CimiDataHotrankClient
from web.backend.hotrank_models import (
    HotrankFetchResult,
    HotrankLatestResponse,
    HotrankRunRequest,
    HotrankRunResponse,
    HotrankRunStatus,
    HotrankSnapshot,
    HotrankTrendTopic,
)
from web.backend.hotrank_store import HotrankStore
from web.backend.models import PromptResponse, SavePromptRequest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
ENV_PATH = PROJECT_ROOT / ".env"
STORE = HotrankStore(PROJECT_ROOT / "web_jobs" / "hotrank")
router = APIRouter(prefix="/api/hotrank", tags=["hotrank"])
CategoryClassifier = Callable[[list[HotrankTrendTopic]], dict[str, str]]
ASYNC_RUNS: dict[str, HotrankRunStatus] = {}
ASYNC_RUNS_LOCK = Lock()
MISSING_LLM_KEY_WARNING_PREFIX = "LLM_API_KEY 未配置"


@router.get("/latest", response_model=HotrankLatestResponse)
def get_latest_hotrank() -> HotrankLatestResponse:
    return HotrankLatestResponse(snapshot=_display_snapshot(STORE.load_latest()))


@router.post("/runs", response_model=HotrankRunResponse)
def create_hotrank_run(request: HotrankRunRequest) -> HotrankRunResponse:
    channel_ids = _normalize_channel_ids(request.channel_ids)
    if request.limit < 1 or request.limit > 50:
        raise HTTPException(status_code=400, detail="limit 必须在 1 到 50 之间")

    try:
        fetch_results = _run_hotrank_fetch(channel_ids)
    except CimiDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"热榜拉取失败：{exc}") from exc

    if not any(result.ok for result in fetch_results):
        detail = "；".join(result.error for result in fetch_results if result.error)
        raise HTTPException(status_code=400, detail=detail or "所有热榜渠道拉取失败")

    run_id = _new_run_id()
    category_classifier, classifier_warning = _build_category_classifier()
    snapshot = aggregate_hotrank_results(
        fetch_results,
        run_id=run_id,
        requested_channel_ids=channel_ids,
        limit=request.limit,
        category_classifier=category_classifier,
    )
    if classifier_warning:
        snapshot.warnings.append(classifier_warning)
    STORE.save_snapshot(snapshot, fetch_results)
    return HotrankRunResponse(snapshot=snapshot)


@router.post("/runs/async", response_model=HotrankRunStatus)
def create_hotrank_run_async(
    request: HotrankRunRequest,
    background_tasks: BackgroundTasks,
) -> HotrankRunStatus:
    channel_ids = _normalize_channel_ids(request.channel_ids)
    if request.limit < 1 or request.limit > 50:
        raise HTTPException(status_code=400, detail="limit 必须在 1 到 50 之间")

    run_id = _new_run_id()
    now = _utc_now()
    status = HotrankRunStatus(
        run_id=run_id,
        status="queued",
        message="等待开始刷新热榜",
        progress=0.0,
        channel_ids=channel_ids,
        limit=request.limit,
        created_at=now,
        updated_at=now,
    )
    _store_run_status(status)
    background_tasks.add_task(_run_hotrank_background, run_id, channel_ids, request.limit)
    return status


@router.get("/runs/{run_id}", response_model=HotrankRunStatus)
def get_hotrank_run_status(run_id: str) -> HotrankRunStatus:
    return _load_run_status(run_id)


@router.get("/prompts", response_model=PromptResponse)
def get_hotrank_prompts() -> PromptResponse:
    system_path, user_path = _hotrank_prompt_paths_from_config()
    system_prompt = read_text_file(system_path) or DEFAULT_CLASSIFICATION_SYSTEM_PROMPT
    user_prompt = read_text_file(user_path) or DEFAULT_CLASSIFICATION_USER_PROMPT
    return PromptResponse(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        warnings=validate_hotrank_prompt(system_prompt, user_prompt),
    )


@router.put("/prompts", response_model=PromptResponse)
def save_hotrank_prompts(request: SavePromptRequest) -> PromptResponse:
    system_path, user_path = _hotrank_prompt_paths_from_config()
    warnings = validate_hotrank_prompt(request.system_prompt, request.user_prompt)
    write_text_file_with_backup(system_path, request.system_prompt)
    write_text_file_with_backup(user_path, request.user_prompt)
    return PromptResponse(
        system_prompt=request.system_prompt,
        user_prompt=request.user_prompt,
        warnings=warnings,
    )


def _run_hotrank_fetch(channel_ids: list[int]) -> list[HotrankFetchResult]:
    client = CimiDataHotrankClient()
    return client.fetch_channels(channel_ids)


def _display_snapshot(snapshot: HotrankSnapshot | None) -> HotrankSnapshot | None:
    if snapshot is None or not read_env_value(ENV_PATH, "LLM_API_KEY"):
        return snapshot
    warnings = getattr(snapshot, "warnings", [])
    rewritten_warnings: list[str] = []
    changed = False
    for warning in warnings:
        if str(warning).startswith(MISSING_LLM_KEY_WARNING_PREFIX):
            rewritten_warnings.append(
                "该快照生成时未启用 AI 分类；当前 API Key 已配置，刷新一次即可使用 AI 分类。"
            )
            changed = True
        else:
            rewritten_warnings.append(str(warning))
    if not changed:
        return snapshot
    return snapshot.model_copy(update={"warnings": rewritten_warnings})


def _normalize_channel_ids(channel_ids: list[int] | None) -> list[int]:
    selected = channel_ids or DEFAULT_CHANNEL_IDS
    normalized: list[int] = []
    for channel_id in selected:
        if channel_id not in CHANNEL_NAMES:
            raise HTTPException(status_code=400, detail=f"不支持的热榜渠道：{channel_id}")
        if channel_id not in normalized:
            normalized.append(channel_id)
    if not normalized:
        raise HTTPException(status_code=400, detail="至少选择一个热榜渠道")
    return normalized


def _run_hotrank_background(run_id: str, channel_ids: list[int], limit: int) -> None:
    try:
        _update_run_status(
            run_id,
            status="fetching",
            message="正在拉取各平台热榜",
            progress=0.08,
        )
        try:
            fetch_results = _run_hotrank_fetch(channel_ids)
        except CimiDataError as exc:
            raise RuntimeError(str(exc)) from exc
        except Exception as exc:
            raise RuntimeError(f"热榜拉取失败：{exc}") from exc

        if not any(result.ok for result in fetch_results):
            detail = "；".join(result.error for result in fetch_results if result.error)
            raise RuntimeError(detail or "所有热榜渠道拉取失败")

        classifier_started_at = {"value": 0.0}

        def on_classification_start(total_count: int) -> None:
            classifier_started_at["value"] = time.monotonic()
            _update_run_status(
                run_id,
                status="classifying",
                message=f"正在做 AI 主题分类：0/{total_count}",
                progress=0.35,
                total_topics=total_count,
                classified_topics=0,
                estimated_seconds_remaining=None,
            )

        def on_classification_progress(done_count: int, total_count: int) -> None:
            elapsed_seconds = max(0.0, time.monotonic() - classifier_started_at["value"])
            estimated_seconds_remaining = None
            if done_count > 0 and total_count > done_count:
                estimated_seconds_remaining = (
                    elapsed_seconds / done_count * (total_count - done_count)
                )
            ratio = done_count / total_count if total_count else 1.0
            _update_run_status(
                run_id,
                status="classifying",
                message=f"正在做 AI 主题分类：{done_count}/{total_count}",
                progress=0.35 + 0.55 * ratio,
                total_topics=total_count,
                classified_topics=done_count,
                estimated_seconds_remaining=estimated_seconds_remaining,
            )

        category_classifier, classifier_warning = _build_category_classifier(
            progress_callback=on_classification_progress,
            start_callback=on_classification_start,
        )
        if category_classifier is None:
            _update_run_status(
                run_id,
                status="saving",
                message="AI 分类已跳过，正在保存关键词分类快照",
                progress=0.9,
            )
        snapshot = aggregate_hotrank_results(
            fetch_results,
            run_id=run_id,
            requested_channel_ids=channel_ids,
            limit=limit,
            category_classifier=category_classifier,
        )
        if classifier_warning:
            snapshot.warnings.append(classifier_warning)
        _update_run_status(
            run_id,
            status="saving",
            message="正在保存热榜快照",
            progress=0.95,
            estimated_seconds_remaining=None,
        )
        STORE.save_snapshot(snapshot, fetch_results)
        _update_run_status(
            run_id,
            status="succeeded",
            message="热榜刷新完成",
            progress=1.0,
            snapshot=snapshot,
            warnings=snapshot.warnings,
            estimated_seconds_remaining=0.0,
        )
    except Exception as exc:
        _update_run_status(
            run_id,
            status="failed",
            message="热榜刷新失败",
            progress=1.0,
            error=str(exc),
            estimated_seconds_remaining=None,
        )


def _build_category_classifier(
    progress_callback: Callable[[int, int], None] | None = None,
    start_callback: Callable[[int], None] | None = None,
) -> tuple[CategoryClassifier | None, str]:
    config = load_app_config(CONFIG_PATH)
    classify_config = config.hotrank.ai_classification
    if not classify_config.enabled:
        return None, "AI 主题分类未启用，当前使用关键词分类"

    api_key = read_env_value(ENV_PATH, "LLM_API_KEY")
    if not api_key:
        return None, "LLM_API_KEY 未配置，AI 主题分类已跳过，当前使用关键词分类"

    system_path, user_path = _hotrank_prompt_paths_from_config()
    system_prompt = read_text_file(system_path) or DEFAULT_CLASSIFICATION_SYSTEM_PROMPT
    user_prompt = read_text_file(user_path) or DEFAULT_CLASSIFICATION_USER_PROMPT
    classifier = HotrankAiClassifier(
        HotrankAiClassifierConfig(
            api_key=api_key,
            base_url=classify_config.base_url,
            model=classify_config.model.strip() or "gpt-5.4",
            workers=classify_config.workers,
            timeout_seconds=float(classify_config.timeout_seconds),
            max_retries=int(classify_config.max_retries),
            max_completion_tokens=classify_config.max_completion_tokens,
            reasoning_effort=classify_config.reasoning_effort.strip(),
            system_prompt=system_prompt,
            user_prompt_template=user_prompt,
        )
    )

    def classify_with_progress(topics: list[HotrankTrendTopic]) -> dict[str, str]:
        if start_callback is not None:
            start_callback(len(topics))
        return classifier.classify_topics(topics, progress_callback=progress_callback)

    return classify_with_progress, ""


def _hotrank_prompt_paths_from_config() -> tuple[Path, Path]:
    config = load_app_config(CONFIG_PATH)
    prompt_config = config.hotrank.ai_classification.prompt
    return (
        config.resolve_path(prompt_config.system_path),
        config.resolve_path(prompt_config.user_path),
    )


def _store_run_status(status: HotrankRunStatus) -> None:
    with ASYNC_RUNS_LOCK:
        ASYNC_RUNS[status.run_id] = status


def _load_run_status(run_id: str) -> HotrankRunStatus:
    with ASYNC_RUNS_LOCK:
        status = ASYNC_RUNS.get(run_id)
    if status is None:
        raise HTTPException(status_code=404, detail="热榜任务不存在")
    return status


def _update_run_status(run_id: str, **updates: object) -> HotrankRunStatus:
    with ASYNC_RUNS_LOCK:
        current = ASYNC_RUNS.get(run_id)
        if current is None:
            raise RuntimeError(f"热榜任务不存在: {run_id}")
        sanitized_updates = dict(updates)
        if "progress" in sanitized_updates:
            progress = float(sanitized_updates["progress"])
            sanitized_updates["progress"] = max(0.0, min(1.0, progress))
        sanitized_updates["updated_at"] = _utc_now()
        next_status = current.model_copy(update=sanitized_updates)
        ASYNC_RUNS[run_id] = next_status
        return next_status


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new_run_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:8]
