# Progress / Streak Microservice (CS 361 Group 6)

## Overview

This microservice tracks **user progress streaks** over time.  
It records when a user completes an activity (such as finishing a study task) and maintains:

- `current_streak` – how many consecutive days they’ve logged the activity.
- `best_streak` – their all‑time longest streak.
- `last_activity` – the last date the activity was logged (in UTC).

It is designed to be called over **JSON-over-HTTP** by a Main Program, not via direct function calls.

---

## Architecture

- **Core logic module**: `Progress_Streak.py`
  - Pure Python functions for loading/saving streak data and updating streaks.
  - Data stored in `streaks.json` in this folder.
- **HTTP wrapper**: `app.py`
  - Flask app that exposes the core logic over a small REST API.
  - Listens on `127.0.0.1:5004` by default.

Data model in `streaks.json`:

```json
{
  "<user_id>": {
    "<activity_type>": {
      "current_streak": 3,
      "best_streak": 10,
      "last_activity": "2026-03-11T00:00:00+00:00"
    }
  }
}
```

- `user_id`: arbitrary string identifier for the user.
- `activity_type`: e.g. `"task_completion"` (allows multiple independent streaks per user).

---

## How streaks are calculated

The service uses **UTC dates** (time of day is ignored):

- **First log** for a `(user_id, activity_type)`:
  - `current_streak = 1`, `best_streak = 1`.
- **Same UTC day as last_activity**:
  - `current_streak` stays the same (no double‑counting).
- **Next consecutive day**:
  - `current_streak += 1`.
- **Gap of 2+ days**:
  - `current_streak` resets to `1`.
- `best_streak` is always the maximum of the current streak and previous best.

---

## HTTP API

Base URL (default):

```text
http://127.0.0.1:5004
```

### 1. Health check

`GET /health`

Response (200):

```json
{
  "status": "ok",
  "service": "progress-streak"
}
```

---

### 2. Log an activity (update streak)

`POST /log`

Request body (JSON):

```json
{
  "user_id": "default_user",
  "activity_type": "task_completion",
  "timestamp": "2026-03-11T18:00:00+00:00"
}
```

- `user_id` (required): string.
- `activity_type` (optional, defaults to `"task_completion"` if empty).
- `timestamp` (optional):
  - If omitted, the service uses **today in UTC**.
  - If provided, must be ISO‑8601, e.g. `"2026-03-11T18:00:00+00:00"` or `"2026-03-11T18:00:00Z"`.

Success response (200):

```json
{
  "success": true,
  "user_id": "default_user",
  "activity_type": "task_completion",
  "current_streak": 3,
  "best_streak": 5,
  "last_activity": "2026-03-11T00:00:00+00:00"
}
```

Error response (400):

```json
{
  "success": false,
  "error": "user_id and activity_type are required"
}
```

---

### 3. Get streak status

`GET /streak/<user_id>`

Query parameters:

- `activity_type` – optional, defaults to `"task_completion"`.

Example:

```text
GET /streak/default_user?activity_type=task_completion
```

Success response when streak exists:

```json
{
  "success": true,
  "user_id": "default_user",
  "activity_type": "task_completion",
  "current_streak": 3,
  "best_streak": 5,
  "last_activity": "2026-03-11T00:00:00+00:00"
}
```

Success response when no streak yet:

```json
{
  "success": true,
  "user_id": "default_user",
  "activity_type": "task_completion",
  "current_streak": 0,
  "best_streak": 0,
  "last_activity": null
}
```

Error response (400) if input invalid:

```json
{
  "success": false,
  "error": "user_id and activity_type are required"
}
```

---

## How to run this microservice

Inside this folder (optionally with a virtualenv activated):

```bash
cd "CS-361-Group-6-Progress-Streak-Microservice"

python3 -m pip install flask
python3 app.py
```

You should see Flask listening on `127.0.0.1:5004`.

Test with `curl`:

```bash
curl -X POST http://127.0.0.1:5004/log \
  -H "Content-Type: application/json" \
  -d '{"user_id": "default_user", "activity_type": "task_completion"}'

curl "http://127.0.0.1:5004/streak/default_user?activity_type=task_completion"
```

---

## Example integration with a Main Program

In the Student Learning Hub main Flask app, integration looks like:

- When a task is created:

```python
requests.post(
    f"{PROGRESS_SERVICE_URL}/log",
    json={
        "user_id": "default_user",
        "activity_type": "task_completion",
    },
    timeout=3,
)
```

- When rendering the home page:

```python
resp = requests.get(
    f"{PROGRESS_SERVICE_URL}/streak/default_user",
    params={"activity_type": "task_completion"},
    timeout=3,
)
streak_info = resp.json()
```

The Main Program communicates strictly via **HTTP requests and JSON**, treating this module as a true microservice.

