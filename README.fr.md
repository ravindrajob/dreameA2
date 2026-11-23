# Dreame A2 — Cockpit 3D LiDAR WebGL & Passerelle Home Assistant

[![Licence: MIT](https://img.shields.io/badge/Licence-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-brightgreen.svg)](https://www.python.org/)
[![Three.js WebGL](https://img.shields.io/badge/Three.js-WebGL-black.svg)](https://threejs.org/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Compatible-41BDF5.svg)](https://www.home-assistant.io/)

Visualiseur **3D LiDAR `.pcd` interactif** (Three.js) et passerelle **FastAPI** découplée pour le robot tondeuse **Dreame Roboticmower A2** (OmniSense 2.0) sous Home Assistant.

- **English version:** [`README.md`](README.md) · **Article complet :** [blog.ravindra-job.fr](https://blog.ravindra-job.fr/iot/dreame-a2-lidar-3d-pcd-passerelle-zero-trust-meteo-pluie/)

![Aperçu Cockpit 3D LiDAR Dreame A2](assets/preview.webp)

## Fonctionnalités

- **Nuage de points 3D :** Rendu `.pcd` WebGL (OrbitControls, palette d'altitude hypsométrique, marqueur position robot).
- **HUD temps réel :** Batterie, surface tondue, usure des lames et état capteur de pluie via API REST Home Assistant.
- **Commandes sécurisées :** Tonte, Pause, Retour station protégés par jeton `Bearer` + liste blanche CORS.
- **Mode Démo Zero-PII :** Fonctionne sans tondeuse grâce au générateur de jardin synthétique (`scripts/generate_synthetic_pcd.py`).

## Démarrage Rapide (Docker)

```bash
git clone https://github.com/ravindrajob/dreameA2.git
cd dreameA2
cp .env.example .env   # HA_URL, HA_TOKEN, API_AUTH_TOKEN (optionnel en mode démo)
docker compose up -d
# http://127.0.0.1:8000
```

## Carte Lovelace Home Assistant

```yaml
type: iframe
title: Cockpit 3D Dreame A2
url: http://IP_DE_VOTRE_SERVEUR:8000/
aspect_ratio: 16x9
```

Exemple complet : [`lovelace/dreame_a2_card.yaml`](lovelace/dreame_a2_card.yaml).

## Sécurité & Licence

- Conteneur non-root (`appuser`), `cap_drop: [ALL]`, `no-new-privileges:true`, bind `127.0.0.1:8000`.
- Compatible avec [okolbu/ha-dreame-a2-mower](https://github.com/okolbu/ha-dreame-a2-mower) · Licence [MIT](LICENSE) — **Ravindra JOB**.
