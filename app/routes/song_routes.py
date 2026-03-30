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
        "folders_scanned": getattr(song_index, 'folders_scanned', []),
        "total_files_seen": getattr(song_index, 'total_files_seen', 0),
        "errors": getattr(song_index, 'errors', []),
        "sample_songs": [
            {"artist": s.artist, "title": s.title, "file_type": s.file_type}
            for s in song_index.songs[:5]
        ] if song_index.songs else [],
    }


@router.post("/songs/rescan")
def rescan_songs():
    config = load_config()
    if not config["song_folders"]:
        return {"count": 0, "scan_time": 0, "errors": ["No song folders configured"]}
    song_index.scan(config["song_folders"], config["song_extensions"])
    return {
        "count": song_index.count,
        "scan_time": round(song_index.scan_time, 2),
        "folders_scanned": song_index.folders_scanned,
        "total_files_seen": song_index.total_files_seen,
        "extensions": config["song_extensions"],
        "errors": song_index.errors,
    }
