import time
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input
from textual.containers import Horizontal
from textual.binding import Binding
import widgets.pomo_state as pomo_state


def _timer_bar(remaining: float, total: float, width: int = 20) -> str:
    if total <= 0:
        return ""
    ratio = max(0.0, remaining / total)
    filled = int(ratio * width)
    color = "#4ade80" if ratio > 0.5 else ("#f87171" if ratio <= 0.2 else "#fbbf24")
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
        Binding("s", "start_stop", "Start/Stop", show=False),
        Binding("r", "reset",      "Reset",      show=False),
        Binding("e", "edit",       "Set Time",   show=False),
        Binding("p", "reset_pomo", "Reset Log",  show=False),
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
    #cd-body {
        height: 1fr;
    }
    #cd-timer {
        width: 1fr;
        height: 100%;
        padding: 1 2;
        content-align: center middle;
    }
    #cd-pomo {
        width: 26;
        height: 100%;
        padding: 1 2;
        border-left: solid #2a2a2a;
        content-align: left top;
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

    def compose(self) -> ComposeResult:
        with Horizontal(id="cd-body"):
            yield Static(id="cd-timer")
            yield Static(id="cd-pomo")
        yield Input(
            placeholder="e.g. 1:30  or  90  (h:mm or minutes) — Enter to set",
            id="cd-input",
        )

    def on_mount(self) -> None:
        self.set_interval(0.5, self._tick)
        self._refresh_display()

    # ── Pomodoro panel ────────────────────────────────────────────────────

    def _pomo_content(self) -> str:
        work, brk, work_n = pomo_state.totals()
        cur       = pomo_state.current_type()
        cur_start = pomo_state.current_session_start()
        cur_label = "[#4ade80]WORK[/]" if cur == "work" else "[#f87171]BREAK[/]"
        cur_time  = _fmt(time.time() - cur_start)

        return (
            "[bold #888888]POMODORO[/]\n\n"
            f"[#4ade80]WORK [/]  {_fmt(work)}\n"
            f"[#666666]{work_n} sessions[/]\n\n"
            f"[#f87171]BREAK[/]  {_fmt(brk)}\n\n"
            f"[#888888]now:[/] {cur_label} {cur_time}\n\n"
            "[#444444]p = reset log[/]"
        )

    # ── Timer core ────────────────────────────────────────────────────────

    def _tick(self) -> None:
        pomo_state.check_day_reset()
        if self._running and self._remaining > 0:
            now = time.monotonic()
            elapsed = now - self._last_tick
            self._last_tick = now
            self._remaining = max(0.0, self._remaining - elapsed)
            if self._remaining <= 0:
                self._running = False
                pomo_state.open_session("break")
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

        self.query_one("#cd-timer", Static).update(
            f"[bold #888888]TIMER[/]\n\n"
            f"{status}\n\n"
            f"{time_str}"
            f"{bar_str}\n\n"
            "[#444444]s=start/stop  r=reset  e=edit[/]"
        )
        self.query_one("#cd-pomo", Static).update(self._pomo_content())

    # ── Actions ───────────────────────────────────────────────────────────

    def action_start_stop(self) -> None:
        if self._total <= 0 or self._remaining <= 0:
            return
        self._running = not self._running
        if self._running:
            self._last_tick = time.monotonic()
            pomo_state.open_session("work")
        else:
            pomo_state.open_session("break")
        self._refresh_display()

    def action_reset(self) -> None:
        if self._running:
            pomo_state.open_session("break")
        self._remaining = self._total
        self._running = False
        self._refresh_display()

    def action_reset_pomo(self) -> None:
        pomo_state.reset()
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
                pomo_state.open_session("break")
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
