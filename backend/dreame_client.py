"""
Home Assistant Client for Dreame Robotic Mower A2.
Handles dynamic entry_id resolution, entity querying, and command dispatching.
"""

import os
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger("dreame_client")
logging.basicConfig(level=logging.INFO)

class DreameHAClient:
    def __init__(self, ha_url: Optional[str] = None, ha_token: Optional[str] = None):
        self.ha_url = (ha_url or os.getenv("HA_URL", "http://192.0.2.100:8123")).rstrip("/")
        self.ha_token = ha_token or os.getenv("HA_TOKEN", "")
        self.mower_entity = os.getenv("MOWER_ENTITY_ID", "lawn_mower.a2")
        self.cached_entry_id: Optional[str] = None

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.ha_token}",
            "Content-Type": "application/json"
        }

    async def get_states(self) -> Optional[list]:
        """Fetch all states from Home Assistant API."""
        if not self.ha_token:
            return None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.ha_url}/api/states", headers=self.headers)
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.warning(f"Could not reach Home Assistant at {self.ha_url}: {e}")
        return None

    async def resolve_entry_id(self) -> Optional[str]:
        """Dynamically find the config entry ID for dreame_lawn_mower domain."""
        if self.cached_entry_id:
            return self.cached_entry_id
        if not self.ha_token:
            return None

        url = f"{self.ha_url}/api/config/config_entries/entry"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code == 200:
                    entries = resp.json()
                    for entry in entries:
                        if entry.get("domain") in ("dreame_lawn_mower", "dreame_mower"):
                            self.cached_entry_id = entry.get("entry_id")
                            logger.info(f"Discovered Dreame entry_id: {self.cached_entry_id}")
                            return self.cached_entry_id
        except Exception as e:
            logger.warning(f"Dynamic entry_id resolution failed: {e}")
        return None

    async def get_mower_telemetry(self) -> Dict[str, Any]:
        """Extract clean telemetry without hardcoded assumptions."""
        states = await self.get_states()
        if not states:
            return self.get_demo_telemetry()

        mower_state = None
        rain_sensor_state = None
        blade_life = None
        session_area = None
        map_area = None

        for s in states:
            eid = s.get("entity_id", "")
            if eid == self.mower_entity:
                mower_state = s
            elif "rain_sensor" in eid and eid.startswith("binary_sensor."):
                rain_sensor_state = s.get("state")
            elif "blade_life" in eid:
                try:
                    blade_life = float(s.get("state"))
                except (ValueError, TypeError):
                    pass
            elif "current_mowed_area" in eid or "mowing_area" in eid:
                try:
                    session_area = float(s.get("state"))
                except (ValueError, TypeError):
                    pass
            elif "map_area" in eid:
                try:
                    map_area = float(s.get("state"))
                except (ValueError, TypeError):
                    pass

        attrs = mower_state.get("attributes", {}) if mower_state else {}
        state_str = mower_state.get("state", "unknown") if mower_state else "unknown"

        # Determine rain status label factually
        if rain_sensor_state in ("on", "rain", "true"):
            rain_label = "🌧️ Rain Detected"
            rain_active = True
        elif rain_sensor_state in ("off", "dry", "false"):
            rain_label = "☀️ Dry Weather"
            rain_active = False
        else:
            rain_label = "❔ Sensor Unavailable"
            rain_active = None

        return {
            "robot": {
                "name": attrs.get("friendly_name", "Dreame A2"),
                "state": state_str,
                "battery": attrs.get("battery_level", attrs.get("battery", 100)),
                "blade_life_pct": blade_life if blade_life is not None else attrs.get("blade_life", 100),
                "mowing_area_m2": session_area,
                "map_total_area_m2": map_area or attrs.get("map_area"),
            },
            "environment": {
                "rain_sensor_active": rain_active,
                "rain_status_label": rain_label,
            },
            "is_demo": False
        }

    def get_demo_telemetry(self) -> Dict[str, Any]:
        """Return synthetic demo telemetry when HA is disconnected."""
        return {
            "robot": {
                "name": "Dreame Roboticmower A2 (Demo)",
                "state": "docked",
                "battery": 100,
                "blade_life_pct": 85,
                "mowing_area_m2": None, # None when not active (docked)
                "map_total_area_m2": 300.0, # 20m x 15m synthetic demo garden
            },
            "environment": {
                "rain_sensor_active": False,
                "rain_status_label": "☀️ Dry Weather (Demo)",
            },
            "is_demo": True
        }

    async def send_command(self, action: str) -> bool:
        """Send mowing action to Home Assistant."""
        if not self.ha_token:
            logger.info(f"Demo command executed: {action}")
            return True

        action_service_map = {
            "start": ("lawn_mower", "start_mowing"),
            "pause": ("lawn_mower", "pause"),
            "dock": ("lawn_mower", "dock"),
            "stop": ("lawn_mower", "pause"),
        }

        if action not in action_service_map:
            raise ValueError(f"Action '{action}' is not allowed.")

        domain, service = action_service_map[action]
        url = f"{self.ha_url}/api/services/{domain}/{service}"
        payload = {"entity_id": self.mower_entity}

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=self.headers, json=payload)
            return resp.status_code in (200, 201)
