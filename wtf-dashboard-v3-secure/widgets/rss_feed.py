import feedparser
from textual.widgets import Static
from config import RSS_URL


class RSSWidget(Static):
    """RSS feed reader."""

    DEFAULT_CSS = """
    RSSWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 1 2;
        overflow: auto;
    }
    RSSWidget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update("[bold #888888]RSS FEED[/]\n\n[#666666]Loading...[/]")
        self.set_interval(300, self.refresh_data)
        self.run_worker(self._fetch, thread=True)

    def refresh_data(self) -> None:
        self.run_worker(self._fetch, thread=True)

    def _fetch(self) -> None:
        try:
            feed = feedparser.parse(RSS_URL)
            title = feed.feed.get("title", RSS_URL)[:40]
            entries = feed.entries[:12]

            lines = [f"[bold #888888]RSS[/]  [#666666]{title}[/]\n"]
            for i, entry in enumerate(entries, 1):
                etitle = (entry.get("title") or "")[:55]
                lines.append(f"[#666666]{i:>2}.[/] [white]{etitle}[/]")

            if not entries:
                lines.append("[#f87171]No entries found.[/]")

            self.app.call_from_thread(self.update, "\n".join(lines))
        except Exception as e:
            self.app.call_from_thread(
                self.update,
                f"[bold #888888]RSS FEED[/]\n\n[#f87171]Error: {e}[/]"
            )
