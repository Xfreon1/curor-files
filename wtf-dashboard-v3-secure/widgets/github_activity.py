import httpx
from textual.widgets import Static
from config import GITHUB_USERNAME, GITHUB_TOKEN


_EVENT_ICONS = {
    "PushEvent":                "⬆ Pushed",
    "PullRequestEvent":         "⎇ PR",
    "IssuesEvent":              "◎ Issue",
    "WatchEvent":               "★ Starred",
    "ForkEvent":                "⑂ Forked",
    "CreateEvent":              "+ Created",
    "DeleteEvent":              "- Deleted",
    "IssueCommentEvent":        "💬 Comment",
    "PullRequestReviewEvent":   "✔ Reviewed",
    "ReleaseEvent":             "⬛ Released",
}


def _time_ago(created_at: str) -> str:
    from datetime import datetime, timezone
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"
    except Exception:
        return ""


def _describe_event(event: dict) -> str:
    etype = event.get("type", "Event")
    repo = event.get("repo", {}).get("name", "?")
    payload = event.get("payload", {})
    icon = _EVENT_ICONS.get(etype, "· Event")

    detail = ""
    if etype == "PushEvent":
        count = len(payload.get("commits", []))
        detail = f"{count} commit{'s' if count != 1 else ''}"
    elif etype == "PullRequestEvent":
        action = payload.get("action", "")
        pr = payload.get("pull_request", {})
        num = pr.get("number", "")
        detail = f"#{num} {action}"
    elif etype == "IssuesEvent":
        action = payload.get("action", "")
        issue = payload.get("issue", {})
        num = issue.get("number", "")
        detail = f"#{num} {action}"
    elif etype == "CreateEvent":
        ref_type = payload.get("ref_type", "")
        ref = payload.get("ref") or ""
        detail = f"{ref_type} {ref}".strip()

    if detail:
        return f"{icon} {detail}"
    return icon


class GitHubActivityWidget(Static):
    """Recent GitHub activity for configured user."""

    DEFAULT_CSS = """
    GitHubActivityWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 1 2;
        overflow: auto;
    }
    GitHubActivityWidget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update("[bold #888888]GITHUB ACTIVITY[/]\n\n[#666666]Loading...[/]")
        self.set_interval(120, self.refresh_data)
        self.run_worker(self._fetch, thread=True)

    def refresh_data(self) -> None:
        self.run_worker(self._fetch, thread=True)

    def _fetch(self) -> None:
        if not GITHUB_USERNAME:
            self.app.call_from_thread(
                self.update,
                "[bold #888888]GITHUB ACTIVITY[/]\n\n"
                "[#666666]Set GITHUB_USERNAME in config.py[/]"
            )
            return

        try:
            headers = {"Accept": "application/vnd.github+json"}
            if GITHUB_TOKEN:
                headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

            url = f"https://api.github.com/users/{GITHUB_USERNAME}/events?per_page=10"
            r = httpx.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            events = r.json()

            lines = [f"[bold #888888]GITHUB ACTIVITY[/]  [#666666]{GITHUB_USERNAME}[/]\n"]
            for event in events[:8]:
                repo = event.get("repo", {}).get("name", "?")
                repo_short = repo.split("/")[-1] if "/" in repo else repo
                desc = _describe_event(event)
                age = _time_ago(event.get("created_at", ""))

                lines.append(
                    f"[#666666]{repo:<28}[/] [white]{desc}[/] [#444444]{age}[/]"
                )

            self.app.call_from_thread(self.update, "\n".join(lines))
        except Exception as e:
            self.app.call_from_thread(
                self.update,
                f"[bold #888888]GITHUB ACTIVITY[/]\n\n[#f87171]Error: {e}[/]"
            )
