# Dreame A2 — 3D LiDAR WebGL Cockpit & Home Assistant Bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-brightgreen.svg)](https://www.python.org/)
[![Three.js WebGL](https://img.shields.io/badge/Three.js-WebGL-black.svg)](https://threejs.org/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Compatible-41BDF5.svg)](https://www.home-assistant.io/)

Interactive **3D LiDAR `.pcd` point-cloud viewer** (Three.js) and decoupled **FastAPI telemetry bridge** for the **Dreame Roboticmower A2** (OmniSense 2.0) and Home Assistant.

- **French version:** [`README.fr.md`](README.fr.md) · **Full technical write-up:** [blog.ravindra-job.fr](https://blog.ravindra-job.fr/iot/dreame-a2-lidar-3d-pcd-passerelle-zero-trust-meteo-pluie/)

![Dreame A2 3D LiDAR Cockpit Preview](assets/preview.webp)

## What It Does

- **3D Point Cloud Viewer:** Renders `.pcd` LiDAR maps in WebGL with OrbitControls, elevation heatmap, and live mower position.
- **Live Telemetry HUD:** Battery, mowed area, blade wear, and physical rain sensor status via Home Assistant REST API.
- **Authenticated Controls:** Start, Pause, and Return to Dock gated by `Authorization: Bearer` token + explicit CORS allowlist.
- **Zero-PII Demo Mode:** Runs out-of-the-box with a synthetic procedural garden (`scripts/generate_synthetic_pcd.py`), no mower required.

```text
Home Assistant (dreame_lawn_mower) ──REST──▶ FastAPI Backend (:8000) ──HTTP──▶ Three.js 3D Cockpit / Lovelace iframe
```

## Quick Start (Docker)

```bash
git clone https://github.com/ravindrajob/dreameA2.git
cd dreameA2
cp .env.example .env   # set HA_URL, HA_TOKEN, API_AUTH_TOKEN (optional for demo mode)
docker compose up -d
# Open http://127.0.0.1:8000
```

## Standalone Python

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
python3 backend/main.py
```

## Home Assistant Lovelace Card

```yaml
type: iframe
title: Dreame A2 3D Cockpit
url: http://YOUR_SERVER_IP:8000/
aspect_ratio: 16x9
```

Full stack example: [`lovelace/dreame_a2_card.yaml`](lovelace/dreame_a2_card.yaml).

## Security & Privacy

- Non-root container (`appuser`), `cap_drop: [ALL]`, `no-new-privileges:true`, bound to `127.0.0.1:8000`.
- Zero personal geometry committed — run `./scripts/verify_zero_pii.sh` before sharing custom builds.

## Credits & License

- Compatible with [okolbu/ha-dreame-a2-mower](https://github.com/okolbu/ha-dreame-a2-mower).
- Licensed under [MIT](LICENSE) — **Ravindra JOB**.
