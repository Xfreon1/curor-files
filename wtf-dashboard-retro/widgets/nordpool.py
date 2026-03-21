import httpx
from datetime import datetime, timezone, timedelta
from textual.widgets import Static


class NordpoolWidget(Static):
    """NordPool electricity prices for Latvia from Elering API."""

    DEFAULT_CSS = """
    NordpoolWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 1 2;
        overflow: auto;
    }
    NordpoolWidget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update("[bold #888888]NORDPOOL ELECTRICITY (LV)[/]\n\n[#666666]Loading...[/]")
        self.set_interval(1800, self.refresh_data)
        self.run_worker(self._fetch, thread=True)

    def refresh_data(self) -> None:
        self.run_worker(self._fetch, thread=True)

    def _fetch(self) -> None:
        try:
            today = datetime.now(timezone.utc).date()
            start = f"{today}T00:00:00Z"
            end = f"{today}T23:59:59Z"
            url = (
                f"https://dashboard.elering.ee/api/nps/price"
                f"?start={start}&end={end}"
            )
            r = httpx.get(url, timeout=15)
            data = r.json()

            # Elering returns {"data": {"ee": [...], "lv": [...], ...}}
            lv_prices = data.get("data", {}).get("lv", [])
            if not lv_prices:
                raise ValueError("No LV price data")

            # Each entry: {"timestamp": unix_seconds, "price": EUR/MWh}
            now_utc = datetime.now(timezone.utc)
            current_hour_ts = now_utc.replace(minute=0, second=0, microsecond=0)
            next_hour_ts = current_hour_ts + timedelta(hours=1)

            current_price = None
            next_price = None
            prices_kwh = []

            for entry in lv_prices:
                ts = entry.get("timestamp", 0)
                price_mwh = entry.get("price", 0)
                price_kwh = price_mwh / 1000.0
                prices_kwh.append((ts, price_kwh))

                entry_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                if entry_dt == current_hour_ts:
                    current_price = price_kwh
                elif entry_dt == next_hour_ts:
                    next_price = price_kwh

            if not prices_kwh:
                raise ValueError("Empty price list")

            avg = sum(p for _, p in prices_kwh) / len(prices_kwh)
            min_ts, min_price = min(prices_kwh, key=lambda x: x[1])
            max_ts, max_price = max(prices_kwh, key=lambda x: x[1])

            def fmt_hour(ts: int) -> str:
                return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M")

            def price_color(p: float) -> str:
                if p < 0.05:
                    return "#4ade80"
                elif p < 0.15:
                    return "#fbbf24"
                else:
                    return "#f87171"

            cur_str = f"[{price_color(current_price)}]{current_price:.3f} €/kWh[/]" if current_price is not None else "[#666666]N/A[/]"
            nxt_str = f"[{price_color(next_price)}]{next_price:.3f} €/kWh[/]  [#444444]({next_hour_ts.strftime('%H:%M')})[/]" if next_price is not None else "[#666666]N/A[/]"

            text = (
                f"[bold #888888]NORDPOOL ELECTRICITY (LV)[/]\n\n"
                f"[#666666]Now :[/]  {cur_str}\n"
                f"[#666666]Avg :[/]  [white]{avg:.3f} €/kWh[/]\n"
                f"[#666666]Min :[/]  [#4ade80]{min_price:.3f} €/kWh[/]  [#444444]{fmt_hour(min_ts)}[/]\n"
                f"[#666666]Max :[/]  [#f87171]{max_price:.3f} €/kWh[/]  [#444444]{fmt_hour(max_ts)}[/]\n"
                f"[#666666]Next:[/]  {nxt_str}"
            )
            self.app.call_from_thread(self.update, text)
        except Exception as e:
            self.app.call_from_thread(
                self.update,
                f"[bold #888888]NORDPOOL ELECTRICITY (LV)[/]\n\n[#f87171]Error: {e}[/]"
            )
