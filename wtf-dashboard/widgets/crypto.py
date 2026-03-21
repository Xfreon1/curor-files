import httpx
from textual.widgets import Static
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import CRYPTO_IDS, CRYPTO_SYMBOLS


COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids={ids}&vs_currencies=usd&include_24hr_change=true"
)


class CryptoWidget(Static):
    """Top 10 crypto prices from CoinGecko (no key needed)."""

    DEFAULT_CSS = """
    CryptoWidget {
        height: 1fr;
        border: round #2a2a2a;
        padding: 1 2;
        overflow: auto;
    }
    CryptoWidget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update("[bold #888888]CRYPTO[/]\n\n[#666666]Loading...[/]")
        self.set_interval(30, self.refresh_data)
        self.run_worker(self._fetch, thread=True)

    def refresh_data(self) -> None:
        self.run_worker(self._fetch, thread=True)

    def _fetch(self) -> None:
        try:
            url = COINGECKO_URL.format(ids=",".join(CRYPTO_IDS))
            r = httpx.get(url, timeout=15)
            data = r.json()

            lines = ["[bold #888888]CRYPTO[/]  [#666666](CoinGecko)[/]\n"]
            lines.append(f"[#666666]{'COIN':<8} {'PRICE (USD)':>14} {'24h %':>8}[/]")
            lines.append("[#2a2a2a]" + "─" * 34 + "[/]")

            for coin_id in CRYPTO_IDS:
                sym = CRYPTO_SYMBOLS.get(coin_id, coin_id.upper())
                info = data.get(coin_id, {})
                price = info.get("usd", 0)
                change = info.get("usd_24h_change", 0) or 0
                color = "#4ade80" if change >= 0 else "#f87171"
                sign = "+" if change >= 0 else ""

                # Format price nicely
                if price >= 1000:
                    price_str = f"${price:>12,.2f}"
                elif price >= 1:
                    price_str = f"${price:>12.4f}"
                else:
                    price_str = f"${price:>12.6f}"

                lines.append(
                    f"[white]{sym:<8}[/] "
                    f"[bold white]{price_str}[/] "
                    f"[{color}]{sign}{change:>+6.2f}%[/]"
                )

            self.app.call_from_thread(self.update, "\n".join(lines))
        except Exception as e:
            self.app.call_from_thread(
                self.update,
                f"[bold #888888]CRYPTO[/]\n\n[#f87171]Error: {e}[/]"
            )
