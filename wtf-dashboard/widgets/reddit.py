import httpx
from textual.widgets import Static
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import REDDIT_SUBS, NEWS_FILTER_KEYWORDS


def _highlight_title(title: str) -> str:
    """Return amber-highlighted title if any keyword matches, else white."""
    title_lower = title.lower()
    for kw in NEWS_FILTER_KEYWORDS:
        if kw.lower() in title_lower:
            return f"[bold #fbbf24]{title}[/]"
    return f"[white]{title}[/]"


REDDIT_URL = "https://www.reddit.com/r/{sub}/hot.json?limit=8"
HEADERS = {"User-Agent": "wtf-dashboard/1.0"}


class RedditWidget(Static):
    """Hot posts from configured subreddits."""

    DEFAULT_CSS = """
    RedditWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 1 2;
        overflow: auto;
    }
    RedditWidget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update("[bold #888888]REDDIT[/]\n\n[#666666]Loading...[/]")
        self.set_interval(300, self.refresh_data)
        self.run_worker(self._fetch, thread=True)

    def refresh_data(self) -> None:
        self.run_worker(self._fetch, thread=True)

    def _fetch(self) -> None:
        lines = []
        for sub in REDDIT_SUBS:
            try:
                r = httpx.get(
                    REDDIT_URL.format(sub=sub),
                    headers=HEADERS,
                    timeout=10,
                    follow_redirects=True,
                )
                data = r.json()
                posts = data["data"]["children"]
                lines.append(f"[bold #888888]r/{sub}[/]")
                for i, post in enumerate(posts[:8], 1):
                    d = post["data"]
                    title = (d.get("title") or "")[:52]
                    score = d.get("score", 0)
                    comments = d.get("num_comments", 0)
                    lines.append(
                        f"[#666666]{i}.[/] {_highlight_title(title)}\n"
                        f"   [#4ade80]{score}↑[/] [#666666]{comments} comments[/]"
                    )
                lines.append("")
            except Exception as e:
                lines.append(f"[bold #888888]r/{sub}[/]\n[#f87171]{e}[/]\n")

        subs_str = " + ".join(f"r/{s}" for s in REDDIT_SUBS)
        header = f"[bold #888888]REDDIT[/]  [#666666]{subs_str}[/]\n\n"
        self.app.call_from_thread(self.update, header + "\n".join(lines))
