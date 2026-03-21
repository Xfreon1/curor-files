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


class CountdownWidget(Widget):
    """Countdown timer with hours/minutes input and a draining progress bar."""

    can_focus = True

    BINDINGS = [
        Binding("s", "start_stop", "Start/Stop", show=False),
        Binding("r", "reset",      "Reset",      show=False),
        Binding("e", "edit",       "Set Time",   show=False),
    ]

    DEFAULT_CSS = """
    CountdownWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 0;
        overflow: hidden;
        content-align: center middle;
    }
    CountdownWidget:focus, CountdownWidget:focus-within {
        border: round #4ade80;
    }
    #cd-display {
        height: 1fr;
        padding: 1 2;
        content-align: center middle;
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
        self._total: float = 0.0       # total seconds set
        self._remaining: float = 0.0   # seconds left
        self._running: bool = False
        self._last_tick: float = 0.0

    def compose(self) -> ComposeResult:
        yield Static(id="cd-display")
        yield Input(placeholder="e.g. 1:30  or  90  (h:mm or minutes) — Enter to set", id="cd-input")

    def on_mount(self) -> None:
        self.set_interval(0.5, self._tick)
        self._refresh_display()

    def _tick(self) -> None:
        if not self._running or self._remaining <= 0:
            return
        now = time.monotonic()
        elapsed = now - self._last_tick
        self._last_tick = now
        self._remaining = max(0.0, self._remaining - elapsed)
        if self._remaining <= 0:
            self._running = False
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

        lines = (
            f"[bold #888888]TIMER[/]\n\n"
            f"{status}\n\n"
            f"{time_str}"
            f"{bar_str}\n\n"
            f"{hint}"
        )
        self.query_one("#cd-display", Static).update(lines)

    def action_start_stop(self) -> None:
        if self._total <= 0:
            return
        if self._remaining <= 0:
            return
        self._running = not self._running
        if self._running:
            self._last_tick = time.monotonic()
        self._refresh_display()

    def action_reset(self) -> None:
        self._remaining = self._total
        self._running = False
        self._refresh_display()

    def action_edit(self) -> None:
        inp = self.query_one("#cd-input", Input)
        inp.display = True
        inp.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        seconds = self._parse_time(text)
        if seconds and seconds > 0:
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
                # Plain minutes
                return int(parts[0]) * 60
            elif len(parts) == 2:
                # h:mm
                return int(parts[0]) * 3600 + int(parts[1]) * 60
            elif len(parts) == 3:
                # h:mm:ss
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except ValueError:
            return None
