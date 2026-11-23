"""
Dreame Robotic Mower A2 - Standalone 3D Cockpit & API Backend.
Community open-source package.
"""

import hmac
import logging
import os
import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from fastapi.middleware.cors import CORSMiddleware
from dreame_client import DreameHAClient

logger = logging.getLogger("dreame_a2_api")

app = FastAPI(
    title="Dreame A2 LiDAR Cockpit API",
    description="Community 3D WebGL viewer and telemetry bridge for Dreame Roboticmower A2",
    version="1.0.0"
)

_allowed_origins = [
    o.strip()
    for o in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

security = HTTPBearer(auto_error=False)
client = DreameHAClient()

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
ASSETS_DIR = WEB_DIR / "assets"

class ActionRequest(BaseModel):
    action: str = Field(..., description="Action to perform: start, pause, dock, stop")

@app.get("/api/status")
async def get_status():
    """Retrieve current mower status and environment data."""
    data = await client.get_mower_telemetry()
    return JSONResponse(data)

@app.get("/api/pointcloud")
async def get_pointcloud():
    """Serve the 3D PCD pointcloud map."""
    pcd_path = ASSETS_DIR / "demo_garden.pcd"
    if not pcd_path.exists():
        raise HTTPException(status_code=404, detail="Point cloud file not found.")
    return FileResponse(pcd_path, media_type="text/plain", filename="map.pcd")

@app.post("/api/action")
async def post_action(req: ActionRequest, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Dispatch physical command to Home Assistant."""
    allowed_actions = {"start", "pause", "dock", "stop"}
    if req.action not in allowed_actions:
        raise HTTPException(status_code=400, detail=f"Action '{req.action}' not permitted. Allowed: {list(allowed_actions)}")

    # Fail-closed when live HA_TOKEN is configured or API_AUTH_TOKEN is defined
    expected_token = os.getenv("API_AUTH_TOKEN")
    ha_live = bool(os.getenv("HA_TOKEN"))
    if ha_live and not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API_AUTH_TOKEN must be configured before dispatching live mower commands.",
        )
    if expected_token:
        provided = credentials.credentials if credentials else None
        if not provided or not hmac.compare_digest(provided, expected_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API authorization token.",
                headers={"WWW-Authenticate": "Bearer"}
            )

    try:
        success = await client.send_command(req.action)
        return {"status": "ok", "action": req.action, "success": success}
    except Exception:
        logger.exception("Failed to dispatch mower command")
        raise HTTPException(status_code=500, detail="Internal error while dispatching mower command.")

# Mount static frontend
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=False)
