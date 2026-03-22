import heapq
import threading
import psutil
from textual.widget import Widget
from textual.widgets import Static, Input
from textual.app import ComposeResult
from textual.binding import Binding
from widgets.utils import pct_bar


def _rss(p: dict) -> float:
    mi = p.get("memory_info")
    if mi is None:
        return 0.0
    return getattr(mi, "rss", 0) or 0


_SORT_MODES = ["cpu", "ram", "name"]
_SORT_LABELS = {"cpu": "CPU%", "ram": "RAM", "name": "NAME"}


class ProcessesWidget(Widget):
    """Processes with sortable columns and name filter."""

    can_focus = True

    BINDINGS = [
        Binding("up",   "move_up",    "Up",     show=False),
        Binding("down", "move_down",  "Down",   show=False),
        Binding("k",    "kill_proc",  "Kill",   show=False),
        Binding("c",    "sort_cpu",   "CPU",    show=False),
        Binding("m",    "sort_ram",   "RAM",    show=False),
        Binding("n",    "sort_name",  "Name",   show=False),
        Binding("f",    "filter",     "Filter", show=False),
    ]

    DEFAULT_CSS = """
    ProcessesWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 0;
        overflow: hidden;
    }
    ProcessesWidget:focus, ProcessesWidget:focus-within {
        border: round #4ade80;
    }
    #proc-display {
        height: 1fr;
        padding: 1 2;
        overflow: auto;
    }
    #proc-filter {
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
        self._lock = threading.Lock()
        self._selected = 0
        self._all_procs: list[dict] = []
        self._cpu_total: float = 0.0
        self._ram_used_gb: float = 0.0
        self._ram_total_gb: float = 0.0
        self._ram_pct: float = 0.0
        self._sort_mode: str = "cpu"
        self._filter_text: str = ""
        self._confirm_kill: bool = False
        self._confirm_pid: int | None = None

    def compose(self) -> ComposeResult:
        yield Static(id="proc-display")
        yield Input(placeholder="Filter by name — Enter to apply, Esc to cancel", id="proc-filter")

    def on_mount(self) -> None:
        self.set_interval(5, self.refresh_procs)
        self.refresh_procs()

    def refresh_procs(self) -> None:
        self.run_worker(self._collect, thread=True)

    def _collect(self) -> None:
        try:
            cpu_total = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()

            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
                try:
                    procs.append(p.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            with self._lock:
                self._cpu_total = cpu_total
                self._ram_used_gb = ram.used / 1_073_741_824
                self._ram_total_gb = ram.total / 1_073_741_824
                self._ram_pct = ram.percent
                self._all_procs = procs

            self.app.call_from_thread(self._draw)
        except Exception as e:
            def _show_error():
                self.query_one("#proc-display", Static).update(f"[#f87171]Error: {e}[/]")
            self.app.call_from_thread(_show_error)

    def _get_sorted_procs(self) -> list[dict]:
        """Return filtered and sorted process list."""
        procs = self._all_procs
        if self._filter_text:
            ft = self._filter_text.lower()
            procs = [p for p in procs if ft in (p.get("name") or "").lower()]

        if self._sort_mode == "cpu":
            return heapq.nlargest(16, procs, key=lambda x: x.get("cpu_percent") or 0)
        elif self._sort_mode == "ram":
            return heapq.nlargest(16, procs, key=_rss)
        else:  # name
            return sorted(procs, key=lambda x: (x.get("name") or "").lower())[:16]

    def _draw(self) -> None:
        col = 20
        cpu_c = "#4ade80" if self._cpu_total < 70 else ("#f87171" if self._cpu_total > 90 else "#fbbf24")
        ram_c = "#4ade80" if self._ram_pct < 70 else ("#f87171" if self._ram_pct > 90 else "#fbbf24")

        if self._confirm_kill and self._confirm_pid is not None:
            kill_hint = f"[#f87171]Kill PID {self._confirm_pid}? k=confirm[/]"
        else:
            kill_hint = "[#666666]k=kill[/]"

        # Filter indicator
        filter_hint = ""
        if self._filter_text:
            filter_hint = f"  [#fbbf24]filter: {self._filter_text}[/]"

        lines = [
            f"[bold #888888]PROCESSES[/]  {kill_hint}{filter_hint}",
            f"[#666666]CPU[/] [{cpu_c}]{self._cpu_total:5.1f}%[/] {pct_bar(self._cpu_total)}",
            f"[#666666]RAM[/] [{ram_c}]{self._ram_pct:5.1f}%[/] {pct_bar(self._ram_pct)} [#666666]{self._ram_used_gb:.1f}/{self._ram_total_gb:.0f}GB[/]",
            "",
        ]

        # Column headers with sort indicator
        def hdr(mode, label, width):
            if self._sort_mode == mode:
                return f"[bold #4ade80]{label:<{width}}[/]"
            return f"[#666666]{label:<{width}}[/]"

        lines.append(
            f"   {hdr('name', 'NAME', col)} {hdr('cpu', 'CPU%', 6)} {hdr('ram', 'RAM', 6)}  "
            f"[#444444]c/m/n=sort f=filter[/]"
        )
        lines.append("[#2a2a2a]" + "─" * (col + 18) + "[/]")

        sorted_procs = self._get_sorted_procs()

        # Clamp selection
        if sorted_procs and self._selected >= len(sorted_procs):
            self._selected = len(sorted_procs) - 1

        for i, p in enumerate(sorted_procs):
            cpu = p.get("cpu_percent") or 0
            rss_gb = _rss(p) / 1_073_741_824
            name = (p.get("name") or "?")[:col]
            cpu_color = "#f87171" if cpu > 50 else "#e8e8e8"
            ram_color = "#f87171" if rss_gb > 4 else "#e8e8e8"

            cpu_val = f"{cpu:5.1f}%"
            ram_val = f"{rss_gb:5.2f}G"

            if i == self._selected:
                lines.append(
                    f"[reverse][bold #4ade80]>[/] [white]{name:<{col}}[/] "
                    f"[{cpu_color}]{cpu_val}[/] [{ram_color}]{ram_val}[/][/reverse]"
                )
            else:
                lines.append(
                    f"   [white]{name:<{col}}[/] "
                    f"[{cpu_color}]{cpu_val}[/] [{ram_color}]{ram_val}[/]"
                )

        self.query_one("#proc-display", Static).update("\n".join(lines))

    def _total(self) -> int:
        return len(self._get_sorted_procs())

    def _reset_confirm(self) -> None:
        self._confirm_kill = False
        self._confirm_pid = None

    def action_move_up(self) -> None:
        self._reset_confirm()
        if self._selected > 0:
            self._selected -= 1
            self._draw()

    def action_move_down(self) -> None:
        self._reset_confirm()
        if self._selected < self._total() - 1:
            self._selected += 1
            self._draw()

    def action_sort_cpu(self) -> None:
        self._sort_mode = "cpu"
        self._selected = 0
        self._reset_confirm()
        self._draw()

    def action_sort_ram(self) -> None:
        self._sort_mode = "ram"
        self._selected = 0
        self._reset_confirm()
        self._draw()

    def action_sort_name(self) -> None:
        self._sort_mode = "name"
        self._selected = 0
        self._reset_confirm()
        self._draw()

    def action_filter(self) -> None:
        inp = self.query_one("#proc-filter", Input)
        inp.value = self._filter_text
        inp.display = True
        inp.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._filter_text = event.value.strip()
        self._selected = 0
        event.input.clear()
        event.input.display = False
        self.focus()
        self._draw()

    def on_key(self, event) -> None:
        if event.key == "escape":
            inp = self.query_one("#proc-filter", Input)
            if inp.display:
                inp.clear()
                inp.display = False
                self._filter_text = ""
                self._selected = 0
                self.focus()
                self._draw()
                event.stop()

    def action_kill_proc(self) -> None:
        sorted_procs = self._get_sorted_procs()
        if self._selected >= len(sorted_procs):
            return
        p = sorted_procs[self._selected]
        pid = p.get("pid")
        if pid is None:
            return

        if self._confirm_kill and self._confirm_pid == pid:
            try:
                psutil.Process(pid).terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            self._reset_confirm()
            self.refresh_procs()
        else:
            self._confirm_kill = True
            self._confirm_pid = pid
            self._draw()
