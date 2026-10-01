from __future__ import annotations

import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def test_upload_job_generates_excel_report(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("REPORT_DIR", str(tmp_path / "reports"))
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")

    for module_name in ("src.api", "src.jobs", "src.models", "src.database"):
        sys.modules.pop(module_name, None)
    api = importlib.import_module("src.api")
    data_dir = Path(__file__).parents[1] / "data"

    with TestClient(api.app) as client:
        with (data_dir / "live_sessions.csv").open("rb") as sessions, (data_dir / "inventory.csv").open("rb") as inventory:
            response = client.post(
                "/api/jobs",
                files={
                    "sessions": ("sessions.csv", sessions, "text/csv"),
                    "inventory": ("inventory.csv", inventory, "text/csv"),
                },
            )
        assert response.status_code == 202
        job = response.json()
        assert job["status"] in {"PENDING", "SUCCEEDED"}

        status = client.get(f"/api/jobs/{job['id']}")
        assert status.status_code == 200
        assert status.json()["status"] == "SUCCEEDED"

        report = client.get(f"/api/jobs/{job['id']}/report")
        assert report.status_code == 200
        assert report.content.startswith(b"PK")
