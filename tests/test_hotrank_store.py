from pathlib import Path

from web.backend.hotrank_models import HotrankSnapshot
from web.backend.hotrank_store import HotrankStore


def test_hotrank_store_writes_run_and_latest(tmp_path: Path):
    store = HotrankStore(tmp_path)
    snapshot = HotrankSnapshot(
        run_id="20260521-100000-test",
        created_at="2026-05-21T10:00:00+00:00",
        channels_requested=[1, 3],
        channels_succeeded=[1, 3],
        channels_failed=[],
        raw_item_count=0,
        top_trends=[],
        category_counts={},
    )

    store.save_snapshot(snapshot, [])
    loaded = store.load_latest()

    assert loaded is not None
    assert loaded.run_id == snapshot.run_id
    assert (tmp_path / "runs" / snapshot.run_id / "raw.json").exists()
    assert (tmp_path / "runs" / snapshot.run_id / "trends.json").exists()
    assert (tmp_path / "latest.json").exists()
