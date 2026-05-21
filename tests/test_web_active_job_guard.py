from fastapi.testclient import TestClient

import web.backend.app as app_module
from web.backend.job_store import JobStore


def test_create_job_rejects_when_another_job_is_active(tmp_path, monkeypatch):
    test_store = JobStore(tmp_path / "jobs")
    active_job = test_store.create_job(
        run_mode="collect_only",
        execution_mode="parallel",
    )
    monkeypatch.setattr(app_module, "job_store", test_store)
    client = TestClient(app_module.app)

    response = client.post(
        "/api/jobs",
        json={"run_mode": "collect_only", "execution_mode": "serial"},
    )

    assert response.status_code == 409
    assert active_job.job_id in response.json()["detail"]


def test_save_config_rejects_when_job_is_active(tmp_path, monkeypatch):
    test_store = JobStore(tmp_path / "jobs")
    test_store.create_job(run_mode="collect_only", execution_mode="parallel")
    monkeypatch.setattr(app_module, "job_store", test_store)
    client = TestClient(app_module.app)

    response = client.put("/api/config", json={"config": {}, "api_key": None})

    assert response.status_code == 409
    assert "保存配置" in response.json()["detail"]


def test_cancel_job_marks_active_job_as_cancel_requested(tmp_path, monkeypatch):
    test_store = JobStore(tmp_path / "jobs")
    active_job = test_store.create_job(
        run_mode="collect_only",
        execution_mode="parallel",
    )
    monkeypatch.setattr(app_module, "job_store", test_store)
    client = TestClient(app_module.app)

    response = client.post(f"/api/jobs/{active_job.job_id}/cancel")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"
    assert body["cancel_requested"] is True
    events = test_store.read_events(active_job.job_id)
    assert events[0].type == "cancel_requested"
