import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from textual.widgets import Static
from config import NEWS_FILTER_KEYWORDS
from widgets.utils import highlight_title


HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"


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
            ids = (r.json() or [])[:15]

            def fetch_one(sid):
                sr = httpx.get(HN_ITEM_URL.format(sid), timeout=8)
                return sid, sr.json()

            results = {}
            with ThreadPoolExecutor(max_workers=5) as pool:
                futures = {pool.submit(fetch_one, sid): sid for sid in ids}
                for future in as_completed(futures):
                    try:
                        sid, story = future.result()
                        results[sid] = story
                    except httpx.HTTPError:
                        pass
            # Preserve original order
            stories = [results[sid] for sid in ids if sid in results]

            lines = ["[bold #888888]HACKER NEWS[/]  [#666666]top 15[/]\n"]
            for i, s in enumerate(stories, 1):
                title = (s.get("title") or "")[:55]
                score = s.get("score", 0)
                comments = s.get("descendants", 0)
                score_color = "#4ade80" if score > 200 else "#888888"
                lines.append(
                    f"[#666666]{i:>2}.[/] {highlight_title(title, NEWS_FILTER_KEYWORDS)}\n"
                    f"    [{score_color}]{score}pts[/] [#666666]· {comments} comments[/]"
                )

            self.app.call_from_thread(self.update, "\n".join(lines))
        except (httpx.HTTPError, KeyError, ValueError) as e:
            self.app.call_from_thread(
                self.update,
                f"[bold #888888]HACKER NEWS[/]\n\n[#f87171]Error: {e}[/]"
            )
