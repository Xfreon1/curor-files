import yfinance as yf
from textual.widgets import Static
from config import INDEX_TICKERS, INDEX_NAMES, SP500_TICKERS


def _fetch_tickers(tickers: list[str]) -> list[dict]:
    results = []
    for t in tickers:
        try:
            info = yf.Ticker(t).fast_info
            price = getattr(info, "last_price", 0) or 0
            prev = getattr(info, "previous_close", 0) or price
            change = price - prev
            pct = (change / prev * 100) if prev else 0
            results.append({
                "ticker": t,
                "price": price,
                "change": change,
                "pct": pct,
            })
        except (AttributeError, TypeError, ValueError):
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


class StockTableWidget(Static):
    """Generic stock/index table widget."""

    DEFAULT_CSS = """
    StockTableWidget {
        height: 1fr;
        border: round #2a2a2a;
        padding: 1 2;
        overflow: auto;
    }
    StockTableWidget:focus {
        border: round #4ade80;
    }
    """

    def __init__(self, title: str, tickers: list[str],
                 name_map: dict[str, str] | None = None,
                 col_width: int = 10, refresh_seconds: int = 300, **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self._tickers = tickers
        self._name_map = name_map or {}
        self._col_width = col_width
        self._refresh_seconds = refresh_seconds

    def on_mount(self) -> None:
        self.update(f"[bold #888888]{self._title}[/]\n\n[#666666]Loading...[/]")
        self.set_interval(self._refresh_seconds, self.refresh_data)
        self.run_worker(self._fetch, thread=True)

    def refresh_data(self) -> None:
        self.run_worker(self._fetch, thread=True)

    def _fetch(self) -> None:
        data = _fetch_tickers(self._tickers)
        lines = [f"[bold #888888]{self._title}[/]\n"]
        lines.append(f"[#666666]{'TICKER':<{self._col_width}} {'PRICE':>10} {'CHANGE':>10} {'%':>8}[/]")
        lines.append("[#2a2a2a]" + "─" * (self._col_width + 32) + "[/]")
        for d in data:
            name = self._name_map.get(d["ticker"], d["ticker"])
            lines.append(_fmt_row(name, d["price"], d["change"], d["pct"], col_width=self._col_width))
        self.app.call_from_thread(self.update, "\n".join(lines))


# Backward-compatible aliases
def IndicesWidget(**kwargs):
    return StockTableWidget("INDICES", INDEX_TICKERS, name_map=INDEX_NAMES, col_width=12, **kwargs)


def SP500Widget(**kwargs):
    return StockTableWidget("TOP 10 S&P 500 STOCKS", SP500_TICKERS, col_width=10, **kwargs)
