"""
Shared Pomodoro / timeline session state.
Imported by CountdownWidget (writes) and DayTimelineWidget (reads).
Thread-safe via threading.Lock.
"""
import time
import threading
from datetime import datetime, date

_lock = threading.Lock()
_sessions: list = []
_current_day: date | None = None
_day_start: float = 0.0


def _do_init(today: date) -> None:
    """Initialize (or reset) for a new day. Must be called with _lock held."""
    global _sessions, _current_day, _day_start
    cur = "break"
    if _sessions and _sessions[-1]["end"] is None:
        cur = _sessions[-1]["type"]
    _current_day = today
    _day_start = datetime.combine(today, datetime.min.time()).timestamp()
    _sessions = [{"type": cur, "start": time.time(), "end": None}]


# Initialize at import time
with _lock:
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
