import psutil
import subprocess
import csv
import io
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from textual.widgets import Static
from config import LHM_URL


def _get_temps() -> dict:
    """Read temperatures from LibreHardwareMonitor web server."""
    result = {"cpu": None, "gpu": None, "drives": {}}
    try:
        import urllib.request, json
        r = urllib.request.urlopen(LHM_URL, timeout=3)
        data = json.loads(r.read())

        def walk(node, path=""):
            name = node.get("Text", "")
            value = node.get("Value", "")
            current_path = f"{path}/{name}"
            if "°" in str(value):
                try:
                    val = round(float(value.split()[0].replace(",", ".")))
                except Exception:
                    val = None
                if val is not None:
                    p = current_path.lower()
                    if "xeon" in p or "intel" in p or "amd" in p and "cpu" in p:
                        if "package" in p or "core average" in p:
                            result["cpu"] = val
                    elif "radeon" in p or "gpu" in p:
                        result["gpu"] = val
                    elif any(x in p for x in ["kingston", "wdc", "samsung", "crucial", "seagate"]):
                        short = name if name != "Temperature" else path.split("/")[-1][:14]
                        result["drives"][short] = val
            for child in node.get("Children", []):
                walk(child, current_path)

        walk(data)
    except Exception:
        pass
    return result


def _get_gpu_load() -> float:
    """Get GPU 3D load via Windows typeperf."""
    try:
        r = subprocess.run(
            ['typeperf', r'\GPU Engine(*engtype_3D*)\Utilization Percentage', '-sc', '1'],
            capture_output=True, text=True, timeout=6
        )
        data_lines = [l for l in r.stdout.splitlines() if l.startswith('"') and '/' in l[:6]]
        if not data_lines:
            return 0.0
        reader = csv.reader(io.StringIO(data_lines[-1]))
        row = next(reader)
        values = [float(v) for v in row[1:] if v.strip()]
        return min(sum(values), 100.0)
    except Exception:
        return 0.0


def _bar(pct: float, width: int = 14) -> str:
    filled = int(min(pct, 100) / 100 * width)
    color = "#4ade80" if pct < 70 else ("#f87171" if pct > 90 else "#fbbf24")
    return f"[{color}]{'█' * filled}[/][#2a2a2a]{'░' * (width - filled)}[/]"


def _pct_color(pct: float, warn: float = 70, crit: float = 90) -> str:
    return "#4ade80" if pct < warn else ("#f87171" if pct > crit else "#fbbf24")


def _temp(val) -> str:
    if val is None:
        return "[#444444]--°C[/]"
    color = "#4ade80" if val < 60 else ("#f87171" if val > 80 else "#fbbf24")
    return f"[{color}]{val}°C[/]"


def _net_bar(bps: float, max_bps: float = 104_857_600, width: int = 14) -> str:
    """Bar scaled to max_bps (default 100 MB/s)."""
    pct = min(bps / max_bps * 100, 100)
    filled = int(pct / 100 * width)
    return f"[#4ade80]{'█' * filled}[/][#2a2a2a]{'░' * (width - filled)}[/]"


def _fmt_bytes(b: float) -> str:
    if b >= 1_048_576:
        return f"{b/1_048_576:6.1f} MB/s"
    elif b >= 1024:
        return f"{b/1024:6.1f} KB/s"
    return f"{b:6.0f}  B/s"


class SystemStatsWidget(Static):
    """CPU, GPU, RAM, Disks, Network — compact bar layout."""

    DEFAULT_CSS = """
    SystemStatsWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 1 2;
        overflow: auto;
    }
    SystemStatsWidget:focus {
        border: round #4ade80;
    }
    """

    _prev_net = None

    def on_mount(self) -> None:
        self._prev_net = psutil.net_io_counters()
        self.set_interval(2, self.refresh_stats)
        self.refresh_stats()

    def refresh_stats(self) -> None:
        self.run_worker(self._collect, thread=True)

    def _collect(self) -> None:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk_c = psutil.disk_usage("C:/")
        disk_d = psutil.disk_usage("D:/")
        disk_f = psutil.disk_usage("F:/")
        gpu = _get_gpu_load()
        temps = _get_temps()

        net = psutil.net_io_counters()
        if self._prev_net:
            sent = (net.bytes_sent - self._prev_net.bytes_sent) / 2
            recv = (net.bytes_recv - self._prev_net.bytes_recv) / 2
        else:
            sent = recv = 0
        self._prev_net = net

        ram_pct  = ram.percent
        c_pct    = disk_c.percent
        d_pct    = disk_d.percent
        f_pct    = disk_f.percent

        def disk_row(label, pct, used, total, temp=None):
            t = f"  {_temp(temp)}" if temp is not None else ""
            return (
                f"[#888888]{label:<4}[/] [{_pct_color(pct,80,95)}]{pct:5.1f}%[/] "
                f"{_bar(pct)} [#666666]{used:.0f}/{total:.0f}GB[/]{t}"
            )

        lines = [
            f"[bold #888888]SYSTEM STATS[/]\n",
            # CPU
            f"[#888888]CPU [/] [{_pct_color(cpu)}]{cpu:5.1f}%[/] {_bar(cpu)}  {_temp(temps['cpu'])}",
            # GPU
            f"[#888888]GPU [/] [{_pct_color(gpu)}]{gpu:5.1f}%[/] {_bar(gpu)}  {_temp(temps['gpu'])}",
            # RAM
            f"[#888888]RAM [/] [{_pct_color(ram_pct)}]{ram_pct:5.1f}%[/] {_bar(ram_pct)} "
            f"[#666666]{ram.used/1e9:.1f}/{ram.total/1e9:.1f}GB[/]",
            "",
            # Drives
            disk_row("C:", c_pct, disk_c.used/1e9, disk_c.total/1e9),
            disk_row("D:", d_pct, disk_d.used/1e9, disk_d.total/1e9),
            disk_row("F:", f_pct, disk_f.used/1e9, disk_f.total/1e9),
            "",
            # Network
            f"[#888888]NET [/] [#4ade80]↑[/] {_net_bar(sent)} [white]{_fmt_bytes(sent)}[/]",
            f"     [#f87171]↓[/] {_net_bar(recv)} [white]{_fmt_bytes(recv)}[/]",
        ]

        self.app.call_from_thread(self.update, "\n".join(lines))
