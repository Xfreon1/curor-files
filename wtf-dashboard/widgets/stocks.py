import yfinance as yf
from textual.widgets import Static
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import INDEX_TICKERS, INDEX_NAMES, SP500_TICKERS


def _fetch_tickers(tickers: list[str]) -> list[dict]:
    results = []
    for t in tickers:
        try:
            info = yf.Ticker(t).fast_info
            price = info.last_price or 0
            prev = info.previous_close or price
            change = price - prev
            pct = (change / prev * 100) if prev else 0
            results.append({
                "ticker": t,
                "price": price,
                "change": change,
                "pct": pct,
            })
        except Exception:
            results.append({"ticker": t, "price": 0, "change": 0, "pct": 0})
    return results


def _fmt_row(ticker: str, price: float, change: float, pct: float, col_width: int = 10) -> str:
    color = "#4ade80" if change >= 0 else "#f87171"
    sign = "+" if change >= 0 else ""
    name = ticker[:col_width].ljust(col_width)
    return (
        f"[white]{name}[/] "
        f"[bold white]{price:>10.2f}[/] "
        f"[{color}]{sign}{change:>+8.2f}  {sign}{pct:>+6.2f}%[/]"
    )


class IndicesWidget(Static):
    """S&P 500, DJIA, NASDAQ-100 indices."""

    DEFAULT_CSS = """
    IndicesWidget {
        height: 1fr;
        border: round #2a2a2a;
        padding: 1 2;
        overflow: auto;
    }
    IndicesWidget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update("[bold #888888]INDICES[/]\n\n[#666666]Loading...[/]")
        self.set_interval(60, self.refresh_data)
        self.run_worker(self._fetch, thread=True)

    def refresh_data(self) -> None:
        self.run_worker(self._fetch, thread=True)

    def _fetch(self) -> None:
        data = _fetch_tickers(INDEX_TICKERS)
        lines = ["[bold #888888]INDICES[/]\n"]
        lines.append(f"[#666666]{'TICKER':<12} {'PRICE':>10} {'CHANGE':>10} {'%':>8}[/]")
        lines.append("[#2a2a2a]" + "─" * 46 + "[/]")
        for d in data:
            name = INDEX_NAMES.get(d["ticker"], d["ticker"])
            lines.append(_fmt_row(name, d["price"], d["change"], d["pct"], col_width=12))
        self.app.call_from_thread(self.update, "\n".join(lines))


class SP500Widget(Static):
    """Top 10 S&P 500 stocks."""

    DEFAULT_CSS = """
    SP500Widget {
        height: 1fr;
        border: round #2a2a2a;
        padding: 1 2;
        overflow: auto;
    }
    SP500Widget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update("[bold #888888]TOP 10 S&P 500 STOCKS[/]\n\n[#666666]Loading...[/]")
        self.set_interval(60, self.refresh_data)
        self.run_worker(self._fetch, thread=True)

    def refresh_data(self) -> None:
        self.run_worker(self._fetch, thread=True)

    def _fetch(self) -> None:
        data = _fetch_tickers(SP500_TICKERS)
        lines = ["[bold #888888]TOP 10 S&P 500 STOCKS[/]\n"]
        lines.append(f"[#666666]{'TICKER':<10} {'PRICE':>10} {'CHANGE':>10} {'%':>8}[/]")
        lines.append("[#2a2a2a]" + "─" * 44 + "[/]")
        for d in data:
            lines.append(_fmt_row(d["ticker"], d["price"], d["change"], d["pct"]))
        self.app.call_from_thread(self.update, "\n".join(lines))
