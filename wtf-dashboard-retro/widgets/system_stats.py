import psutil
import subprocess
import csv
import io
import time as _time
import threading
from collections import deque
from textual.widgets import Static
from config import LHM_URL
from widgets.utils import pct_bar, pct_color, fmt_bytes


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


_gpu_cache: dict = {"value": 0.0, "ts": 0.0}


def _get_gpu_load() -> float:
    """Get GPU 3D load via Windows typeperf (cached for 10s)."""
    now = _time.monotonic()
    if now - _gpu_cache["ts"] < 10.0:
        return _gpu_cache["value"]
    try:
        r = subprocess.run(
            ['typeperf', r'\GPU Engine(*engtype_3D*)\Utilization Percentage', '-sc', '1'],
            capture_output=True, text=True, timeout=6
        )
        data_lines = [l for l in r.stdout.splitlines() if l.startswith('"') and '/' in l[:6]]
        if not data_lines:
            return _gpu_cache["value"]
        reader = csv.reader(io.StringIO(data_lines[-1]))
        row = next(reader)
        values = [float(v) for v in row[1:] if v.strip()]
        result = min(sum(values), 100.0)
        _gpu_cache["value"] = result
        _gpu_cache["ts"] = now
        return result
    except Exception:
        return _gpu_cache["value"]



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


_SPARKS = "▁▂▃▄▅▆▇█"


def _sparkline(vals: list, width: int = 16, max_val: float = 0.0) -> str:
    """Render ASCII sparkline. max_val=0 means auto-scale to window max."""
    if not vals:
        return "[#333333]" + "·" * width + "[/]"
    window = vals[-width:]
    mx = max_val if max_val > 0 else max(max(window), 1)
    pad = width - len(window)
    chars = [_SPARKS[min(int(v / mx * 7), 7)] for v in window]
    return "[#333333]" + " " * pad + "[/][#4ade80]" + "".join(chars) + "[/]"


def _uptime_badge() -> str:
    """Return color-coded uptime string."""
    elapsed = _time.time() - psutil.boot_time()
    days = int(elapsed // 86400)
    hours = int((elapsed % 86400) // 3600)
    mins = int((elapsed % 3600) // 60)
    label = f"{days}d {hours}h" if days > 0 else f"{hours}h {mins}m"
    color = "#4ade80" if days < 1 else ("#fbbf24" if days < 7 else "#f87171")
    return f"[{color}]↑{label}[/]"




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

    def on_mount(self) -> None:
        self._prev_net = psutil.net_io_counters()
        self._lock = threading.Lock()
        self._cpu_hist: deque = deque(maxlen=30)
        self._gpu_hist: deque = deque(maxlen=30)
        self._ram_hist: deque = deque(maxlen=30)
        self._sent_hist: deque = deque(maxlen=30)
        self._recv_hist: deque = deque(maxlen=30)
        self.set_interval(2, self.refresh_stats)
        self.refresh_stats()

    def refresh_stats(self) -> None:
        self.run_worker(self._collect, thread=True)

    def _collect(self) -> None:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        gpu = _get_gpu_load()
        temps = _get_temps()

        # Auto-detect disk partitions
        disks = []
        for p in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(p.mountpoint)
                label = p.mountpoint.rstrip("\\")
                disks.append((label, usage))
            except (PermissionError, OSError):
                pass

        # Network with lock to protect _prev_net and history deques
        net = psutil.net_io_counters()
        with self._lock:
            if self._prev_net:
                sent = (net.bytes_sent - self._prev_net.bytes_sent) / 2
                recv = (net.bytes_recv - self._prev_net.bytes_recv) / 2
            else:
                sent = recv = 0
            self._prev_net = net
            self._cpu_hist.append(cpu)
            self._gpu_hist.append(gpu)
            self._ram_hist.append(ram.percent)
            self._sent_hist.append(sent)
            self._recv_hist.append(recv)
            cpu_snap = list(self._cpu_hist)
            gpu_snap = list(self._gpu_hist)
            ram_snap = list(self._ram_hist)
            sent_snap = list(self._sent_hist)
            recv_snap = list(self._recv_hist)

        cpu_spark = _sparkline(cpu_snap, max_val=100.0)
        gpu_spark = _sparkline(gpu_snap, max_val=100.0)
        ram_spark = _sparkline(ram_snap, max_val=100.0)
        sent_spark = _sparkline(sent_snap)
        recv_spark = _sparkline(recv_snap)
        uptime = _uptime_badge()

        ram_pct = ram.percent

        def disk_row(label, pct, used, total, temp=None):
            t = f"  {_temp(temp)}" if temp is not None else ""
            return (
                f"[#888888]{label:<4}[/] [{pct_color(pct,80,95)}]{pct:5.1f}%[/] "
                f"{pct_bar(pct)} [#666666]{used:.0f}/{total:.0f}GB[/]{t}"
            )

        lines = [
            f"[bold #888888]SYSTEM STATS[/]  {uptime}\n",
            f"[#888888]CPU [/] [{pct_color(cpu)}]{cpu:5.1f}%[/] {pct_bar(cpu)}  {_temp(temps['cpu'])}",
            f"     {cpu_spark}",
            f"[#888888]GPU [/] [{pct_color(gpu)}]{gpu:5.1f}%[/] {pct_bar(gpu)}  {_temp(temps['gpu'])}",
            f"     {gpu_spark}",
            f"[#888888]RAM [/] [{pct_color(ram_pct)}]{ram_pct:5.1f}%[/] {pct_bar(ram_pct)} "
            f"[#666666]{ram.used/1e9:.1f}/{ram.total/1e9:.1f}GB[/]",
            f"     {ram_spark}",
            "",
        ]

        for label, usage in disks:
            lines.append(disk_row(label, usage.percent, usage.used / 1e9, usage.total / 1e9))

        lines.extend([
            "",
            f"[#888888]NET [/] [#4ade80]↑[/] {_net_bar(sent)} [white]{fmt_bytes(sent)}[/]",
            f"     [#f87171]↓[/] {_net_bar(recv)} [white]{fmt_bytes(recv)}[/]",
        ])

        self.app.call_from_thread(self.update, "\n".join(lines))
