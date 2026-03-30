"""Queue management API routes."""
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.queue_manager import queue_manager

router = APIRouter(tags=["queue"])


class AddSingerRequest(BaseModel):
    name: str
    song_title: str
    song_artist: str = "Unknown"
    file_path: str = ""
    tip_amount: float = 0.0


class TipRequest(BaseModel):
    amount: float


class MoveRequest(BaseModel):
    to_position: int


@router.get("/queue")
def get_queue():
    return {
        "queue": queue_manager.get_queue(),
        "current": queue_manager.get_current(),
    }


@router.post("/queue/add")
def add_to_queue(req: AddSingerRequest):
    if not queue_manager.session_id:
        return {"error": "No active session. Start a session first."}
    entry = queue_manager.add_singer(
        name=req.name,
        song_title=req.song_title,
        song_artist=req.song_artist,
        file_path=req.file_path,
        tip_amount=req.tip_amount,
    )
    return {"message": f"Added {entry.name}", "queue": queue_manager.get_queue()}


@router.post("/queue/next")
def next_singer():
    current = queue_manager.next_singer()
    return {
        "current": current,
        "queue": queue_manager.get_queue(),
    }


@router.delete("/queue/{position}")
def remove_from_queue(position: int):
    if queue_manager.remove_singer(position):
        return {"message": "Removed", "queue": queue_manager.get_queue()}
    return {"error": "Invalid position"}


@router.post("/queue/{position}/move")
def move_in_queue(position: int, req: MoveRequest):
    if queue_manager.move_singer(position, req.to_position):
        return {"queue": queue_manager.get_queue()}
    return {"error": "Invalid positions"}


@router.post("/queue/{position}/top")
def move_to_top(position: int):
    if queue_manager.move_to_top(position):
        return {"queue": queue_manager.get_queue()}
    return {"error": "Invalid position"}


@router.post("/queue/{position}/tip")
def add_tip(position: int, req: TipRequest):
    if queue_manager.add_tip(position, req.amount):
        return {"message": f"Tip of ${req.amount:.2f} added", "queue": queue_manager.get_queue()}
    return {"error": "Invalid position or amount"}


@router.post("/queue/clear")
def clear_queue():
    queue_manager.clear_queue()
    return {"message": "Queue cleared"}
