import time
from textual.widgets import Static
from textual.binding import Binding
import widgets.pomo_state as pomo_state

_DETAIL_WIDTH = 1440  # 1 char = 1 minute


# ── Renderers ─────────────────────────────────────────────────────────────────

def _build_cells_detail(sessions: list, day_start: float) -> list:
    now = time.time()
    elapsed = int(min((now - day_start) / 60.0, _DETAIL_WIDTH))
    cells = ["b"] * elapsed + ["f"] * (_DETAIL_WIDTH - elapsed)
    for s in sessions:
        if s["type"] != "work":
            continue
        s0 = max(s["start"], day_start)
        s1 = min(s["end"] or now, now)
        if s1 - s0 < 60:
            continue
        c0 = int((s0 - day_start) / 60.0)
        c1 = int((s1 - day_start) / 60.0)
        if c1 <= c0:
            c1 = c0 + 1
        for i in range(max(0, c0), min(_DETAIL_WIDTH, c1 + 1)):
            cells[i] = "w"
    return cells


def _build_cells_overview(sessions: list, day_start: float, width: int) -> list:
    now = time.time()
    elapsed = int(min((now - day_start) / 86400.0, 1.0) * width)
    cells = ["b"] * elapsed + ["f"] * (width - elapsed)
    for s in sessions:
        if s["type"] != "work":
            continue
        s0 = max(s["start"], day_start)
        s1 = min(s["end"] or now, now)
        if s1 - s0 < 60:
            continue
        c0 = int((s0 - day_start) / 86400.0 * width)
        c1 = int((s1 - day_start) / 86400.0 * width)
        if c1 <= c0:
            c1 = c0 + 1
        for i in range(max(0, c0), min(width, c1 + 1)):
            cells[i] = "w"
    return cells


def _cells_to_bar(cells: list) -> str:
    bar = ""
    i = 0
    while i < len(cells):
        c = cells[i]
        j = i
        while j < len(cells) and cells[j] == c:
            j += 1
        color = "#4ade80" if c == "w" else ("#f87171" if c == "b" else "#1a1a1a")
        bar += f"[{color}]{'█' * (j - i)}[/]"
        i = j
    return bar


def _hour_labels_detail() -> str:
    row = [" "] * _DETAIL_WIDTH
    for h in range(0, 24):
        pos = h * 60          # left edge of this hour's 60-char slot
        row[pos] = "|"        # tick mark at the hour boundary
        s = str(h + 1)        # label: 1-24
        for k, ch in enumerate(s):
            if pos + 1 + k < _DETAIL_WIDTH:
                row[pos + 1 + k] = ch
    return "[#888888]" + "".join(row) + "[/]"


def _hour_labels_overview(width: int) -> str:
    row = [" "] * width
    for h in range(1, 25):
        pos = min(int(h * width / 24) - 1, width - 1)
        s = str(h)
        for k, ch in enumerate(reversed(s)):
            idx = pos - k
            if 0 <= idx < width:
                row[idx] = ch
    return "[#888888]" + "".join(row) + "[/]"


# ── Widget ────────────────────────────────────────────────────────────────────

class DayTimelineWidget(Static):
    """24-hour work/break timeline. t = toggle overview / detail (1 min per char)."""

    can_focus = True

    BINDINGS = [
        Binding("t", "toggle_mode", "Toggle view", show=False),
    ]

    DEFAULT_CSS = """
    DayTimelineWidget {
        height: 4;
        width: 100%;
        padding: 0 1;
        background: #0f0f0f;
        overflow-x: auto;
        overflow-y: hidden;
    }
    DayTimelineWidget:focus {
        background: #111111;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._detail_mode: bool = False

    def on_mount(self) -> None:
        self.set_interval(5, self._draw)
        self._draw()

    def action_toggle_mode(self) -> None:
        self._detail_mode = not self._detail_mode
        self._draw()

    def _draw(self) -> None:
        pomo_state.check_day_reset()
        sessions, day_start = pomo_state.get_snapshot()

        if self._detail_mode:
            cells  = _build_cells_detail(sessions, day_start)
            bar    = _cells_to_bar(cells)
            labels = _hour_labels_detail()
            self.update(bar + "\n" + labels)
            # Auto-scroll to keep current minute centred
            try:
                current_minute = int((time.time() - day_start) / 60.0)
                target_x = max(0, current_minute - self.size.width // 2)
                self.scroll_to(x=target_x, animate=False)
            except Exception:
                pass
        else:
            try:
                width = max(24, self.content_size.width)
            except Exception:
                width = 72
            cells  = _build_cells_overview(sessions, day_start, width)
            bar    = _cells_to_bar(cells)
            labels = _hour_labels_overview(width)
            self.update(bar + "\n" + labels)
            self.scroll_to(x=0, animate=False)
