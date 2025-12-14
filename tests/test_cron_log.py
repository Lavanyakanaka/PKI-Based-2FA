import os
from fastapi.testclient import TestClient
from app.server import app


def test_cron_log_endpoint(tmp_path, monkeypatch):
    p = tmp_path / "last_code.txt"
    p.write_text("line1\n2025-01-01 00:00:00 - 2FA Code: 123456\n")
    monkeypatch.setenv("CRON_LOG_PATH", str(p))
    client = TestClient(app)
    r = client.get("/cron-log")
    assert r.status_code == 200
    data = r.json()
    assert "last" in data
    assert data["last"].startswith("2025-01-01")
