"""Song search API routes."""
from fastapi import APIRouter, Query
from app.services.song_index import song_index
from config import load_config

router = APIRouter(tags=["songs"])


@router.get("/songs/search")
def search_songs(q: str = Query("", min_length=1), limit: int = Query(25, le=50)):
    return song_index.search(q, limit=limit)


@router.get("/songs/stats")
def song_stats():
    return {
        "count": song_index.count,
        "scan_time": round(song_index.scan_time, 2),
        "last_scan": song_index.last_scan,
    }


@router.post("/songs/rescan")
def rescan_songs():
    config = load_config()
    if config["song_folders"]:
        song_index.scan(config["song_folders"], config["song_extensions"])
    return {
        "count": song_index.count,
        "scan_time": round(song_index.scan_time, 2),
    }
