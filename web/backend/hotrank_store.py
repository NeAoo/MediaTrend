from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from web.backend.hotrank_models import HotrankFetchResult, HotrankSnapshot


class HotrankStore:
    def __init__(self, root: Path):
        self.root = root
        self.runs_root = root / "runs"
        self.latest_path = root / "latest.json"
        self._lock = Lock()
        self.runs_root.mkdir(parents=True, exist_ok=True)

    def run_dir(self, run_id: str) -> Path:
        assert run_id.strip(), "run_id must not be empty"
        return self.runs_root / run_id

    def save_snapshot(
        self,
        snapshot: HotrankSnapshot,
        fetch_results: list[HotrankFetchResult],
    ) -> HotrankSnapshot:
        with self._lock:
            run_dir = self.run_dir(snapshot.run_id)
            run_dir.mkdir(parents=True, exist_ok=False)
            self._write_json(
                run_dir / "raw.json",
                [result.model_dump(mode="json") for result in fetch_results],
            )
            snapshot_data = snapshot.model_dump(mode="json")
            self._write_json(run_dir / "trends.json", snapshot_data)
            self._write_json(self.latest_path, snapshot_data)
        return snapshot

    def load_latest(self) -> HotrankSnapshot | None:
        if not self.latest_path.exists():
            return None
        return HotrankSnapshot.model_validate_json(self.latest_path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, data) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(path.suffix + ".tmp")
        temporary_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)
