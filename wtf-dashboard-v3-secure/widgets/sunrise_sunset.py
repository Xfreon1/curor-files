import httpx
from datetime import datetime, timezone
from textual.widgets import Static
from config import LAT, LON


class SunriseSunsetWidget(Static):
    """Shows sunrise, sunset, and day length for configured coordinates."""

    DEFAULT_CSS = """
    SunriseSunsetWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 1 2;
    }
    SunriseSunsetWidget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update("[bold #888888]SUNRISE / SUNSET[/]\n\n[#666666]Loading...[/]")
        self.set_interval(3600, self.refresh_data)
        self.run_worker(self._fetch, thread=True)

    def refresh_data(self) -> None:
        self.run_worker(self._fetch, thread=True)

    def _fetch(self) -> None:
        try:
            url = (
                f"https://api.sunrise-sunset.org/json"
                f"?lat={LAT}&lng={LON}&formatted=0"
            )
            r = httpx.get(url, timeout=10)
            d = r.json()

            if d.get("status") != "OK":
                raise ValueError("API error")

            results = d["results"]

            def parse_utc(s: str) -> datetime:
                return datetime.fromisoformat(s.replace("Z", "+00:00"))

            sunrise_utc = parse_utc(results["sunrise"])
            sunset_utc = parse_utc(results["sunset"])

            # Convert to local time (simple UTC offset from system)
            local_offset = datetime.now().astimezone().utcoffset()
            sunrise_local = sunrise_utc + local_offset
            sunset_local = sunset_utc + local_offset

            day_seconds = int(results["day_length"])
            hours = day_seconds // 3600
            minutes = (day_seconds % 3600) // 60

            text = (
                f"[bold #888888]SUNRISE / SUNSET[/]\n\n"
                f"[#fbbf24]↑[/] [white]{sunrise_local.strftime('%H:%M')}[/]\n"
                f"[#888888]↓[/] [white]{sunset_local.strftime('%H:%M')}[/]\n"
                f"[#666666]Day:[/] [white]{hours}h {minutes}m[/]"
            )
            self.app.call_from_thread(self.update, text)
        except Exception as e:
            self.app.call_from_thread(
                self.update,
                f"[bold #888888]SUNRISE / SUNSET[/]\n\n[#f87171]Error: {e}[/]"
            )
