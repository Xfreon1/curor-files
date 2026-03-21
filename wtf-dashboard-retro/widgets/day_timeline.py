import time
from textual.widgets import Static
from textual.binding import Binding
import widgets.pomo_state as pomo_state

_COLORS = {"w": "#4ade80", "b": "#f87171", "f": "#1a1a1a"}
_TEXT   = {"w": "#1a1a1a", "b": "#1a1a1a", "f": "#666666"}


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


class DayTimelineWidget(Static):
    """24-hour work/break timeline. t = toggle overview / detail (4 bars)."""

    can_focus = True

    BINDINGS = [
        Binding("t", "toggle_mode", "Toggle view", show=False),
    ]

    DEFAULT_CSS = """
    DayTimelineWidget {
        height: 1;
        width: 100%;
        padding: 0 1;
        background: #0f0f0f;
    }
    DayTimelineWidget:focus {
        background: #111111;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._detail_mode: bool = False  # start with single 24h bar

    def on_mount(self) -> None:
        self.set_interval(5, self._draw)
        self.call_after_refresh(self._draw)

    def on_resize(self, event) -> None:
        self._draw()

    def action_toggle_mode(self) -> None:
        self._detail_mode = not self._detail_mode
        self.styles.height = 4 if self._detail_mode else 1
        self._draw()

    def _draw(self) -> None:
        pomo_state.check_day_reset()
        sessions, day_start = pomo_state.get_snapshot()

        try:
            width = self.size.width - 2
            if width < 24:
                width = 72
        except Exception:
            width = 72

        if self._detail_mode:
            lines = []
            for bar_idx in range(4):
                lines.append(_build_bar(sessions, day_start, bar_idx * 6, width))
            self.update("\n".join(lines))
        else:
            self.update(_build_overview(sessions, day_start, width))
