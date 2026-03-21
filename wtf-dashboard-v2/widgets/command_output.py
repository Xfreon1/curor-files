import shlex
import subprocess
from textual.widgets import Static
from config import CUSTOM_COMMAND, CUSTOM_COMMAND_SHELL


def _escape(text: str) -> str:
    """Escape Rich markup characters."""
    return text.replace("[", r"\[")


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
        cmd_display = _escape(CUSTOM_COMMAND[:50])
        self.update(
            f"[bold #888888]COMMAND OUTPUT[/]\n"
            f"[#666666]$ {cmd_display}[/]\n\n"
            "[#666666]Running...[/]"
        )
        self.set_interval(30, self.refresh_output)
        self.run_worker(self._run, thread=True)

    def refresh_output(self) -> None:
        self.run_worker(self._run, thread=True)

    def _run(self) -> None:
        cmd_display = _escape(CUSTOM_COMMAND[:50])
        try:
            if CUSTOM_COMMAND_SHELL:
                args = CUSTOM_COMMAND
                use_shell = True
            else:
                args = shlex.split(CUSTOM_COMMAND)
                use_shell = False

            result = subprocess.run(
                args,
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = result.stdout.strip() or result.stderr.strip() or "(no output)"
            output = _escape(output)
            text = (
                f"[bold #888888]COMMAND OUTPUT[/]\n"
                f"[#666666]$ {cmd_display}[/]\n\n"
                f"[#e8e8e8]{output}[/]"
            )
        except subprocess.TimeoutExpired:
            text = (
                f"[bold #888888]COMMAND OUTPUT[/]\n"
                f"[#666666]$ {cmd_display}[/]\n\n"
                "[#f87171]Command timed out[/]"
            )
        except OSError as e:
            text = (
                f"[bold #888888]COMMAND OUTPUT[/]\n\n"
                f"[#f87171]Error: {_escape(str(e))}[/]"
            )
        self.app.call_from_thread(self.update, text)
