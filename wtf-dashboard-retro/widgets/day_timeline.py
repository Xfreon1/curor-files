import time
from textual.widgets import Static
import widgets.pomo_state as pomo_state

_WIDTH = 1440  # 24 hours × 60 minutes — 1 char = 1 minute


def _render(sessions: list, day_start: float) -> str:
    now = time.time()
    elapsed = int(min((now - day_start) / 60.0, _WIDTH))

    # 'w' = work, 'b' = break, 'f' = future
    cells = ["b"] * elapsed + ["f"] * (_WIDTH - elapsed)

    for s in sessions:
        if s["type"] != "work":
            continue
        s0 = max(s["start"], day_start)
        s1 = min(s["end"] or now, now)
        if s1 - s0 < 60:      # skip sub-minute sessions
            continue
        c0 = int((s0 - day_start) / 60.0)
        c1 = int((s1 - day_start) / 60.0)
        if c1 <= c0:
            c1 = c0 + 1
        for i in range(max(0, c0), min(_WIDTH, c1 + 1)):
            cells[i] = "w"

    # RLE → colored █ chars
    bar = ""
    i = 0
    while i < _WIDTH:
        c = cells[i]
        j = i
        while j < _WIDTH and cells[j] == c:
            j += 1
        color = "#4ade80" if c == "w" else ("#f87171" if c == "b" else "#1a1a1a")
        bar += f"[{color}]{'█' * (j - i)}[/]"
        i = j

    # Hour labels centred in each 60-char slot
    row = [" "] * _WIDTH
    for h in range(1, 25):
        centre = (h - 1) * 60 + 30
        s = str(h)
        start = centre - len(s) // 2
        for k, ch in enumerate(s):
            if 0 <= start + k < _WIDTH:
                row[start + k] = ch
    labels = "[#444444]" + "".join(row) + "[/]"

    return bar + "\n" + labels


class DayTimelineWidget(Static):
    """24-hour work/break timeline — 1 char per minute, auto-scrolls to now."""

    DEFAULT_CSS = """
    DayTimelineWidget {
        height: 3;
        width: 100%;
        padding: 0 1;
        background: #0f0f0f;
        overflow-x: auto;
        overflow-y: hidden;
    }
    """

    def on_mount(self) -> None:
        self.set_interval(5, self._draw)
        self._draw()

    def _draw(self) -> None:
        pomo_state.check_day_reset()
        sessions, day_start = pomo_state.get_snapshot()
        self.update(_render(sessions, day_start))
        # Auto-scroll so current minute is centred in the visible area
        try:
            current_minute = int((time.time() - day_start) / 60.0)
            visible = self.size.width
            target_x = max(0, current_minute - visible // 2)
            self.scroll_to(x=target_x, animate=False)
        except Exception:
            pass
