# bot/utils.py

import os
import json
from datetime import datetime
from bot.config import MOOD_OPTIONS

MOOD_FILE = "mood_data.json"

def load_mood_data():
    if not os.path.exists(MOOD_FILE):
        with open(MOOD_FILE, "w") as f:
            json.dump({}, f)
        return {}

    with open(MOOD_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # Handle empty or corrupt file gracefully
            return {}

def save_mood_data(data):
    with open(MOOD_FILE, "w") as f:
        json.dump(data, f)

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def secret_commands(text):
    match text.lower():
        case "/peach":
            return "🍑 That means: I want cuddles but I don’t wanna ask."
        case "/storm":
            return "⚡️ That means: My heart’s messy and I need your calm."
        case "/sunny":
            return "☀️ That means: You make me feel light even on heavy days."
        case "/silk":
            return "🧵 That means: I need a soft talk and a soft voice tonight."
        case _:
            return "✨ Secret code not recognized. Try again or whisper a new one."

def count_moods(entries):
    counter = {}
    for entry in entries:
        mood = entry["mood"]
        counter[mood] = counter.get(mood, 0) + 1
    return counter
