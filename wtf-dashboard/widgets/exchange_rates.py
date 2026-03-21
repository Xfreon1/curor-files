import httpx
from textual.widgets import Static
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import EXCHANGE_BASE, EXCHANGE_CURRENCIES


class ExchangeRatesWidget(Static):
    """Live exchange rates from exchangerate-api.com (free tier)."""

    DEFAULT_CSS = """
    ExchangeRatesWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 1 2;
        overflow: auto;
    }
    ExchangeRatesWidget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update("[bold #888888]EXCHANGE RATES[/]\n\n[#666666]Loading...[/]")
        self.set_interval(1800, self.refresh_data)
        self.run_worker(self._fetch, thread=True)

    def refresh_data(self) -> None:
        self.run_worker(self._fetch, thread=True)

    def _fetch(self) -> None:
        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{EXCHANGE_BASE}"
            r = httpx.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            rates = data.get("rates", {})

            lines = [f"[bold #888888]EXCHANGE RATES[/]  [#666666]{EXCHANGE_BASE}[/]\n"]
            for currency in EXCHANGE_CURRENCIES:
                rate = rates.get(currency)
                if rate is not None:
                    lines.append(
                        f"[#666666]{EXCHANGE_BASE} → {currency:<4}[/]  [bold white]{rate:>10.4f}[/]"
                    )
                else:
                    lines.append(f"[#666666]{EXCHANGE_BASE} → {currency:<4}[/]  [#444444]N/A[/]")

            self.app.call_from_thread(self.update, "\n".join(lines))
        except Exception as e:
            self.app.call_from_thread(
                self.update,
                f"[bold #888888]EXCHANGE RATES[/]\n\n[#f87171]Error: {e}[/]"
            )
