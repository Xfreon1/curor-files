import psutil
from textual.widget import Widget
from textual.widgets import Static
from textual.app import ComposeResult
from textual.binding import Binding


def _rss(p: dict) -> float:
    mi = p.get("memory_info")
    if mi is None:
        return 0.0
    return getattr(mi, "rss", 0) or 0


class ProcessesWidget(Widget):
    """Processes sorted by CPU (top) then RAM (bottom). Up/Down to select, K to kill."""

    can_focus = True

    BINDINGS = [
        Binding("up",   "move_up",   "Up",   show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("k",    "kill_proc", "Kill", show=False),
    ]

    DEFAULT_CSS = """
    ProcessesWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 0;
        overflow: hidden;
    }
    ProcessesWidget:focus {
        border: round #4ade80;
    }
    #proc-display {
        height: 1fr;
        padding: 1 2;
        overflow: auto;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._selected = 0
        self._by_cpu: list[dict] = []
        self._by_ram: list[dict] = []
        self._cpu_total: float = 0.0
        self._ram_used_gb: float = 0.0
        self._ram_total_gb: float = 0.0
        self._ram_pct: float = 0.0

    def compose(self) -> ComposeResult:
        yield Static(id="proc-display")

    def on_mount(self) -> None:
        self.set_interval(5, self.refresh_procs)
        self.refresh_procs()

    def refresh_procs(self) -> None:
        self.run_worker(self._collect, thread=True)

    def _collect(self) -> None:
        try:
            self._cpu_total = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            self._ram_used_gb = ram.used / 1_073_741_824
            self._ram_total_gb = ram.total / 1_073_741_824
            self._ram_pct = ram.percent

            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
                try:
                    procs.append(p.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            self._by_cpu = sorted(procs, key=lambda x: x.get("cpu_percent") or 0, reverse=True)[:8]
            self._by_ram = sorted(procs, key=_rss, reverse=True)[:8]

            total = len(self._by_cpu) + len(self._by_ram)
            if self._selected >= total:
                self._selected = 0
            self.app.call_from_thread(self._draw)
        except Exception as e:
            self.app.call_from_thread(
                self.query_one("#proc-display", Static).update,
                f"[#f87171]Error: {e}[/]"
            )

    @staticmethod
    def _pct_bar(pct: float, width: int = 16) -> str:
        filled = int(pct / 100 * width)
        color = "#4ade80" if pct < 70 else ("#f87171" if pct > 90 else "#fbbf24")
        return f"[{color}]{'█' * filled}[/][#2a2a2a]{'░' * (width - filled)}[/]"

    def _draw(self) -> None:
        col = 20
        cpu_c = "#4ade80" if self._cpu_total < 70 else ("#f87171" if self._cpu_total > 90 else "#fbbf24")
        ram_c = "#4ade80" if self._ram_pct < 70 else ("#f87171" if self._ram_pct > 90 else "#fbbf24")

        lines = [
            f"[bold #888888]PROCESSES[/]  [#666666]k=kill[/]",
            f"[#666666]CPU[/] [{cpu_c}]{self._cpu_total:5.1f}%[/] {self._pct_bar(self._cpu_total)}",
            f"[#666666]RAM[/] [{ram_c}]{self._ram_pct:5.1f}%[/] {self._pct_bar(self._ram_pct)} [#666666]{self._ram_used_gb:.1f}/{self._ram_total_gb:.0f}GB[/]",
            "",
        ]

        # ── CPU section ──
        lines.append(f"[#666666]{'NAME':<{col}} {'CPU%':>6}[/]")
        lines.append("[#2a2a2a]" + "─" * (col + 8) + "[/]")
        for i, p in enumerate(self._by_cpu):
            cpu = p.get("cpu_percent") or 0
            color = "#f87171" if cpu > 50 else "#e8e8e8"
            name = (p.get("name") or "?")[:col]
            val = f"{cpu:5.1f}%"
            if i == self._selected:
                lines.append(f"[reverse][bold #4ade80]>[/] [white]{name:<{col}}[/] [{color}]{val}[/][/reverse]")
            else:
                lines.append(f"   [white]{name:<{col}}[/] [{color}]{val}[/]")

        # ── RAM section ──
        lines.append("")
        lines.append(f"[#666666]{'NAME':<{col}} {'RAM GB':>6}[/]")
        lines.append("[#2a2a2a]" + "─" * (col + 8) + "[/]")
        offset = len(self._by_cpu)
        for i, p in enumerate(self._by_ram):
            rss_gb = _rss(p) / 1_073_741_824
            color = "#f87171" if rss_gb > 4 else "#e8e8e8"
            name = (p.get("name") or "?")[:col]
            val = f"{rss_gb:5.2f}G"
            j = offset + i
            if j == self._selected:
                lines.append(f"[reverse][bold #4ade80]>[/] [white]{name:<{col}}[/] [{color}]{val}[/][/reverse]")
            else:
                lines.append(f"   [white]{name:<{col}}[/] [{color}]{val}[/]")

        self.query_one("#proc-display", Static).update("\n".join(lines))

    def _total(self) -> int:
        return len(self._by_cpu) + len(self._by_ram)

    def action_move_up(self) -> None:
        if self._selected > 0:
            self._selected -= 1
            self._draw()

    def action_move_down(self) -> None:
        if self._selected < self._total() - 1:
            self._selected += 1
            self._draw()

    def action_kill_proc(self) -> None:
        cpu_len = len(self._by_cpu)
        p = self._by_cpu[self._selected] if self._selected < cpu_len else self._by_ram[self._selected - cpu_len]
        pid = p.get("pid")
        if pid is None:
            return
        try:
            psutil.Process(pid).terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        self.refresh_procs()
