from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from web.backend.models import ExecutionMode, JobEvent, JobSnapshot, RunMode


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class JobStore:
    def __init__(self, root: Path):
        self.root = root
        self._lock = Lock()
        self.root.mkdir(parents=True, exist_ok=True)

    def create_job(self, run_mode: RunMode, execution_mode: ExecutionMode) -> JobSnapshot:
        job_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:8]
        now = utc_now_iso()
        snapshot = JobSnapshot(
            job_id=job_id,
            status="queued",
            run_mode=run_mode,
            execution_mode=execution_mode,
            created_at=now,
            updated_at=now,
        )
        self.job_dir(job_id).mkdir(parents=True, exist_ok=False)
        self.save_job(snapshot)
        return snapshot

    def job_dir(self, job_id: str) -> Path:
        return self.root / job_id

    def save_job(self, snapshot: JobSnapshot) -> None:
        path = self.job_dir(snapshot.job_id) / "status.json"
        path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")

    def load_job(self, job_id: str) -> JobSnapshot:
        path = self.job_dir(job_id) / "status.json"
        return JobSnapshot.model_validate_json(path.read_text(encoding="utf-8"))

    def list_jobs(self, limit: int = 50) -> list[JobSnapshot]:
        snapshots: list[JobSnapshot] = []
        for status_path in sorted(self.root.glob("*/status.json"), reverse=True):
            try:
                snapshots.append(JobSnapshot.model_validate_json(status_path.read_text(encoding="utf-8")))
            except Exception:
                continue
            if len(snapshots) >= limit:
                break
        return snapshots

    def update_job(self, snapshot: JobSnapshot, **changes) -> JobSnapshot:
        updated = snapshot.model_copy(update={**changes, "updated_at": utc_now_iso()})
        self.save_job(updated)
        return updated

    def is_cancel_requested(self, job_id: str) -> bool:
        return self.load_job(job_id).cancel_requested

    def request_cancel(self, job_id: str) -> JobSnapshot:
        snapshot = self.load_job(job_id)
        if snapshot.status in {"succeeded", "failed", "cancelled"}:
            return snapshot
        return self.update_job(snapshot, cancel_requested=True)

    def append_event(self, job_id: str, **event_fields) -> JobEvent:
        event = JobEvent(job_id=job_id, created_at=utc_now_iso(), **event_fields)
        event_path = self.job_dir(job_id) / "events.jsonl"
        with self._lock:
            with event_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event.model_dump(), ensure_ascii=False) + "\n")
            snapshot = self.load_job(job_id)
            self.save_job(
                snapshot.model_copy(
                    update={
                        "events_count": snapshot.events_count + 1,
                        "updated_at": utc_now_iso(),
                    }
                )
            )
        return event

    def read_events(self, job_id: str, start: int = 0) -> list[JobEvent]:
        event_path = self.job_dir(job_id) / "events.jsonl"
        if not event_path.exists():
            return []
        events: list[JobEvent] = []
        for index, line in enumerate(event_path.read_text(encoding="utf-8").splitlines()):
            if index < start or not line.strip():
                continue
            events.append(JobEvent.model_validate_json(line))
        return events

    def save_artifacts(self, job_id: str, artifacts: dict) -> None:
        path = self.job_dir(job_id) / "artifacts.json"
        path.write_text(json.dumps(artifacts, ensure_ascii=False, indent=2), encoding="utf-8")
        snapshot = self.load_job(job_id)
        self.save_job(snapshot.model_copy(update={"artifacts": artifacts, "updated_at": utc_now_iso()}))
