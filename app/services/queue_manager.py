"""Queue manager with fair rotation and tip-based priority."""
import time
from dataclasses import dataclass, field
from datetime import datetime
from app.models.database import get_db
from config import load_config


@dataclass
class QueueEntry:
    singer_id: int
    name: str
    song_title: str
    song_artist: str
    file_path: str
    signup_time: str
    songs_sung: int = 0
    tip_amount: float = 0.0
    tip_total: float = 0.0  # Cumulative tips this session
    is_current: bool = False
    manual_position: int | None = None  # KJ override position

    @property
    def priority_score(self) -> float:
        """Lower score = goes sooner.

        Base: songs_sung * 1000 (everyone gets song N before anyone gets N+1)
        Tip bonus: subtract tip_amount * tip_weight (tips move you up within your round)
        Tiebreaker: signup_time (earlier signup goes first)
        """
        config = load_config()
        tip_weight = config.get("tip_weight", 50)
        base = self.songs_sung * 1000
        tip_bonus = self.tip_amount * tip_weight
        return base - tip_bonus


class QueueManager:
    def __init__(self):
        self._queue: list[QueueEntry] = []
        self._current: QueueEntry | None = None
        self._session_id: int | None = None

    @property
    def session_id(self) -> int | None:
        return self._session_id

    @session_id.setter
    def session_id(self, value: int):
        self._session_id = value
        self._queue = []
        self._current = None

    def add_singer(self, name: str, song_title: str, song_artist: str,
                   file_path: str = "", tip_amount: float = 0.0) -> QueueEntry:
        """Add a singer to the queue. Returns the new entry."""
        if not self._session_id:
            raise ValueError("No active session. Start a session first.")

        db = get_db()
        now = datetime.now().isoformat()

        # Check if singer already exists in this session
        row = db.execute(
            "SELECT id, songs_sung, tip_total FROM singers WHERE session_id=? AND name=? COLLATE NOCASE",
            (self._session_id, name)
        ).fetchone()

        if row:
            singer_id = row["id"]
            songs_sung = row["songs_sung"]
            new_tip_total = row["tip_total"] + tip_amount
            db.execute(
                "UPDATE singers SET tip_total=?, is_active=1 WHERE id=?",
                (new_tip_total, singer_id)
            )
        else:
            cursor = db.execute(
                "INSERT INTO singers (session_id, name, signup_time, tip_total) VALUES (?, ?, ?, ?)",
                (self._session_id, name, now, tip_amount)
            )
            singer_id = cursor.lastrowid
            songs_sung = 0

        db.commit()

        entry = QueueEntry(
            singer_id=singer_id,
            name=name,
            song_title=song_title,
            song_artist=song_artist,
            file_path=file_path,
            signup_time=now,
            songs_sung=songs_sung,
            tip_amount=tip_amount,
            tip_total=tip_amount if not row else row["tip_total"] + tip_amount,
        )

        self._queue.append(entry)
        self._sort_queue()
        return entry

    def _sort_queue(self):
        """Sort queue by priority score, then by signup time."""
        # Separate manually positioned entries from auto-sorted ones
        manual = [(e.manual_position, e) for e in self._queue if e.manual_position is not None]
        auto = [e for e in self._queue if e.manual_position is None]

        auto.sort(key=lambda e: (e.priority_score, e.signup_time))

        # Merge manual positions back in
        result = list(auto)
        for pos, entry in sorted(manual):
            idx = min(pos, len(result))
            result.insert(idx, entry)

        self._queue = result

    def get_queue(self) -> list[dict]:
        """Get the current queue as a list of dicts."""
        items = []
        for i, e in enumerate(self._queue):
            items.append({
                "position": i + 1,
                "singer_id": e.singer_id,
                "name": e.name,
                "song_title": e.song_title,
                "song_artist": e.song_artist,
                "file_path": e.file_path,
                "songs_sung": e.songs_sung,
                "tip_amount": e.tip_amount,
                "tip_total": e.tip_total,
                "is_current": e.is_current,
            })
        return items

    def get_current(self) -> dict | None:
        """Get the currently performing singer."""
        if self._current:
            return {
                "singer_id": self._current.singer_id,
                "name": self._current.name,
                "song_title": self._current.song_title,
                "song_artist": self._current.song_artist,
                "file_path": self._current.file_path,
            }
        return None

    def next_singer(self) -> dict | None:
        """Mark current song as done and advance to the next singer.

        Records the completed song in history and updates the singer's count.
        """
        db = get_db()

        # Record completed song
        if self._current:
            now = datetime.now().isoformat()
            db.execute(
                """INSERT INTO song_history
                   (singer_id, session_id, song_title, song_artist, file_path, sung_at, tip_amount)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (self._current.singer_id, self._session_id,
                 self._current.song_title, self._current.song_artist,
                 self._current.file_path, now, self._current.tip_amount)
            )
            db.execute(
                "UPDATE singers SET songs_sung = songs_sung + 1 WHERE id=?",
                (self._current.singer_id,)
            )
            db.commit()
            self._current.is_current = False

        # Pop next from queue
        if self._queue:
            self._current = self._queue.pop(0)
            self._current.is_current = True
            return self.get_current()

        self._current = None
        return None

    def remove_singer(self, position: int) -> bool:
        """Remove a singer from the queue by position (1-based)."""
        idx = position - 1
        if 0 <= idx < len(self._queue):
            self._queue.pop(idx)
            return True
        return False

    def move_singer(self, from_pos: int, to_pos: int) -> bool:
        """Move a singer from one position to another (1-based)."""
        fi, ti = from_pos - 1, to_pos - 1
        if 0 <= fi < len(self._queue) and 0 <= ti < len(self._queue):
            entry = self._queue.pop(fi)
            entry.manual_position = ti
            self._queue.insert(ti, entry)
            return True
        return False

    def move_to_top(self, position: int) -> bool:
        """Move a singer to the top of the queue (1-based)."""
        return self.move_singer(position, 1)

    def add_tip(self, position: int, amount: float) -> bool:
        """Add a tip to a singer in the queue (1-based position)."""
        idx = position - 1
        if 0 <= idx < len(self._queue) and amount > 0:
            self._queue[idx].tip_amount += amount
            self._queue[idx].tip_total += amount
            # Update DB
            db = get_db()
            db.execute(
                "UPDATE singers SET tip_total = tip_total + ? WHERE id=?",
                (amount, self._queue[idx].singer_id)
            )
            db.commit()
            self._sort_queue()
            return True
        return False

    def clear_queue(self):
        """Clear the entire queue."""
        self._queue = []
        self._current = None

    def get_stats(self) -> dict:
        """Get session statistics."""
        if not self._session_id:
            return {"total_singers": 0, "total_songs": 0, "in_queue": 0, "tips_total": 0}

        db = get_db()
        singers = db.execute(
            "SELECT COUNT(*) as c FROM singers WHERE session_id=?",
            (self._session_id,)
        ).fetchone()
        songs = db.execute(
            "SELECT COUNT(*) as c FROM song_history WHERE session_id=?",
            (self._session_id,)
        ).fetchone()
        tips = db.execute(
            "SELECT COALESCE(SUM(tip_total), 0) as t FROM singers WHERE session_id=?",
            (self._session_id,)
        ).fetchone()

        return {
            "total_singers": singers["c"],
            "total_songs": songs["c"],
            "in_queue": len(self._queue),
            "tips_total": tips["t"],
            "now_singing": self.get_current(),
        }


# Global singleton
queue_manager = QueueManager()
