import httpx
from textual.widgets import Static
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import NEWS_FILTER_KEYWORDS


HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def _highlight_title(title: str) -> str:
    """Return amber-highlighted title if any keyword matches, else white."""
    title_lower = title.lower()
    for kw in NEWS_FILTER_KEYWORDS:
        if kw.lower() in title_lower:
            return f"[bold #fbbf24]{title}[/]"
    return f"[white]{title}[/]"


class HackerNewsWidget(Static):
    """Top 15 Hacker News stories."""

    DEFAULT_CSS = """
    HackerNewsWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 1 2;
        overflow: auto;
    }
    HackerNewsWidget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update("[bold #888888]HACKER NEWS[/]\n\n[#666666]Loading...[/]")
        self.set_interval(300, self.refresh_data)
        self.run_worker(self._fetch, thread=True)

    def refresh_data(self) -> None:
        self.run_worker(self._fetch, thread=True)

    def _fetch(self) -> None:
        try:
            r = httpx.get(HN_TOP_URL, timeout=10)
            ids = r.json()[:15]

            stories = []
            for story_id in ids:
                try:
                    sr = httpx.get(HN_ITEM_URL.format(story_id), timeout=8)
                    stories.append(sr.json())
                except Exception:
                    pass

            lines = ["[bold #888888]HACKER NEWS[/]  [#666666]top 15[/]\n"]
            for i, s in enumerate(stories, 1):
                title = (s.get("title") or "")[:55]
                score = s.get("score", 0)
                comments = s.get("descendants", 0)
                score_color = "#4ade80" if score > 200 else "#888888"
                lines.append(
                    f"[#666666]{i:>2}.[/] {_highlight_title(title)}\n"
                    f"    [{score_color}]{score}pts[/] [#666666]· {comments} comments[/]"
                )

            self.app.call_from_thread(self.update, "\n".join(lines))
        except Exception as e:
            self.app.call_from_thread(
                self.update,
                f"[bold #888888]HACKER NEWS[/]\n\n[#f87171]Error: {e}[/]"
            )
