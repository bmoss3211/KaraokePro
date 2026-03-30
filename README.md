# KaraokePro

Queue management app for live karaoke hosting. Handles singer rotation, song search, and tip-based priority.

## Setup

### Requirements
- Windows 10/11
- Python 3.10+ (download from [python.org](https://www.python.org/downloads/) — check "Add Python to PATH" during install)

### Install & Run

1. Download or clone this repo
2. Double-click **`start.bat`**
3. The app opens in your browser at `http://localhost:8000`

### First Run

1. Click the gear icon (top right) to open **Settings**
2. Add your song folder path (e.g., `E:\Karaoke Songs`) — one path per line
3. Click **Save & Rescan**
4. Click **Start Session** to begin your night

## Usage

- **Add Singer**: Type name, search for a song, optionally set a tip, click "Add to Queue"
- **Song Done**: Click the green "SONG DONE — NEXT SINGER" button to advance the rotation
- **Tips**: Click the `$` button on any queued singer to add a tip mid-queue
- **Rotation**: Everyone gets their 1st song before anyone gets a 2nd. Tips bump you up within your current round, not past people who haven't sung yet.
- **Ctrl+Enter**: Quick-add shortcut
