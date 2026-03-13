"""
HTTP wrapper for the Progress / Streak microservice.

Exposes the core functions in Progress_Streak.py over JSON/HTTP
so that main programs can track and query user streaks.

Endpoints:
- GET  /health
- POST /log
- GET  /streak/<user_id>
"""

from __future__ import annotations

from typing import Any, Dict

from flask import Flask, jsonify, request

import Progress_Streak

app = Flask(__name__)


@app.get("/health")
def health() -> tuple[Dict[str, Any], int]:
    return {"status": "ok", "service": "progress-streak"}, 200


@app.post("/log")
def log_activity_endpoint():
    payload = request.get_json(silent=True) or {}
    user_id = (payload.get("user_id") or "").strip()
    activity_type = (payload.get("activity_type") or "").strip() or "task_completion"
    timestamp = payload.get("timestamp")

    result = Progress_Streak.log_activity(
        user_id=user_id,
        activity_type=activity_type,
        timestamp=timestamp,
    )

    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@app.get("/streak/<user_id>")
def streak_status(user_id: str):
    activity_type = (request.args.get("activity_type") or "task_completion").strip()
    result = Progress_Streak.get_status(user_id=user_id, activity_type=activity_type)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


if __name__ == "__main__":
    # Use port 5004 so it does not conflict with other services.
    app.run(host="127.0.0.1", port=5004, debug=False)

