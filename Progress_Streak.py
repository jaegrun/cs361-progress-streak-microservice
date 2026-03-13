"""
Progress / Streak microservice core logic.

This module is designed to be used both as:
- a local Python import (for tests), and
- an HTTP microservice via the Flask wrapper in app.py.

Data model (stored in streaks.json):
{
  "<user_id>": {
    "<activity_type>": {
      "current_streak": 3,
      "best_streak": 10,
      "last_activity": "2026-03-11T18:00:00+00:00"
    }
  }
}
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any


DATA_FILE = "streaks.json"


def _utc_today() -> datetime:
    """Return current date in UTC with time cleared."""
    now = datetime.now(timezone.utc)
    return datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc)


def _parse_timestamp(ts: str) -> datetime:
    """Parse ISO-8601 timestamp, accepting 'Z' suffix."""
    normalized = ts.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).astimezone(timezone.utc)


def _load_data() -> Dict[str, Any]:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def _save_data(data: Dict[str, Any]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def log_activity(user_id: str, activity_type: str, timestamp: str | None = None) -> Dict[str, Any]:
    """
    Record an activity occurrence for a user and update their streak.

    - If activity is on the same UTC day as the last one: streak stays the same.
    - If next consecutive day: streak increments.
    - If 2+ days gap: streak resets to 1.
    """
    if not user_id or not activity_type:
        return {"success": False, "error": "user_id and activity_type are required"}

    data = _load_data()

    if timestamp is None:
        today = _utc_today()
    else:
        dt = _parse_timestamp(timestamp)
        today = datetime(year=dt.year, month=dt.month, day=dt.day, tzinfo=timezone.utc)

    user_rec = data.setdefault(user_id, {})
    streak_rec = user_rec.get(activity_type)

    if streak_rec and streak_rec.get("last_activity"):
        last_dt = _parse_timestamp(streak_rec["last_activity"])
        last_day = datetime(
            year=last_dt.year, month=last_dt.month, day=last_dt.day, tzinfo=timezone.utc
        )
        delta_days = (today - last_day).days

        if delta_days == 0:
            current_streak = streak_rec.get("current_streak", 1)
        elif delta_days == 1:
            current_streak = streak_rec.get("current_streak", 0) + 1
        else:
            current_streak = 1
    else:
        current_streak = 1

    best_streak = max(current_streak, (streak_rec or {}).get("best_streak", 0))

    new_rec = {
        "current_streak": current_streak,
        "best_streak": best_streak,
        "last_activity": today.isoformat(),
    }
    user_rec[activity_type] = new_rec
    data[user_id] = user_rec
    _save_data(data)

    return {"success": True, "user_id": user_id, "activity_type": activity_type, **new_rec}


def get_status(user_id: str, activity_type: str) -> Dict[str, Any]:
    """
    Return current/best streak info for a user/activity_type.
    """
    if not user_id or not activity_type:
        return {"success": False, "error": "user_id and activity_type are required"}

    data = _load_data()
    user_rec = data.get(user_id, {})
    streak_rec = user_rec.get(activity_type)

    if not streak_rec:
        return {
            "success": True,
            "user_id": user_id,
            "activity_type": activity_type,
            "current_streak": 0,
            "best_streak": 0,
            "last_activity": None,
        }

    return {
        "success": True,
        "user_id": user_id,
        "activity_type": activity_type,
        "current_streak": streak_rec.get("current_streak", 0),
        "best_streak": streak_rec.get("best_streak", 0),
        "last_activity": streak_rec.get("last_activity"),
    }

