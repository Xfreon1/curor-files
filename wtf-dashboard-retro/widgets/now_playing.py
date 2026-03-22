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
                try:
                    import datetime
                    lut = timeline.last_updated_time
                    result["position_set_at"] = lut.timestamp()
                except Exception:
                    pass
        except Exception:
            pass

        # Extract album art thumbnail
        try:
            thumb_ref = props.thumbnail
            if thumb_ref is not None:
                from winrt.windows.storage.streams import DataReader
                stream = await thumb_ref.open_read_async()
                size = stream.size
                reader = DataReader(stream)
                await reader.load_async(size)
                result["thumbnail_bytes"] = bytes(reader.read_buffer(size))
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
        # Album art cache
        self._art_cache_key: str = ""
        self._art_lines: list[str] = []

    def on_mount(self) -> None:
        self.set_interval(0.3, self._fetch_smtc)
        self.set_interval(0.3, self._redraw)
        self.run_worker(self._fetch_smtc_worker, thread=True)

    def _fetch_smtc(self) -> None:
        self.run_worker(self._fetch_smtc_worker, thread=True)

    def _fetch_smtc_worker(self) -> None:
        try:
            info = _get_media_sync()
            level, muted = _get_volume()
            status_code = info.get("status", 0)

            # Process album art — only when track changes
            cache_key = f"{info.get('title', '')}|{info.get('artist', '')}"
            thumb_bytes = info.pop("thumbnail_bytes", None)

            if cache_key and cache_key != self._art_cache_key:
                art_lines = []
                if thumb_bytes:
                    try:
                        from widgets.braille_art import image_to_braille
                        art_lines = image_to_braille(thumb_bytes, width=16, height=8)
                    except Exception:
                        pass
                with self._lock:
                    self._art_lines = art_lines
                    self._art_cache_key = cache_key

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
            art_lines = list(self._art_lines)

        if last_pos is not None and last_duration is not None:
            if is_playing:
                elapsed_since = time.monotonic() - last_pos_time
                pos = min(last_pos + elapsed_since, last_duration)
            else:
                pos = last_pos
            info["position"] = pos
            info["duration"] = last_duration
        self._draw(info, level, muted, art_lines)

    def _draw(self, info: dict, level: int, muted: bool, art_lines: list[str] | None = None) -> None:
        vol_bar = _vol_bar(level, muted)

        # Build text lines
        text_lines = []
        text_lines.append("[bold #888888]NOW PLAYING[/]")
        text_lines.append("")

        if not info:
            text_lines.append("[#666666]Nothing playing[/]")
            text_lines.append("")
            text_lines.append(f"[#888888]VOL[/] {vol_bar}")
        else:
            title = info.get("title", "Unknown")[:30]
            artist = info.get("artist", "")[:28]
            status_code = info.get("status", 0)
            status = _STATUS.get(status_code, "Playing")

            text_lines.append(f"[bold #4ade80]{status}[/]")
            text_lines.append(f"[bold white]{title}[/]")
            if artist:
                text_lines.append(f"[#888888]{artist}[/]")

            pos = info.get("position")
            dur = info.get("duration")
            if pos is not None and dur is not None:
                text_lines.append(_progress_bar(pos, dur))

            text_lines.append("")
            text_lines.append(f"[#888888]VOL[/] {vol_bar}")

        if art_lines:
            # Side-by-side: art on left, text on right
            max_rows = max(len(art_lines), len(text_lines))
            art_width = len(art_lines[0]) if art_lines else 0
            blank_art = " " * art_width

            while len(art_lines) < max_rows:
                art_lines.append(blank_art)
            while len(text_lines) < max_rows:
                text_lines.append("")

            merged = []
            for art_row, text_row in zip(art_lines, text_lines):
                merged.append(f"[#4ade80]{art_row}[/]  {text_row}")
            self.update("\n".join(merged))
        else:
            self.update("\n".join(text_lines))
