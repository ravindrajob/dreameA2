"""Smoke and security guardrail tests for Dreame A2 Cockpit."""

import shutil
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_DIR / "backend"))

import main as api_main  # noqa: E402

client = TestClient(api_main.app)


def test_health_and_demo_status(monkeypatch):
    monkeypatch.delenv("HA_TOKEN", raising=False)
    api_main.client.ha_token = ""

    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json() == {"status": "ok"}

    r_status = client.get("/api/status")
    assert r_status.status_code == 200
    body = r_status.json()
    assert body["is_demo"] is True
    assert body["robot"]["battery"] == 100
    assert body["environment"]["rain_sensor_active"] is False


def test_synthetic_pointcloud_endpoint_and_header():
    r = client.get("/api/pointcloud")
    assert r.status_code == 200
    lines = r.text.splitlines()
    assert lines[0].startswith("# .PCD v0.7")
    assert "POINTS 15000" in lines[:12]
    data_idx = lines.index("DATA ascii")
    assert len(lines) - (data_idx + 1) == 15000


def test_action_fail_closed_and_bearer_auth(monkeypatch):
    # Live HA_TOKEN without API_AUTH_TOKEN must fail closed (503)
    monkeypatch.setenv("HA_TOKEN", "dummy-live-ha-token")
    monkeypatch.delenv("API_AUTH_TOKEN", raising=False)
    r = client.post("/api/action", json={"action": "start"})
    assert r.status_code == 503

    # Invalid action rejected before dispatch (400)
    r_bad = client.post("/api/action", json={"action": "rm_rf"})
    assert r_bad.status_code == 400

    # Wrong or missing Bearer token rejected (401)
    monkeypatch.setenv("API_AUTH_TOKEN", "test-secret-token")
    r_unauth = client.post("/api/action", json={"action": "pause"})
    assert r_unauth.status_code == 401
    r_wrong = client.post(
        "/api/action",
        json={"action": "pause"},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert r_wrong.status_code == 401

    # Valid token in demo mode succeeds (200)
    monkeypatch.delenv("HA_TOKEN", raising=False)
    api_main.client.ha_token = ""
    r_ok = client.post(
        "/api/action",
        json={"action": "dock"},
        headers={"Authorization": "Bearer test-secret-token"},
    )
    assert r_ok.status_code == 200
    assert r_ok.json() == {"status": "ok", "action": "dock", "success": True}


def test_verify_zero_pii_script_passes_clean_and_catches_rfc1918(tmp_path):
    script = REPO_DIR / "scripts/verify_zero_pii.sh"
    res_clean = subprocess.run(["bash", str(script)], capture_output=True, text=True)
    assert res_clean.returncode == 0, res_clean.stdout + res_clean.stderr

    # Negative test on an isolated copy containing a synthetic private IPv4 leak
    sandbox = tmp_path / "repo_copy"
    (sandbox / "scripts").mkdir(parents=True)
    shutil.copy2(script, sandbox / "scripts/verify_zero_pii.sh")
    synthetic_private_ip = ".".join(["10", "254", "99", "50"])
    (sandbox / "leaked_config.txt").write_text(
        f"HA_URL=http://{synthetic_private_ip}:8123\n",
        encoding="utf-8",
    )

    res_leak = subprocess.run(
        ["bash", str(sandbox / "scripts/verify_zero_pii.sh")],
        capture_output=True,
        text=True,
    )
    assert res_leak.returncode != 0
    assert "PRIVATE-IP" in res_leak.stdout
