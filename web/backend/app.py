from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from config.app_config import load_app_config
from web.backend.config_service import (
    ConfigWriteError,
    read_text_file,
    read_yaml_config,
    validate_scoring_prompt,
    write_text_file_with_backup,
    write_validated_config,
)
from web.backend.env_service import mask_secret, read_env_value, write_env_value
from web.backend.job_runner import run_web_job
from web.backend.job_store import JobStore
from web.backend.models import (
    ConfigResponse,
    JobCreateRequest,
    JobSnapshot,
    PromptResponse,
    SaveConfigRequest,
    SavePromptRequest,
    SystemStatus,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
ENV_PATH = PROJECT_ROOT / ".env"
JOBS_ROOT = PROJECT_ROOT / "web_jobs"
FRONTEND_DIST = PROJECT_ROOT / "web" / "frontend" / "dist"
ACTIVE_JOB_STATUSES = {"queued", "running"}
ACTIVE_JOB_STALE_SECONDS = 24 * 60 * 60

app = FastAPI(title="AITrend Web Dashboard", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

job_store = JobStore(JOBS_ROOT)


def _http_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


def _is_recent_active_job(snapshot: JobSnapshot) -> bool:
    if snapshot.status not in ACTIVE_JOB_STATUSES:
        return False
    try:
        updated_at = datetime.fromisoformat(snapshot.updated_at)
    except ValueError:
        return True
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - updated_at).total_seconds()
    return age_seconds <= ACTIVE_JOB_STALE_SECONDS


def _active_job_snapshot() -> JobSnapshot | None:
    for snapshot in job_store.list_jobs(limit=20):
        if _is_recent_active_job(snapshot):
            return snapshot
    return None


def _ensure_no_active_job(action_name: str) -> None:
    active_job = _active_job_snapshot()
    if active_job is None:
        return
    raise HTTPException(
        status_code=409,
        detail=f"任务 {active_job.job_id} 正在运行中，暂不能{action_name}",
    )


def _prompt_paths_from_config() -> tuple[Path, Path]:
    config = load_app_config(CONFIG_PATH)
    return (
        config.resolve_path(config.scoring.prompt.system_path),
        config.resolve_path(config.scoring.prompt.user_path),
    )


@app.get("/api/config", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    api_key = read_env_value(ENV_PATH, "LLM_API_KEY")
    return ConfigResponse(
        config=read_yaml_config(CONFIG_PATH),
        masked_api_key=mask_secret(api_key),
        has_api_key=bool(api_key),
    )


@app.put("/api/config", response_model=ConfigResponse)
def save_config(request: SaveConfigRequest) -> ConfigResponse:
    _ensure_no_active_job("保存配置")
    try:
        write_validated_config(CONFIG_PATH, request.config)
        if request.api_key is not None:
            write_env_value(ENV_PATH, "LLM_API_KEY", request.api_key.strip())
    except ConfigWriteError as exc:
        raise _http_error(exc) from exc
    api_key = read_env_value(ENV_PATH, "LLM_API_KEY")
    return ConfigResponse(
        config=read_yaml_config(CONFIG_PATH),
        masked_api_key=mask_secret(api_key),
        has_api_key=bool(api_key),
    )


@app.get("/api/prompts", response_model=PromptResponse)
def get_prompts() -> PromptResponse:
    system_path, user_path = _prompt_paths_from_config()
    system_prompt = read_text_file(system_path)
    user_prompt = read_text_file(user_path)
    return PromptResponse(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        warnings=validate_scoring_prompt(system_prompt, user_prompt),
    )


@app.put("/api/prompts", response_model=PromptResponse)
def save_prompts(request: SavePromptRequest) -> PromptResponse:
    _ensure_no_active_job("保存 Prompt")
    system_path, user_path = _prompt_paths_from_config()
    warnings = validate_scoring_prompt(request.system_prompt, request.user_prompt)
    write_text_file_with_backup(system_path, request.system_prompt)
    write_text_file_with_backup(user_path, request.user_prompt)
    return PromptResponse(
        system_prompt=request.system_prompt,
        user_prompt=request.user_prompt,
        warnings=warnings,
    )


@app.post("/api/scoring/test")
def test_scoring_connection() -> dict[str, Any]:
    api_key = read_env_value(ENV_PATH, "LLM_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="LLM_API_KEY 未配置")
    config = load_app_config(CONFIG_PATH)
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=config.scoring.base_url,
            timeout=min(30.0, float(config.scoring.timeout_seconds)),
            max_retries=0,
        )
        models = client.models.list()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"连接失败：{exc}") from exc
    return {
        "ok": True,
        "model": config.scoring.model,
        "available_count": len(getattr(models, "data", []) or []),
    }


@app.post("/api/jobs")
def create_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    _ensure_no_active_job("启动新任务")
    snapshot = job_store.create_job(
        run_mode=request.run_mode,
        execution_mode=request.execution_mode,
    )
    background_tasks.add_task(run_web_job, job_store, snapshot, CONFIG_PATH)
    return snapshot.model_dump()


@app.get("/api/jobs")
def list_jobs(limit: int = 50) -> list[dict[str, Any]]:
    return [snapshot.model_dump() for snapshot in job_store.list_jobs(limit=limit)]


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    try:
        return job_store.load_job(job_id).model_dump()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="任务不存在") from exc


@app.get("/api/jobs/{job_id}/events")
def get_job_events(job_id: str, start: int = 0) -> list[dict[str, Any]]:
    return [event.model_dump() for event in job_store.read_events(job_id, start=start)]


@app.get("/api/jobs/{job_id}/stream")
def stream_job_events(job_id: str):
    def event_stream():
        cursor = 0
        while True:
            events = job_store.read_events(job_id, start=cursor)
            for event in events:
                cursor += 1
                yield "data: " + json.dumps(event.model_dump(), ensure_ascii=False) + "\n\n"
            snapshot = job_store.load_job(job_id)
            if snapshot.status in {"succeeded", "failed", "cancelled"} and not events:
                yield "event: done\ndata: " + snapshot.model_dump_json() + "\n\n"
                break
            time.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/reports")
def list_reports() -> list[dict[str, Any]]:
    report_files: list[Path] = []
    report_files.extend((PROJECT_ROOT / "output").glob("*.md"))
    report_files.extend(JOBS_ROOT.glob("*/output/*.md"))
    reports = []
    for path in sorted(report_files, key=lambda item: item.stat().st_mtime, reverse=True):
        reports.append(
            {
                "name": path.name,
                "path": str(path),
                "size": path.stat().st_size,
                "updated_at": path.stat().st_mtime,
            }
        )
    return reports


@app.get("/api/system", response_model=SystemStatus)
def get_system_status() -> SystemStatus:
    config = load_app_config(CONFIG_PATH)
    return SystemStatus(
        project_root=str(PROJECT_ROOT),
        config_path=str(CONFIG_PATH),
        env_path=str(ENV_PATH),
        jobs_root=str(JOBS_ROOT),
        has_api_key=bool(read_env_value(ENV_PATH, "LLM_API_KEY")),
        enabled_sources=config.enabled_sources,
    )


if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
