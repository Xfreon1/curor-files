import time
from textual.widgets import Static
import widgets.pomo_state as pomo_state

_BAR_LINES = 1  # terminal rows for the colored bar


def _render(sessions: list, day_start: float, width: int) -> str:
    now = time.time()

    # How many cells have elapsed so far today
    elapsed = int(min((now - day_start) / 86400.0, 1.0) * width)

    # Build cell array: 'w'=work, 'b'=break, 'f'=future
    cells = ["b"] * elapsed + ["f"] * (width - elapsed)

    for s in sessions:
        if s["type"] != "work":
            continue
        s0 = max(s["start"], day_start)
        s1 = min(s["end"] or now, now)
        if s1 <= s0:
            continue
        c0 = int((s0 - day_start) / 86400.0 * width)
        c1 = min(int((s1 - day_start) / 86400.0 * width), elapsed - 1)
        for i in range(max(0, c0), min(width, c1 + 1)):
            cells[i] = "w"

    # RLE → colored █ chars
    bar = ""
    i = 0
    while i < width:
        c = cells[i]
        j = i
        while j < width and cells[j] == c:
            j += 1
        if c == "w":
            color = "#4ade80"
        elif c == "b":
            color = "#f87171"
        else:
            color = "#1a1a1a"
        bar += f"[{color}]{'█' * (j - i)}[/]"
        i = j

    # Hour labels: right-align each number at its hour boundary
    row = [" "] * width
    for h in range(1, 25):
        pos = min(int(h * width / 24) - 1, width - 1)
        s = str(h)
        for k, ch in enumerate(reversed(s)):
            idx = pos - k
            if 0 <= idx < width:
                row[idx] = ch
    labels = "[#444444]" + "".join(row) + "[/]"

    return ("\n".join([bar] * _BAR_LINES)) + "\n" + labels


class DayTimelineWidget(Static):
    """Full-width 24-hour work/break timeline bar."""

    DEFAULT_CSS = """
    DayTimelineWidget {
        height: 3;
        width: 100%;
        padding: 0 1;
        background: #0f0f0f;
    }
    """

    def on_mount(self) -> None:
        self.set_interval(5, self._draw)
        self._draw()

    def _draw(self) -> None:
        pomo_state.check_day_reset()
        try:
            width = max(24, self.content_size.width)
        except Exception:
            width = 72
        sessions, day_start = pomo_state.get_snapshot()
        self.update(_render(sessions, day_start, width))
