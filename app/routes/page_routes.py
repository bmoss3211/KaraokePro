"""Page/template routes."""
import os
from fastapi import APIRouter
from fastapi.responses import FileResponse
from config import load_config, save_config
from pydantic import BaseModel
from app.services.song_index import song_index

router = APIRouter()

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")


@router.get("/")
def index():
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"), media_type="text/html")


class ConfigUpdate(BaseModel):
    song_folders: list[str] | None = None
    tip_weight: int | None = None
    venue: str | None = None


@router.get("/api/config")
def get_config():
    config = load_config()
    return {
        "song_folders": config["song_folders"],
        "tip_weight": config["tip_weight"],
        "venue": config["venue"],
        "port": config["port"],
        "song_count": song_index.count,
    }


@router.post("/api/config")
def update_config(req: ConfigUpdate):
    config = load_config()
    if req.song_folders is not None:
        config["song_folders"] = req.song_folders
    if req.tip_weight is not None:
        config["tip_weight"] = req.tip_weight
    if req.venue is not None:
        config["venue"] = req.venue
    save_config(config)
    return {"message": "Config saved", "config": config}
