"""
Shared Pomodoro / timeline session state.
Imported by CountdownWidget (writes) and DayTimelineWidget (reads).
Thread-safe via threading.Lock. Persists to pomo_sessions.json.
Daily totals archived to pomo_history.json for monthly overview.
"""
import json
import os
import tempfile
import time
import threading
from datetime import datetime, date

_lock = threading.Lock()
_sessions: list = []
_current_day: date | None = None
_day_start: float = 0.0

_DIR = os.path.dirname(os.path.dirname(__file__))
_SAVE_PATH = os.path.join(_DIR, "pomo_sessions.json")
_HISTORY_PATH = os.path.join(_DIR, "pomo_history.json")


def _save() -> None:
    """Write sessions to disk. Must be called with _lock held."""
    data = {
        "day": _current_day.isoformat() if _current_day else None,
        "day_start": _day_start,
        "sessions": _sessions,
    }
    dir_name = os.path.dirname(_SAVE_PATH) or "."
    try:
        fd, tmp = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, _SAVE_PATH)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass


def _load_history() -> dict:
    """Load monthly history from disk."""
    if not os.path.exists(_HISTORY_PATH):
        return {}
    try:
        with open(_HISTORY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_history(history: dict) -> None:
    """Write monthly history to disk."""
    dir_name = os.path.dirname(_HISTORY_PATH) or "."
    try:
        fd, tmp = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(history, f)
        os.replace(tmp, _HISTORY_PATH)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass


def _archive_day() -> None:
    """Archive current day's totals to history. Must be called with _lock held."""
    if not _sessions or not _current_day:
        return
    now = time.time()
    work = brk = 0.0
    for s in _sessions:
        dur = max(0.0, (s["end"] or now) - s["start"])
        if s["type"] == "work":
            work += dur
        else:
            brk += dur
    if work + brk < 60:
        return
    history = _load_history()
    history[_current_day.isoformat()] = {"work": work, "break": brk}
    _save_history(history)


def _load() -> bool:
    """Load sessions from disk. Must be called with _lock held. Returns True if loaded."""
    global _sessions, _current_day, _day_start
    if not os.path.exists(_SAVE_PATH):
        return False
    try:
        with open(_SAVE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        saved_day = data.get("day")
        if saved_day != date.today().isoformat():
            # Archive the stale day before discarding
            old_day = date.fromisoformat(saved_day) if saved_day else None
            if old_day:
                _current_day = old_day
                _sessions = data.get("sessions", [])
                _archive_day()
            return False
        _current_day = date.fromisoformat(saved_day)
        _day_start = data["day_start"]
        _sessions = data["sessions"]
        # Close the last session from the previous run and start a new break
        now = time.time()
        if _sessions and _sessions[-1]["end"] is None:
            _sessions[-1]["end"] = now
        _sessions.append({"type": "break", "start": now, "end": None})
        return True
    except Exception:
        return False


def _do_init(today: date) -> None:
    """Initialize (or reset) for a new day. Must be called with _lock held."""
    global _sessions, _current_day, _day_start
    # Archive previous day before resetting
    if _current_day and _current_day != today:
        _archive_day()
    cur = "break"
    if _sessions and _sessions[-1]["end"] is None:
        cur = _sessions[-1]["type"]
    _current_day = today
    _day_start = datetime.combine(today, datetime.min.time()).timestamp()
    _sessions = [{"type": cur, "start": time.time(), "end": None}]
    _save()


# Initialize at import time — try loading from disk first
with _lock:
    if not _load():
        _do_init(date.today())


def check_day_reset() -> None:
    with _lock:
        today = date.today()
        if today != _current_day:
            _do_init(today)


def open_session(session_type: str) -> None:
    with _lock:
        now = time.time()
        if _sessions and _sessions[-1]["end"] is None:
            _sessions[-1]["end"] = now
        _sessions.append({"type": session_type, "start": now, "end": None})
        _save()


def current_type() -> str:
    with _lock:
        if _sessions and _sessions[-1]["end"] is None:
            return _sessions[-1]["type"]
        return "break"


def current_session_start() -> float:
    with _lock:
        if _sessions and _sessions[-1]["end"] is None:
            return _sessions[-1]["start"]
        return time.time()


def get_snapshot() -> tuple:
    """Return (sessions_copy, day_start) for rendering."""
    with _lock:
        return list(_sessions), _day_start


def get_month_history() -> dict:
    """Return {iso_date: {"work": secs, "break": secs}} for current month, including today live."""
    with _lock:
        history = _load_history()
        # Add today's live data
        today = date.today()
        now = time.time()
        work = brk = 0.0
        for s in _sessions:
            dur = max(0.0, (s["end"] or now) - s["start"])
            if s["type"] == "work":
                work += dur
            else:
                brk += dur
        history[today.isoformat()] = {"work": work, "break": brk}
        # Filter to current month
        prefix = today.strftime("%Y-%m")
        return {k: v for k, v in history.items() if k.startswith(prefix)}


def totals() -> tuple:
    """Return (work_secs, break_secs, completed_work_sessions)."""
    with _lock:
        now = time.time()
        work = brk = 0.0
        work_n = 0
        for s in _sessions:
            dur = max(0.0, (s["end"] or now) - s["start"])
            if s["type"] == "work":
                work += dur
                if s["end"] is not None:
                    work_n += 1
            else:
                brk += dur
        return work, brk, work_n


def reset() -> None:
    """Clear session history and restart as break."""
    with _lock:
        _sessions.clear()
        _sessions.append({"type": "break", "start": time.time(), "end": None})
        _save()
