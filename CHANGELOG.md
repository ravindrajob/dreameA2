# Changelog

All notable changes and field fixes made while building and hardening the Dreame A2 cockpit.

## v1.1.0 - Offline WebGL, Docker Bind Fix & Smoke Test Suite
- **Fixed Three.js r160 404 regression:** Replaced legacy `unpkg.com/.../examples/js/controls/OrbitControls.js` script tags (removed upstream in Three.js r160) with locally vendorized `three.module.min.js` + `OrbitControls.js` (`0.160.0`) loaded via `<script type="importmap">`. Eliminates runtime CDN dependency and works 100% offline inside Home Assistant Lovelace iframes.
- **Fixed Docker reachability while keeping loopback default:** `backend/main.py` now reads `HOST` defaulting to `127.0.0.1` (safe standalone), while `Dockerfile` injects `ENV HOST=0.0.0.0` so `docker-compose.yml` (`127.0.0.1:8000:8000`) routes cleanly.
- **Hardened `scripts/verify_zero_pii.sh`:** Added active RFC 1918 private IPv4 detection (allowing RFC 5737 `192.0.2.x` documentation examples) and user home directory path checks.
- **Added `GET /health` & `tests/test_api.py`:** Automated tests covering synthetic `.pcd` integrity, demo telemetry fallback, fail-closed `503`/`401`/`400` command auth guards, and positive/negative PII scanner checks.
- **Code cleanup:** Removed unused `sys`/`Request` imports, unused `resolve_entry_id()`, and import-time `logging.basicConfig()`.

## v1.0.0 - Zero-PII Standalone Cockpit & Rain-Sensor Decoupling
- Decoupled physical rain sensor status (`RAIN_SENSOR_ENTITY_ID` or auto-detected `binary_sensor.*rain_sensor*`) from mower state so Home Assistant dashboards display real weather lockout state alongside battery, blade wear, and session area.
- Added fail-closed `API_AUTH_TOKEN` Bearer verification (`hmac.compare_digest`) + explicit `CORS_ALLOWED_ORIGINS` allowlist on `POST /api/action`.
- Built `scripts/generate_synthetic_pcd.py` (15,000-point procedural lawn/terrace/trees `.pcd`) so the viewer can be tested and published without exposing real LiDAR house contours.
- Hardened container defaults: non-root `appuser`, `cap_drop: [ALL]`, `no-new-privileges:true`, 256M memory cap.
