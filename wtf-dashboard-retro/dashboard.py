#!/usr/bin/env python3
"""
WTF-Style Terminal Dashboard
Press 1/2/3/4/5 to switch screens. q to quit.
"""
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Static
from textual.screen import Screen

from widgets.clocks import ClocksWidget
from widgets.weather import WeatherWidget
from widgets.system_stats import SystemStatsWidget
from widgets.processes import ProcessesWidget
from widgets.calendar_widget import CalendarWidget
from widgets.todo import TodoWidget
from widgets.countdown import CountdownWidget
from widgets.now_playing import NowPlayingWidget
from widgets.stocks import IndicesWidget, SP500Widget
from widgets.crypto import CryptoWidget
from widgets.hackernews import HackerNewsWidget
from widgets.reddit import RedditWidget
from widgets.rss_feed import RSSWidget
from widgets.command_output import CommandOutputWidget
from widgets.exchange_rates import ExchangeRatesWidget
from widgets.ip_vpn import IpVpnWidget
from widgets.air_quality import AirQualityWidget
from widgets.sunrise_sunset import SunriseSunsetWidget
from widgets.github_activity import GitHubActivityWidget
from widgets.nordpool import NordpoolWidget
from widgets.toggl_timer import TogglTimerWidget
from widgets.day_timeline import DayTimelineWidget


# ─────────────────────────────────────────────
# Screen 1 — MAIN
# ─────────────────────────────────────────────

class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        with Vertical(id="screen-main"):
            yield ClocksWidget(id="clocks-row")
            yield DayTimelineWidget(id="day-timeline")
            with Horizontal(id="main-middle"):
                yield WeatherWidget(id="weather")
                yield SystemStatsWidget(id="system-stats")
                yield ProcessesWidget(id="processes")
                yield CalendarWidget(id="calendar")
            with Horizontal(id="main-bottom"):
                yield TodoWidget(id="todo")
                yield CountdownWidget(id="countdown")
                yield NowPlayingWidget(id="now-playing")


# ─────────────────────────────────────────────
# Screen 2 — MARKETS
# ─────────────────────────────────────────────

class MarketsScreen(Screen):
    def compose(self) -> ComposeResult:
        with Vertical(id="screen-markets"):
            yield IndicesWidget(id="indices")
            yield SP500Widget(id="sp500")
            with Horizontal(id="markets-bottom"):
                yield CryptoWidget(id="crypto")
                yield ExchangeRatesWidget(id="exchange-rates-markets")


# ─────────────────────────────────────────────
# Screen 3 — NEWS
# ─────────────────────────────────────────────

class NewsScreen(Screen):
    def compose(self) -> ComposeResult:
        with Vertical(id="screen-news"):
            with Horizontal(id="news-top"):
                yield HackerNewsWidget(id="hackernews")
                yield RSSWidget(id="rss")
            with Horizontal(id="news-bottom"):
                yield RedditWidget(id="reddit")
                yield CommandOutputWidget(id="command-output")


# ─────────────────────────────────────────────
# Screen 4 — HOME LAB
# ─────────────────────────────────────────────

class HomeLabScreen(Screen):
    def compose(self) -> ComposeResult:
        with Vertical(id="screen-homelab"):
            with Horizontal(id="homelab-top"):
                yield IpVpnWidget(id="ip-vpn")
                yield AirQualityWidget(id="air-quality")
                yield SunriseSunsetWidget(id="sunrise-sunset")
            yield GitHubActivityWidget(id="github-activity")


# ─────────────────────────────────────────────
# Screen 5 — FINANCE
# ─────────────────────────────────────────────

class FinanceScreen(Screen):
    def compose(self) -> ComposeResult:
        with Vertical(id="screen-finance"):
            with Horizontal(id="finance-top"):
                yield ExchangeRatesWidget(id="exchange-rates-finance")
                yield NordpoolWidget(id="nordpool")
            yield TogglTimerWidget(id="toggl-timer")


# ─────────────────────────────────────────────
# Main App
# ─────────────────────────────────────────────

class Dashboard(App):
    CSS_PATH = "dashboard.tcss"
    TITLE = "WTF Dashboard"
    SHOW_CURSOR = False

    BINDINGS = [
        Binding("1", "switch_screen('main')",     "Main",     show=True),
        Binding("2", "switch_screen('markets')",  "Markets",  show=True),
        Binding("3", "switch_screen('news')",     "News",     show=True),
        Binding("4", "switch_screen('homelab')",  "Home Lab", show=True),
        Binding("5", "switch_screen('finance')",  "Finance",  show=True),
        Binding("q", "quit",                      "Quit",     show=True),
        Binding("a", "add_todo",                  "Add Todo", show=False),
    ]

    SCREENS = {
        "main":    MainScreen,
        "markets": MarketsScreen,
        "news":    NewsScreen,
        "homelab": HomeLabScreen,
        "finance": FinanceScreen,
    }

    def on_mount(self) -> None:
        self.push_screen("main")

    def action_switch_screen(self, screen: str) -> None:
        while len(self.screen_stack) > 1:
            self.pop_screen()
        self.push_screen(screen)

    def action_add_todo(self) -> None:
        """Trigger add-item on the TodoWidget."""
        try:
            todo = self.screen.query_one(TodoWidget)
            todo.action_add_item()
        except Exception:
            pass


if __name__ == "__main__":
    Dashboard().run()
