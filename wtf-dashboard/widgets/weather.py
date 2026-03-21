import httpx
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static
from textual.reactive import reactive
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import WEATHER_API_KEY, WEATHER_CITIES


class WeatherWidget(Static):
    """Displays weather for configured cities."""

    DEFAULT_CSS = """
    WeatherWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 1 2;
        overflow: auto;
    }
    WeatherWidget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update("[#888888]WEATHER[/]\n\n[#666666]Loading...[/]")
        self.set_interval(600, self.refresh_weather)
        self.run_worker(self._fetch_all, thread=True)

    def refresh_weather(self) -> None:
        self.run_worker(self._fetch_all, thread=True)

    def _fetch_all(self) -> None:
        if WEATHER_API_KEY == "YOUR_KEY_HERE":
            self.app.call_from_thread(
                self.update,
                "[#888888]WEATHER[/]\n\n[#f87171]No API key set.[/]\n[#666666]Edit config.py[/]"
            )
            return

        lines = ["[bold #888888]WEATHER[/]\n"]
        for city in WEATHER_CITIES:
            try:
                url = (
                    f"https://api.openweathermap.org/data/2.5/weather"
                    f"?q={city}&appid={WEATHER_API_KEY}&units=metric"
                )
                r = httpx.get(url, timeout=10)
                d = r.json()
                name = d.get("name", city.split(",")[0])[:12]
                temp = d["main"]["temp"]
                desc = d["weather"][0]["description"].capitalize()[:12]
                humidity = d["main"]["humidity"]
                wind = d["wind"]["speed"]
                lines.append(
                    f"[bold white]{name:<12}[/] "
                    f"[bold #4ade80]{temp:>5.1f}°[/] "
                    f"[#666666]H:[/][white]{humidity}%[/] "
                    f"[#666666]W:[/][white]{wind:.1f}[/] "
                    f"[#888888]{desc}[/]"
                )
            except Exception as e:
                lines.append(f"[#f87171]{city.split(',')[0]}: error[/]")

        self.app.call_from_thread(self.update, "\n".join(lines))
