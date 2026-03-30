"""Session management API routes."""
from datetime import datetime
from fastapi import APIRouter
from app.models.database import get_db
from app.services.queue_manager import queue_manager
from config import load_config

router = APIRouter(tags=["sessions"])


@router.post("/session/start")
def start_session():
    config = load_config()
    db = get_db()
    now = datetime.now()
    cursor = db.execute(
        "INSERT INTO sessions (date, start_time, venue) VALUES (?, ?, ?)",
        (now.strftime("%Y-%m-%d"), now.isoformat(), config["venue"])
    )
    db.commit()
    session_id = cursor.lastrowid
    queue_manager.session_id = session_id
    return {"session_id": session_id, "message": "Session started"}


@router.post("/session/end")
def end_session():
    if not queue_manager.session_id:
        return {"error": "No active session"}
    db = get_db()
    db.execute(
        "UPDATE sessions SET end_time=? WHERE id=?",
        (datetime.now().isoformat(), queue_manager.session_id)
    )
    db.commit()
    stats = queue_manager.get_stats()
    queue_manager.clear_queue()
    queue_manager._session_id = None
    return {"message": "Session ended", "stats": stats}


@router.get("/session/current")
def current_session():
    if not queue_manager.session_id:
        return {"active": False}
    return {
        "active": True,
        "session_id": queue_manager.session_id,
        "stats": queue_manager.get_stats(),
    }


@router.get("/session/history")
def session_history():
    """Get singer history for the current session."""
    if not queue_manager.session_id:
        return []
    db = get_db()
    rows = db.execute(
        """SELECT s.name, s.songs_sung, s.tip_total, s.signup_time,
                  GROUP_CONCAT(h.song_title, ', ') as songs_list
           FROM singers s
           LEFT JOIN song_history h ON h.singer_id = s.id
           WHERE s.session_id = ?
           GROUP BY s.id
           ORDER BY s.signup_time""",
        (queue_manager.session_id,)
    ).fetchall()
    return [dict(r) for r in rows]
