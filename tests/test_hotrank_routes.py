from fastapi.testclient import TestClient

import web.backend.hotrank_routes as route_module
from web.backend.app import app
from web.backend.hotrank_models import HotrankChannelItem, HotrankFetchResult
from web.backend.hotrank_store import HotrankStore


def _fake_fetch(channel_ids: list[int]) -> list[HotrankFetchResult]:
    names = {1: "微博", 3: "百度"}
    return [
        HotrankFetchResult(
            channel_id=channel_id,
            channel_name=names[channel_id],
            ok=True,
            items=[
                HotrankChannelItem(
                    channel_id=channel_id,
                    channel_name=names[channel_id],
                    rank=1,
                    title="普京结束访华" if channel_id == 1 else "普京结束对中国的国事访问",
                    hot="100万",
                    created_at="2026-05-21T10:00:00+00:00",
                )
            ],
        )
        for channel_id in channel_ids
    ]


def test_latest_hotrank_does_not_trigger_fetch(tmp_path, monkeypatch):
    monkeypatch.setattr(route_module, "STORE", HotrankStore(tmp_path / "hotrank"))
    monkeypatch.setattr(
        route_module,
        "_run_hotrank_fetch",
        lambda channel_ids: (_ for _ in ()).throw(AssertionError("fetch should not run")),
    )
    client = TestClient(app)

    response = client.get("/api/hotrank/latest")

    assert response.status_code == 200
    assert response.json() == {"snapshot": None}


def test_create_hotrank_run_saves_snapshot(tmp_path, monkeypatch):
    store = HotrankStore(tmp_path / "hotrank")
    monkeypatch.setattr(route_module, "STORE", store)
    monkeypatch.setattr(route_module, "_run_hotrank_fetch", _fake_fetch)
    monkeypatch.setattr(route_module, "_build_category_classifier", lambda: (None, ""))
    client = TestClient(app)

    response = client.post("/api/hotrank/runs", json={"channel_ids": [1, 3], "limit": 10})

    assert response.status_code == 200
    body = response.json()
    assert body["snapshot"]["channels_succeeded"] == [1, 3]
    assert body["snapshot"]["top_trends"][0]["platform_count"] == 2
    assert store.load_latest() is not None


def test_create_hotrank_run_rejects_unknown_channel(tmp_path, monkeypatch):
    monkeypatch.setattr(route_module, "STORE", HotrankStore(tmp_path / "hotrank"))
    client = TestClient(app)

    response = client.post("/api/hotrank/runs", json={"channel_ids": [999]})

    assert response.status_code == 400
    assert "不支持" in response.json()["detail"]
