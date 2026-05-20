import json
from pathlib import Path

from web.backend.job_store import JobStore


def test_job_store_writes_status_and_events(tmp_path: Path):
    store = JobStore(tmp_path)
    snapshot = store.create_job(run_mode="collect_only", execution_mode="serial")

    store.append_event(snapshot.job_id, type="source_started", message="start", source="aihot")
    loaded = store.load_job(snapshot.job_id)

    assert loaded.events_count == 1
    assert (tmp_path / snapshot.job_id / "status.json").exists()
    event_lines = (tmp_path / snapshot.job_id / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(event_lines[0])["source"] == "aihot"
