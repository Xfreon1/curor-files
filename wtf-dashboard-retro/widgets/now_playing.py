import asyncio
import threading
import time
from textual.widgets import Static


# Playback status codes from Windows SMTC
_STATUS = {
    0: "Stopped",
    1: "Closed",
    2: "Changing",
    3: "Stopped",
    4: "Playing",
    5: "Paused",
}


def _get_volume() -> tuple[int, bool]:
    try:
        from pycaw.pycaw import AudioUtilities
        devices = AudioUtilities.GetSpeakers()
        vol = devices.EndpointVolume
        return round(vol.GetMasterVolumeLevelScalar() * 100), bool(vol.GetMute())
    except Exception:
        return 0, False


def _vol_bar(level: int, muted: bool, width: int = 12) -> str:
    if muted:
        return f"[#f87171]{'█' * width}[/] [#f87171]Muted[/]"
    filled = int(level / 100 * width)
    bar = f"[#4ade80]{'█' * filled}{'░' * (width - filled)}[/]"
    return f"{bar} [#888888]{level}%[/]"


def _progress_bar(elapsed_s: float, total_s: float, width: int = 14) -> str:
    if total_s <= 0:
        return ""
    ratio = min(1.0, elapsed_s / total_s)
    filled = int(ratio * width)
    bar = f"[#4ade80]{'█' * filled}[/][#444444]{'░' * (width - filled)}[/]"

    def fmt(s: float) -> str:
        s = int(s)
        return f"{s // 60}:{s % 60:02d}"

    return f"{bar} [#888888]{fmt(elapsed_s)} / {fmt(total_s)}[/]"


def _get_media_sync() -> dict:
    """Synchronous wrapper around the async WinRT call."""
    async def _fetch():
        from winrt.windows.media.control import (
            GlobalSystemMediaTransportControlsSessionManager as GSMTCSM,
        )
        mgr = await GSMTCSM.request_async()
        session = mgr.get_current_session()
        if not session:
            return {}
        props = await session.try_get_media_properties_async()
        pb = session.get_playback_info()

        result = {
            "title": props.title or "",
            "artist": props.artist or "",
            "status": pb.playback_status,
        }

        try:
            timeline = session.get_timeline_properties()
            pos = timeline.position.total_seconds()
            end = timeline.end_time.total_seconds()
            if end > 0:
                result["position"] = pos
                result["duration"] = end
                # last_updated_time = when the app actually set this position value
                try:
                    import datetime
                    lut = timeline.last_updated_time  # datetime.datetime UTC
                    result["position_set_at"] = lut.timestamp()
                except Exception:
                    pass
        except Exception:
            pass

        return result

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_fetch())
    except Exception:
        return {}
    finally:
        loop.close()


class NowPlayingWidget(Static):
    """Shows currently playing media via Windows SMTC."""

    DEFAULT_CSS = """
    NowPlayingWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 1 2;
        content-align: center middle;
    }
    NowPlayingWidget:focus {
        border: round #4ade80;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._lock = threading.Lock()
        # Last snapshot from SMTC
        self._last_info: dict = {}
        self._last_level: int = 0
        self._last_muted: bool = False
        # Position interpolation
        self._last_pos: float | None = None
        self._last_pos_time: float = 0.0
        self._last_duration: float | None = None
        self._is_playing: bool = False

    def on_mount(self) -> None:
        self.set_interval(0.3, self._fetch_smtc)
        # Redraw progress bar every 0.3 seconds using interpolation
        self.set_interval(0.3, self._redraw)
        self.run_worker(self._fetch_smtc_worker, thread=True)

    def _fetch_smtc(self) -> None:
        self.run_worker(self._fetch_smtc_worker, thread=True)

    def _fetch_smtc_worker(self) -> None:
        try:
            info = _get_media_sync()
            level, muted = _get_volume()
            status_code = info.get("status", 0)

            with self._lock:
                self._last_info = info
                self._last_level = level
                self._last_muted = muted
                self._is_playing = (status_code == 4)

                pos = info.get("position")
                dur = info.get("duration")
                pos_set_at = info.get("position_set_at")
                if pos is not None:
                    self._last_pos = pos
                    if pos_set_at is not None:
                        self._last_pos_time = time.monotonic() - (time.time() - pos_set_at)
                    else:
                        self._last_pos_time = time.monotonic()
                if dur is not None:
                    self._last_duration = dur

        except ImportError:
            self.app.call_from_thread(
                self.update,
                "[bold #888888]NOW PLAYING[/]\n\n[#666666]winrt not available[/]"
            )
        except Exception as e:
            self.app.call_from_thread(
                self.update,
                f"[bold #888888]NOW PLAYING[/]\n\n[#f87171]{e}[/]"
            )

    def _redraw(self) -> None:
        """Redraw every 0.3s using interpolated position — no WinRT call."""
        with self._lock:
            info = dict(self._last_info)
            last_pos = self._last_pos
            last_pos_time = self._last_pos_time
            last_duration = self._last_duration
            is_playing = self._is_playing
            level = self._last_level
            muted = self._last_muted

        if last_pos is not None and last_duration is not None:
            if is_playing:
                elapsed_since = time.monotonic() - last_pos_time
                pos = min(last_pos + elapsed_since, last_duration)
            else:
                pos = last_pos
            info["position"] = pos
            info["duration"] = last_duration
        self._draw(info, level, muted)

    def _draw(self, info: dict, level: int, muted: bool) -> None:
        vol_bar = _vol_bar(level, muted)
        if not info:
            self.update(
                f"[bold #888888]NOW PLAYING[/]\n\n"
                f"[#666666]Nothing playing[/]\n\n"
                f"[#888888]VOL[/] {vol_bar}"
            )
            return

        title = info.get("title", "Unknown")[:30]
        artist = info.get("artist", "")[:28]
        status_code = info.get("status", 0)
        status = _STATUS.get(status_code, "Playing")
        artist_line = f"\n[#888888]{artist}[/]" if artist else ""

        pos = info.get("position")
        dur = info.get("duration")
        progress_line = f"\n{_progress_bar(pos, dur)}" if pos is not None and dur is not None else ""

        self.update(
            f"[bold #888888]NOW PLAYING[/]\n\n"
            f"[bold #4ade80]{status}[/]\n"
            f"[bold white]{title}[/]"
            f"{artist_line}"
            f"{progress_line}\n\n"
            f"[#888888]VOL[/] {vol_bar}"
        )
