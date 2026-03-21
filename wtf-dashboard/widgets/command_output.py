import subprocess
from textual.widgets import Static
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import CUSTOM_COMMAND


class CommandOutputWidget(Static):
    """Runs a shell command and shows the output."""

    DEFAULT_CSS = """
    CommandOutputWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 1 2;
        overflow: auto;
    }
    CommandOutputWidget:focus {
        border: round #4ade80;
    }
    """

    def on_mount(self) -> None:
        self.update(
            f"[bold #888888]COMMAND OUTPUT[/]\n"
            f"[#666666]$ {CUSTOM_COMMAND[:50]}[/]\n\n"
            "[#666666]Running...[/]"
        )
        self.set_interval(30, self.refresh_output)
        self.run_worker(self._run, thread=True)

    def refresh_output(self) -> None:
        self.run_worker(self._run, thread=True)

    def _run(self) -> None:
        try:
            result = subprocess.run(
                CUSTOM_COMMAND,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = result.stdout.strip() or result.stderr.strip() or "(no output)"
            # Escape markup characters
            output = output.replace("[", r"\[")
            text = (
                f"[bold #888888]COMMAND OUTPUT[/]\n"
                f"[#666666]$ {CUSTOM_COMMAND[:50]}[/]\n\n"
                f"[#e8e8e8]{output}[/]"
            )
        except subprocess.TimeoutExpired:
            text = (
                f"[bold #888888]COMMAND OUTPUT[/]\n"
                f"[#666666]$ {CUSTOM_COMMAND[:50]}[/]\n\n"
                "[#f87171]Command timed out[/]"
            )
        except Exception as e:
            text = (
                f"[bold #888888]COMMAND OUTPUT[/]\n\n"
                f"[#f87171]Error: {e}[/]"
            )
        self.app.call_from_thread(self.update, text)
