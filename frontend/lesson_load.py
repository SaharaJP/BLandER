import json
import os
from pathlib import Path

LESSONS_DIR = Path(__file__).parent.parent / "lessons"


def load_lessons():
    lessons = []
    for file in LESSONS_DIR.glob("lesson_*.json"):
        with open(file, "r", encoding="utf-8") as f:
            lessons.append(json.load(f))
    return sorted(lessons, key=lambda x: x["id"])