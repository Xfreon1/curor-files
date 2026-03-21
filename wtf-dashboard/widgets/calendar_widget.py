import calendar
import json
import os
from datetime import datetime, date
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input
from textual.binding import Binding


AGENDA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agenda.json")


def _load_agenda() -> dict:
    if not os.path.exists(AGENDA_PATH):
        return {}
    try:
        with open(AGENDA_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_agenda(data: dict) -> None:
    with open(AGENDA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class CalendarWidget(Widget):
    """Month calendar on top + scrollable daily agenda below."""

    can_focus = True

    BINDINGS = [
        Binding("up",    "move_up",   "Up",    show=False),
        Binding("down",  "move_down", "Down",  show=False),
        Binding("e",     "edit_day",  "Edit",  show=False),
        Binding("d",     "clear_day", "Clear", show=False),
    ]

    DEFAULT_CSS = """
    CalendarWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 0;
        overflow: hidden;
    }
    CalendarWidget:focus, CalendarWidget:focus-within {
        border: round #4ade80;
    }
    #cal-top {
        padding: 1 2 0 2;
        height: 11;
    }
    #cal-agenda {
        height: 1fr;
        padding: 0 2 0 2;
        overflow: hidden;
    }
    #cal-input {
        height: 3;
        margin: 0 1 1 1;
        background: #111111;
        color: #e8e8e8;
        border: round #4ade80;
        display: none;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._agenda: dict = {}
        self._days: list[date] = []
        self._selected: int = 0
        self._scroll_offset: int = 0
        self._visible_rows: int = 10
        self._editing_key: str = ""

    def compose(self) -> ComposeResult:
        yield Static(id="cal-top")
        yield Static(id="cal-agenda")
        yield Input(placeholder="Task for this day — Enter to save, Esc to cancel", id="cal-input")

    def on_mount(self) -> None:
        self._agenda = _load_agenda()
        self._build_days()
        self.set_interval(60, self._refresh_cal)
        self._refresh_cal()
        self._refresh_agenda()

    def _build_days(self) -> None:
        now = datetime.now()
        num_days = calendar.monthrange(now.year, now.month)[1]
        self._days = [date(now.year, now.month, d) for d in range(1, num_days + 1)]
        today = date.today()
        for i, d in enumerate(self._days):
            if d == today:
                self._selected = i
                break

    def _refresh_cal(self) -> None:
        now = datetime.now()
        cal = calendar.monthcalendar(now.year, now.month)
        month_name = now.strftime("%B %Y").upper()
        today = now.day

        lines = [f"[bold white]{month_name}[/]\n"]
        lines.append("[#888888]Mo Tu We Th Fr [#4ade80]Sa[/] [#f87171]Su[/][/]")
        lines.append("[#2a2a2a]" + "─" * 21 + "[/]")

        for week in cal:
            row = []
            for i, day in enumerate(week):
                if day == 0:
                    row.append("  ")
                elif day == today:
                    row.append(f"[bold #ffaf00]{day:2}[/]")
                elif i == 5:
                    row.append(f"[#4ade80]{day:2}[/]")
                elif i == 6:
                    row.append(f"[#f87171]{day:2}[/]")
                else:
                    row.append(f"[#e8e8e8]{day:2}[/]")
            lines.append(" ".join(row))

        self.query_one("#cal-top", Static).update("\n".join(lines))

    def _refresh_agenda(self) -> None:
        today = date.today()

        # Calculate visible rows from agenda panel height
        total_h = self.size.height if self.size.height > 0 else 30
        self._visible_rows = max(3, total_h - 13)  # 11 cal + 2 border/padding

        # Keep scroll window around selection
        if self._selected < self._scroll_offset:
            self._scroll_offset = self._selected
        elif self._selected >= self._scroll_offset + self._visible_rows:
            self._scroll_offset = self._selected - self._visible_rows + 1

        focused = self.has_focus
        header = "[#2a2a2a]──[/] [#666666]AGENDA[/]  [#444444]e=edit  d=clear[/]" if focused else "[#2a2a2a]──[/] [#666666]AGENDA[/]  [#444444]tab to focus[/]"
        lines = [header]

        visible = self._days[self._scroll_offset: self._scroll_offset + self._visible_rows]
        for idx, d in enumerate(visible):
            i = idx + self._scroll_offset
            key = d.isoformat()
            msg = self._agenda.get(key, "")

            if d == today:
                date_str = f"[bold #ffaf00]{d.day:2} {d.strftime('%a')}[/]"
            elif d.weekday() == 5:
                date_str = f"[#4ade80]{d.day:2} {d.strftime('%a')}[/]"
            elif d.weekday() == 6:
                date_str = f"[#f87171]{d.day:2} {d.strftime('%a')}[/]"
            elif d < today:
                date_str = f"[#444444]{d.day:2} {d.strftime('%a')}[/]"
            else:
                date_str = f"[#888888]{d.day:2} {d.strftime('%a')}[/]"

            msg_str = f"[white]{msg}[/]" if msg else "[#333333]·[/]"

            if i == self._selected:
                lines.append(f"[bold #4ade80]>[/] {date_str} [reverse]{msg_str}[/reverse]")
            else:
                lines.append(f"  {date_str} {msg_str}")

        # Scroll indicator
        if len(self._days) > self._visible_rows:
            end = self._scroll_offset + self._visible_rows
            lines.append(f"[#444444]  {self._scroll_offset+1}–{min(end, len(self._days))} of {len(self._days)}[/]")

        self.query_one("#cal-agenda", Static).update("\n".join(lines))

    def action_move_up(self) -> None:
        if self._selected > 0:
            self._selected -= 1
            self._refresh_agenda()

    def action_move_down(self) -> None:
        if self._selected < len(self._days) - 1:
            self._selected += 1
            self._refresh_agenda()

    def action_edit_day(self) -> None:
        if not self._days:
            return
        d = self._days[self._selected]
        self._editing_key = d.isoformat()
        inp = self.query_one("#cal-input", Input)
        inp.value = self._agenda.get(self._editing_key, "")
        inp.display = True
        inp.focus()

    def action_clear_day(self) -> None:
        if not self._days:
            return
        key = self._days[self._selected].isoformat()
        self._agenda.pop(key, None)
        _save_agenda(self._agenda)
        self._refresh_agenda()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            self._agenda[self._editing_key] = text
        else:
            self._agenda.pop(self._editing_key, None)
        _save_agenda(self._agenda)
        event.input.clear()
        event.input.display = False
        self._editing_key = ""
        self.focus()
        self._refresh_agenda()

    def on_key(self, event) -> None:
        if event.key == "escape":
            inp = self.query_one("#cal-input", Input)
            if inp.display:
                inp.clear()
                inp.display = False
                self._editing_key = ""
                self.focus()
                event.stop()

    def on_focus(self) -> None:
        self._refresh_agenda()

    def on_blur(self) -> None:
        self._refresh_agenda()
