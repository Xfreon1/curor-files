import httpx
import base64
from datetime import datetime, timezone
from textual.widgets import Static
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import TOGGL_API_TOKEN


def _format_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}h {m:02d}m"
    elif m > 0:
        return f"{m}m {s:02d}s"
    else:
        return f"{s}s"


class TogglTimerWidget(Static):
    """Shows active Toggl Track timer."""

    DEFAULT_CSS = """
    TogglTimerWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 1 2;
        content-align: left top;
    }
    TogglTimerWidget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update("[bold #888888]TOGGL TIMER[/]\n\n[#666666]Loading...[/]")
        self.set_interval(10, self.refresh_data)
        self.run_worker(self._fetch, thread=True)

    def refresh_data(self) -> None:
        self.run_worker(self._fetch, thread=True)

    def _fetch(self) -> None:
        if not TOGGL_API_TOKEN:
            self.app.call_from_thread(
                self.update,
                "[bold #888888]TOGGL TIMER[/]\n\n"
                "[#666666]Set TOGGL_API_TOKEN in config.py[/]"
            )
            return

        try:
            credentials = base64.b64encode(
                f"{TOGGL_API_TOKEN}:api_token".encode()
            ).decode()
            headers = {"Authorization": f"Basic {credentials}"}
            url = "https://api.track.toggl.com/api/v9/me/time_entries/current"
            r = httpx.get(url, headers=headers, timeout=10)
            r.raise_for_status()

            entry = r.json()
            if not entry:
                text = (
                    "[bold #888888]TOGGL TIMER[/]\n\n"
                    "[#666666]● No active timer[/]"
                )
                self.app.call_from_thread(self.update, text)
                return

            # Duration in Toggl API is negative while running (start as negative unix ts)
            start_str = entry.get("start", "")
            project = entry.get("project_name") or entry.get("pid") or "No project"
            description = entry.get("description") or "No description"

            if start_str:
                start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                elapsed = int((datetime.now(timezone.utc) - start_dt).total_seconds())
                duration_str = _format_duration(elapsed)
            else:
                duration_str = "?"

            text = (
                f"[bold #888888]TOGGL TIMER[/]\n\n"
                f"[bold #4ade80]● RUNNING[/]  "
                f"[#666666]Project:[/] [white]{str(project)[:24]}[/]  "
                f"[#666666]Task:[/] [white]{description[:28]}[/]\n"
                f"[#666666]Duration:[/] [bold white]{duration_str}[/]"
            )
            self.app.call_from_thread(self.update, text)
        except Exception as e:
            self.app.call_from_thread(
                self.update,
                f"[bold #888888]TOGGL TIMER[/]\n\n[#f87171]Error: {e}[/]"
            )
