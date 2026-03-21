"""Shared utility functions for dashboard widgets."""


def pct_bar(pct: float, width: int = 14) -> str:
    """Colored percentage bar."""
    filled = int(min(pct, 100) / 100 * width)
    color = pct_color(pct)
    return f"[{color}]{'█' * filled}[/][#2a2a2a]{'░' * (width - filled)}[/]"


def pct_color(pct: float, warn: float = 70, crit: float = 90) -> str:
    """Return color hex based on percentage thresholds."""
    return "#4ade80" if pct < warn else ("#f87171" if pct > crit else "#fbbf24")


def highlight_title(title: str, keywords: list[str]) -> str:
    """Return amber-highlighted title if any keyword matches, else white."""
    title_lower = title.lower()
    for kw in keywords:
        if kw.lower() in title_lower:
            return f"[bold #fbbf24]{title}[/]"
    return f"[white]{title}[/]"


def sanitize_markup(text: str) -> str:
    """Escape Rich markup brackets in user input."""
    return text.replace("[", r"\[")


def fmt_bytes(b: float) -> str:
    """Format bytes/sec for network display."""
    if b >= 1_048_576:
        return f"{b / 1_048_576:6.1f} MB/s"
    elif b >= 1024:
        return f"{b / 1024:6.1f} KB/s"
    return f"{b:6.0f}  B/s"
