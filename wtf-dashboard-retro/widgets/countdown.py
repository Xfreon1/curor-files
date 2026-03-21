import time
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input
from textual.binding import Binding


def _timer_bar(remaining: float, total: float, width: int = 20) -> str:
    if total <= 0:
        return ""
    ratio = max(0.0, remaining / total)
    filled = int(ratio * width)
    if ratio > 0.5:
        color = "#4ade80"
    elif ratio > 0.2:
        color = "#fbbf24"
    else:
        color = "#f87171"
    return f"[{color}]{'█' * filled}[/][#2a2a2a]{'░' * (width - filled)}[/]"


def _fmt(seconds: float) -> str:
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    if h > 0:
        return f"{h}h {m:02d}m"
    elif m > 0:
        return f"{m}m {s:02d}s"
    return f"{s}s"


class CountdownWidget(Widget):
    """Countdown timer with Pomodoro work/break session tracking."""

    can_focus = True

    BINDINGS = [
        Binding("s", "start_stop",  "Start/Stop", show=False),
        Binding("r", "reset",       "Reset",      show=False),
        Binding("e", "edit",        "Set Time",   show=False),
        Binding("p", "reset_pomo",  "Reset Log",  show=False),
    ]

    DEFAULT_CSS = """
    CountdownWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 0;
        overflow: hidden;
    }
    CountdownWidget:focus, CountdownWidget:focus-within {
        border: round #4ade80;
    }
    #cd-display {
        height: 1fr;
        padding: 1 2;
        content-align: center top;
        overflow-y: auto;
    }
    #cd-input {
        height: 3;
        margin: 0 1 1 1;
        background: #111111;
        color: #e8e8e8;
        border: round #4ade80;
        display: none;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._total: float = 0.0
        self._remaining: float = 0.0
        self._running: bool = False
        self._last_tick: float = 0.0
        # Pomodoro session tracking
        self._pomo_active: bool = False    # True once first started
        self._pomo_is_work: bool = False   # current session type
        self._pomo_session_start: float = 0.0
        self._pomo_work: float = 0.0       # accumulated work seconds
        self._pomo_break: float = 0.0      # accumulated break seconds
        self._pomo_work_n: int = 0         # completed work sessions
        self._pomo_break_n: int = 0        # completed break sessions

    def compose(self) -> ComposeResult:
        yield Static(id="cd-display")
        yield Input(placeholder="e.g. 1:30  or  90  (h:mm or minutes) — Enter to set", id="cd-input")

    def on_mount(self) -> None:
        self.set_interval(0.5, self._tick)
        self._refresh_display()

    # ── Pomodoro helpers ──────────────────────────────────────────────────

    def _pomo_on_start(self) -> None:
        """Call when timer starts running → begin/resume WORK session."""
        now = time.monotonic()
        if self._pomo_active and not self._pomo_is_work:
            # closing a BREAK session
            self._pomo_break += now - self._pomo_session_start
            self._pomo_break_n += 1
        self._pomo_active = True
        self._pomo_is_work = True
        self._pomo_session_start = now

    def _pomo_on_stop(self) -> None:
        """Call when timer pauses/ends → close WORK, open BREAK session."""
        if not self._pomo_active or not self._pomo_is_work:
            return
        now = time.monotonic()
        self._pomo_work += now - self._pomo_session_start
        self._pomo_work_n += 1
        self._pomo_is_work = False
        self._pomo_session_start = now

    def _pomo_report(self) -> str:
        now = time.monotonic()
        work = self._pomo_work
        brk = self._pomo_break

        # Add live current session time
        if self._pomo_active:
            live = now - self._pomo_session_start
            if self._pomo_is_work:
                work += live
            else:
                brk += live

        if not self._pomo_active:
            return "[#444444]s=start  p=reset log[/]"

        cur_label = "[#4ade80]WORK[/]" if self._pomo_is_work else "[#f87171]BREAK[/]"
        cur_time = _fmt(now - self._pomo_session_start)

        return (
            "[#2a2a2a]─────────────────────[/]\n"
            f"[#4ade80]WORK [/]  {_fmt(work):<10} [#666666]×{self._pomo_work_n}[/]\n"
            f"[#f87171]BREAK[/]  {_fmt(brk):<10} [#666666]×{self._pomo_break_n}[/]\n"
            f"[#888888]now:[/] {cur_label}  {cur_time}"
        )

    # ── Timer core ────────────────────────────────────────────────────────

    def _tick(self) -> None:
        if not self._running or self._remaining <= 0:
            return
        now = time.monotonic()
        elapsed = now - self._last_tick
        self._last_tick = now
        self._remaining = max(0.0, self._remaining - elapsed)
        if self._remaining <= 0:
            self._running = False
            self._pomo_on_stop()
        self._refresh_display()

    def _refresh_display(self) -> None:
        rem = self._remaining
        h = int(rem) // 3600
        m = (int(rem) % 3600) // 60
        s = int(rem) % 60

        if self._total <= 0:
            time_str = "[#666666]No timer set[/]\n[#444444]e = set time[/]"
            bar_str = ""
        else:
            if rem <= 0:
                time_str = "[bold #f87171]TIME'S UP[/]"
                bar_str = f"\n[#f87171]{'░' * 20}[/]"
            else:
                if h > 0:
                    time_str = (
                        f"[bold #4ade80]{h}[/][#888888]h [/]"
                        f"[bold #4ade80]{m:02}[/][#888888]m [/]"
                        f"[bold #4ade80]{s:02}[/][#888888]s[/]"
                    )
                else:
                    time_str = (
                        f"[bold #4ade80]{m:02}[/][#888888]m [/]"
                        f"[bold #4ade80]{s:02}[/][#888888]s[/]"
                    )
                bar_str = f"\n{_timer_bar(rem, self._total)}"

        status = "[bold #4ade80]RUNNING[/]" if self._running else "[#666666]PAUSED[/]"
        if self._total <= 0:
            status = "[#444444]──────[/]"

        hint = "[#444444]s=start/stop  r=reset  e=edit[/]"
        pomo = self._pomo_report()

        lines = (
            f"[bold #888888]TIMER[/]\n\n"
            f"{status}\n\n"
            f"{time_str}"
            f"{bar_str}\n\n"
            f"{hint}\n\n"
            f"{pomo}"
        )
        self.query_one("#cd-display", Static).update(lines)

    # ── Actions ───────────────────────────────────────────────────────────

    def action_start_stop(self) -> None:
        if self._total <= 0 or self._remaining <= 0:
            return
        self._running = not self._running
        if self._running:
            self._last_tick = time.monotonic()
            self._pomo_on_start()
        else:
            self._pomo_on_stop()
        self._refresh_display()

    def action_reset(self) -> None:
        if self._running:
            self._pomo_on_stop()
        self._remaining = self._total
        self._running = False
        self._refresh_display()

    def action_reset_pomo(self) -> None:
        """Clear Pomodoro session log."""
        self._pomo_active = False
        self._pomo_is_work = False
        self._pomo_work = 0.0
        self._pomo_break = 0.0
        self._pomo_work_n = 0
        self._pomo_break_n = 0
        self._pomo_session_start = 0.0
        self._refresh_display()

    def action_edit(self) -> None:
        inp = self.query_one("#cd-input", Input)
        inp.display = True
        inp.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        seconds = self._parse_time(text)
        if seconds and seconds > 0:
            if self._running:
                self._pomo_on_stop()
            self._total = float(seconds)
            self._remaining = float(seconds)
            self._running = False
        event.input.clear()
        event.input.display = False
        self.focus()
        self._refresh_display()

    def on_key(self, event) -> None:
        if event.key == "escape":
            inp = self.query_one("#cd-input", Input)
            if inp.display:
                inp.clear()
                inp.display = False
                self.focus()
                event.stop()

    @staticmethod
    def _parse_time(text: str) -> int | None:
        """Parse '1:30' → 5400s, '90' → 5400s, '1:30:00' → 5400s."""
        try:
            parts = text.split(":")
            if len(parts) == 1:
                return int(parts[0]) * 60
            elif len(parts) == 2:
                return int(parts[0]) * 3600 + int(parts[1]) * 60
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except ValueError:
            return None
