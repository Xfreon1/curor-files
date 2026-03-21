import httpx
from textual.widgets import Static


_AQI_LABELS = [
    (50,  "Good",            "#4ade80"),
    (100, "Moderate",        "#fbbf24"),
    (150, "Unhealthy (Sens)","#fb923c"),
    (200, "Unhealthy",       "#f87171"),
    (300, "Very Unhealthy",  "#c084fc"),
    (999, "Hazardous",       "#ef4444"),
]


def _aqi_label(pm25: float) -> tuple[str, str]:
    """Return (label, color) for a PM2.5 value using US AQI breakpoints."""
    # Simple linear PM2.5 → AQI approximation
    aqi = pm25 * 4.0  # rough: 25 µg/m³ ≈ AQI 100
    for threshold, label, color in _AQI_LABELS:
        if aqi <= threshold:
            return label, color
    return "Hazardous", "#ef4444"


class AirQualityWidget(Static):
    """Air quality from OpenAQ for configured city."""

    DEFAULT_CSS = """
    AirQualityWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 1 2;
    }
    AirQualityWidget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update("[bold #888888]AIR QUALITY[/]\n\n[#666666]Loading...[/]")
        self.set_interval(600, self.refresh_data)
        self.run_worker(self._fetch, thread=True)

    def refresh_data(self) -> None:
        self.run_worker(self._fetch, thread=True)

    def _fetch(self) -> None:
        try:
            # Get latest measurements for Riga
            url = "https://api.openaq.org/v3/locations?city=Riga&country_id=LV&limit=5"
            headers = {"Accept": "application/json"}
            r = httpx.get(url, headers=headers, timeout=15)
            data = r.json()

            results = data.get("results", [])
            if not results:
                raise ValueError("No locations found")

            location_id = results[0]["id"]
            city_name = results[0].get("locality") or results[0].get("name", "Riga")

            # Get latest measurements
            meas_url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
            mr = httpx.get(meas_url, headers=headers, timeout=15)
            meas_data = mr.json()

            sensors = meas_data.get("results", [])
            pm25 = None
            pm10 = None
            for s in sensors:
                param = (s.get("parameter") or {}).get("name", "")
                value = s.get("value")
                if param == "pm25" and value is not None:
                    pm25 = float(value)
                elif param == "pm10" and value is not None:
                    pm10 = float(value)

            if pm25 is None:
                raise ValueError("No PM2.5 data")

            label, color = _aqi_label(pm25)
            pm10_str = f"{pm10:.1f}" if pm10 is not None else "N/A"

            text = (
                f"[bold #888888]AIR QUALITY[/]\n\n"
                f"[#666666]AQI :[/]  [{color}]{label}[/]\n"
                f"[#666666]PM2.5:[/] [white]{pm25:.1f} µg/m³[/]\n"
                f"[#666666]PM10 :[/] [white]{pm10_str} µg/m³[/]\n"
                f"[#666666]City :[/] [white]{city_name[:20]}, LV[/]"
            )
            self.app.call_from_thread(self.update, text)
        except Exception as e:
            self.app.call_from_thread(
                self.update,
                f"[bold #888888]AIR QUALITY[/]\n\n[#f87171]Error: {e}[/]"
            )
