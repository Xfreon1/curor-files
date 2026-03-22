import calendar
import time
from datetime import date
from textual.widgets import Static
from textual.binding import Binding
import widgets.pomo_state as pomo_state

_COLORS = {"w": "#4ade80", "b": "#f87171", "f": "#1a1a1a"}
_TEXT   = {"w": "#1a1a1a", "b": "#1a1a1a", "f": "#666666"}

_MODES = ["overview", "detail", "month"]


def _build_bar(sessions: list, day_start: float, start_hour: int, width: int) -> str:
    """Build one 6-hour bar with hour labels integrated inside."""
    now = time.time()
    bar_start_min = start_hour * 60
    mins_per_char = 360.0 / width
    elapsed_min = (now - day_start) / 60.0

    # 1) Cell types: work / break / future
    cells = []
    for i in range(width):
        abs_min = bar_start_min + i * mins_per_char
        cells.append("f" if abs_min >= elapsed_min else "b")

    # 2) Overlay work sessions
    for s in sessions:
        if s["type"] != "work":
            continue
        s0 = max(s["start"], day_start)
        s1 = min(s["end"] or now, now)
        if s1 - s0 < 60:
            continue
        s0_min = (s0 - day_start) / 60.0
        s1_min = (s1 - day_start) / 60.0
        c0 = int((s0_min - bar_start_min) / mins_per_char)
        c1 = int((s1_min - bar_start_min) / mins_per_char)
        for i in range(max(0, c0), min(width, c1 + 1)):
            if cells[i] != "f":
                cells[i] = "w"

    # 3) Hour labels inside the bar
    chars = [" "] * width
    for h in range(6):
        abs_hour = start_hour + h
        pos = int(h * width / 6)
        label = f"|{abs_hour}"
        for k, ch in enumerate(label):
            if pos + k < width:
                chars[pos + k] = ch

    # 4) Render — group consecutive same-type cells
    result = ""
    i = 0
    while i < width:
        c = cells[i]
        j = i
        seg = ""
        while j < width and cells[j] == c:
            seg += chars[j]
            j += 1
        result += f"[{_TEXT[c]} on {_COLORS[c]}]{seg}[/]"
        i = j
    return result


def _build_overview(sessions: list, day_start: float, width: int) -> str:
    """Build single full-width 24-hour bar with hour labels inside."""
    now = time.time()
    mins_per_char = 1440.0 / width
    elapsed_min = (now - day_start) / 60.0

    cells = []
    for i in range(width):
        abs_min = i * mins_per_char
        cells.append("f" if abs_min >= elapsed_min else "b")

    for s in sessions:
        if s["type"] != "work":
            continue
        s0 = max(s["start"], day_start)
        s1 = min(s["end"] or now, now)
        if s1 - s0 < 60:
            continue
        s0_min = (s0 - day_start) / 60.0
        s1_min = (s1 - day_start) / 60.0
        c0 = int(s0_min / mins_per_char)
        c1 = int(s1_min / mins_per_char)
        for i in range(max(0, c0), min(width, c1 + 1)):
            if cells[i] != "f":
                cells[i] = "w"

    chars = [" "] * width
    for h in range(24):
        pos = int(h * width / 24)
        label = f"|{h}"
        for k, ch in enumerate(label):
            if pos + k < width:
                chars[pos + k] = ch

    result = ""
    i = 0
    while i < width:
        c = cells[i]
        j = i
        seg = ""
        while j < width and cells[j] == c:
            seg += chars[j]
            j += 1
        result += f"[{_TEXT[c]} on {_COLORS[c]}]{seg}[/]"
        i = j
    return result


def _build_month(history: dict, width: int) -> str:
    """Build monthly work/break overview grid."""
    today = date.today()
    num_days = calendar.monthrange(today.year, today.month)[1]
    month_name = today.strftime("%B %Y").upper()

    # Each entry: "DD ██████░░ WW% " = ~15 chars
    entry_w = 15
    cols = max(1, width // entry_w)

    lines = [f"[bold #888888]{month_name}[/]  [#444444]t = toggle[/]"]

    row = []
    for d in range(1, num_days + 1):
        key = date(today.year, today.month, d).isoformat()
        day_data = history.get(key, {})
        work_s = day_data.get("work", 0)
        break_s = day_data.get("break", 0)
        total = work_s + break_s
        pct = int(work_s / total * 100) if total > 0 else 0

        bar_w = 6
        filled = int(pct / 100 * bar_w)
        bar = f"[#4ade80]{'█' * filled}[/][#333333]{'░' * (bar_w - filled)}[/]"

        if d == today.day:
            entry = f"[bold #ffaf00]{d:2}[/] {bar} [#4ade80]{pct:3d}%[/]"
        elif date(today.year, today.month, d) > today:
            entry = f"[#444444]{d:2} {'·' * bar_w}    [/]"
        else:
            entry = f"[#888888]{d:2}[/] {bar} [#666666]{pct:3d}%[/]"

        row.append(entry)
        if len(row) >= cols:
            lines.append("  ".join(row))
            row = []

    if row:
        lines.append("  ".join(row))

    return "\n".join(lines)


class DayTimelineWidget(Static):
    """24-hour work/break timeline. t = toggle overview / detail / month."""

    DEFAULT_CSS = """
    DayTimelineWidget {
        height: 1;
        width: 100%;
        padding: 0 1;
        background: #0f0f0f;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mode_idx: int = 0  # 0=overview, 1=detail, 2=month

    def on_mount(self) -> None:
        self.set_interval(5, self._draw)
        self.call_after_refresh(self._draw)

    def on_resize(self, event) -> None:
        self._draw()

    def action_toggle_mode(self) -> None:
        self._mode_idx = (self._mode_idx + 1) % 3
        mode = _MODES[self._mode_idx]
        if mode == "overview":
            self.styles.height = 1
        elif mode == "detail":
            self.styles.height = 4
        else:  # month — auto-size to content
            self.styles.height = "auto"
        self.call_after_refresh(self._draw)

    def _draw(self) -> None:
        pomo_state.check_day_reset()

        try:
            width = self.size.width - 2
            if width < 24:
                width = 72
        except Exception:
            width = 72

        mode = _MODES[self._mode_idx]

        if mode == "detail":
            sessions, day_start = pomo_state.get_snapshot()
            lines = []
            for bar_idx in range(4):
                lines.append(_build_bar(sessions, day_start, bar_idx * 6, width))
            self.update("\n".join(lines))
        elif mode == "month":
            history = pomo_state.get_month_history()
            self.update(_build_month(history, width))
        else:
            sessions, day_start = pomo_state.get_snapshot()
            self.update(_build_overview(sessions, day_start, width))
