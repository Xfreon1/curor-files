from textual.widget import Widget
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Horizontal
from datetime import datetime
from zoneinfo import ZoneInfo
from config import WORLD_CLOCKS


class SingleClock(Static):
    """Displays one city clock."""

    DEFAULT_CSS = """
    SingleClock {
        width: 1fr;
        height: 5;
        content-align: center middle;
        border: round #2a2a2a;
        padding: 0 1;
    }
    SingleClock:focus {
        border: round #4ade80;
    }
    """

    def __init__(self, tz: str, label: str, **kwargs):
        super().__init__(**kwargs)
        self.tz = tz
        self.label = label

    def on_mount(self) -> None:
        self.set_interval(1, self.refresh_time)
        self.refresh_time()

    def refresh_time(self) -> None:
        now = datetime.now(ZoneInfo(self.tz))
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%a %d %b")
        self.update(
            f"[bold #5fd787]{self.label}[/]\n"
            f"[bold white]{time_str}[/]\n"
            f"[#666666]{date_str}[/]"
        )


class ClocksWidget(Horizontal):
    """Row of 9 world clocks."""

    DEFAULT_CSS = """
    ClocksWidget {
        height: 7;
        width: 100%;
        background: #0f0f0f;
    }
    """

    def compose(self) -> ComposeResult:
        for tz, label in WORLD_CLOCKS:
            yield SingleClock(tz, label)
