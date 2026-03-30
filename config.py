"""KaraokePro configuration."""
import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "config.json")

DEFAULTS = {
    "song_folders": [],  # List of paths to scan for karaoke files
    "port": 8000,
    "tip_weight": 50,  # How much $1 of tip affects priority (higher = more impact)
    "song_extensions": [".cdg", ".mp3", ".mp4", ".zip", ".kar", ".mkv", ".avi", ".wmv"],
    "venue": "Chaplins",
}


def load_config() -> dict:
    config = dict(DEFAULTS)
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config.update(json.load(f))
    return config


def save_config(config: dict):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
