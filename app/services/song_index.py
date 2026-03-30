"""Song file indexer with fuzzy search."""
import os
import re
import time
from dataclasses import dataclass, field
from rapidfuzz import fuzz, process


@dataclass
class Song:
    file_path: str
    artist: str
    title: str
    disc_id: str = ""
    file_type: str = ""  # cdg_pair, mp4, zip, etc.

    @property
    def search_text(self) -> str:
        return f"{self.artist} {self.title}".lower()


class SongIndex:
    def __init__(self):
        self.songs: list[Song] = []
        self._search_texts: list[str] = []
        self.scan_time: float = 0
        self.last_scan: str = ""

    def scan(self, folders: list[str], extensions: list[str]):
        """Scan folders for karaoke files and build the index."""
        start = time.time()
        songs = []
        seen_stems: set[str] = set()  # Track CDG+MP3 pairs
        self.errors: list[str] = []
        self.folders_scanned: list[str] = []
        self.total_files_seen: int = 0

        ext_set = {e.lower() for e in extensions}

        for folder in folders:
            # Normalize path separators for Windows
            folder = os.path.normpath(folder.strip())
            if not os.path.isdir(folder):
                self.errors.append(f"Folder not found: {folder}")
                continue
            self.folders_scanned.append(folder)
            for root, _dirs, files in os.walk(folder):
                for fname in files:
                    self.total_files_seen += 1
                    ext = os.path.splitext(fname)[1].lower()
                    if ext not in ext_set:
                        continue

                    full_path = os.path.join(root, fname)
                    stem = os.path.splitext(fname)[0]

                    # Handle CDG+MP3 pairs: only index once
                    if ext in (".cdg", ".mp3"):
                        pair_key = os.path.join(root, stem).lower()
                        if pair_key in seen_stems:
                            continue
                        seen_stems.add(pair_key)
                        file_type = "cdg_pair"
                    elif ext == ".mp4":
                        file_type = "mp4"
                    elif ext == ".zip":
                        file_type = "zip"
                    else:
                        file_type = ext.lstrip(".")

                    artist, title, disc_id = self._parse_filename(stem)
                    songs.append(Song(
                        file_path=full_path,
                        artist=artist,
                        title=title,
                        disc_id=disc_id,
                        file_type=file_type,
                    ))

        self.songs = songs
        self._search_texts = [s.search_text for s in songs]
        self.scan_time = time.time() - start
        self.last_scan = time.strftime("%Y-%m-%d %H:%M:%S")

    def _parse_filename(self, stem: str) -> tuple[str, str, str]:
        """Parse karaoke filename into (artist, title, disc_id).

        Common formats:
          SC8995-10 - Nickelback - Far Away
          Nickelback - Far Away
          Far Away - Nickelback
        """
        # Pattern 1: DISCID - Artist - Title
        m = re.match(r'^([A-Z]{2,}\d[\w-]*)\s*-\s*(.+?)\s*-\s*(.+)$', stem)
        if m:
            return m.group(2).strip(), m.group(3).strip(), m.group(1).strip()

        # Pattern 2: Artist - Title (most common)
        parts = stem.split(" - ", 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip(), ""

        # Pattern 3: Just the filename
        return "Unknown", stem.strip(), ""

    def search(self, query: str, limit: int = 25) -> list[dict]:
        """Fuzzy search for songs matching the query."""
        if not query or not self._search_texts:
            return []

        results = process.extract(
            query.lower(),
            self._search_texts,
            scorer=fuzz.WRatio,
            limit=limit,
            score_cutoff=45,
        )

        return [
            {
                "artist": self.songs[idx].artist,
                "title": self.songs[idx].title,
                "disc_id": self.songs[idx].disc_id,
                "file_path": self.songs[idx].file_path,
                "file_type": self.songs[idx].file_type,
                "score": int(score),
            }
            for _text, score, idx in results
        ]

    @property
    def count(self) -> int:
        return len(self.songs)


# Global singleton
song_index = SongIndex()
