import os
import tempfile
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input
from textual.binding import Binding
from config import TODO_FILE


TODO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), TODO_FILE)


def _load_todos():
    if not os.path.exists(TODO_PATH):
        return []
    with open(TODO_PATH, encoding="utf-8") as f:
        return [l.rstrip("\n") for l in f if l.strip()]


def _save_todos(items):
    dir_name = os.path.dirname(TODO_PATH) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for item in items:
                f.write(item + "\n")
        os.replace(tmp_path, TODO_PATH)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


class TodoWidget(Widget):
    """Editable todo list with inline input."""

    can_focus = True

    BINDINGS = [
        Binding("a", "add_item", "Add"),
        Binding("e", "edit_item", "Edit"),
        Binding("d", "delete_item", "Delete"),
        Binding("space", "toggle_item", "Toggle"),
        Binding("up", "move_up", "Up"),
        Binding("down", "move_down", "Down"),
    ]

    DEFAULT_CSS = """
    TodoWidget {
        height: 100%;
        border: round #2a2a2a;
        padding: 0;
        overflow: hidden;
    }
    TodoWidget:focus, TodoWidget:focus-within {
        border: round #4ade80;
    }
    #todo-display {
        height: 1fr;
        padding: 1 2;
        overflow: auto;
    }
    #todo-input {
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
        self.items = _load_todos()
        self._selected = 0
        self._scroll_offset = 0
        self._visible_rows = 8  # updated on first render
        self._editing_index = None  # None = add mode, int = edit mode

    def compose(self) -> ComposeResult:
        yield Static(id="todo-display")
        yield Input(placeholder="New item — press Enter to save, Esc to cancel", id="todo-input")

    def on_mount(self) -> None:
        self._refresh_display()

    def _refresh_display(self) -> None:
        # Calculate visible rows from widget height (border=2, padding=2, header=2)
        total_height = self.size.height if self.size.height > 0 else 14
        self._visible_rows = max(3, total_height - 6)

        # Keep scroll window around selected item
        if self._selected < self._scroll_offset:
            self._scroll_offset = self._selected
        elif self._selected >= self._scroll_offset + self._visible_rows:
            self._scroll_offset = self._selected - self._visible_rows + 1

        header = "[bold #888888]TODO[/]  [#666666]a=add  e=edit  d=del  space=done[/]\n"
        lines = [header]

        if not self.items:
            lines.append("[#666666]No items. Press 'a' to add.[/]")
        else:
            visible = self.items[self._scroll_offset: self._scroll_offset + self._visible_rows]
            for idx, item in enumerate(visible):
                i = idx + self._scroll_offset
                is_done = item.startswith("[x] ")
                label = item[4:] if (is_done or item.startswith("[ ] ")) else item
                cursor = "[bold #4ade80]>[/] " if i == self._selected else "  "
                if is_done:
                    lines.append(f"[#666666]{cursor}[v] {label}[/]")
                else:
                    color = "bold white" if i == self._selected else "#e8e8e8"
                    lines.append(f"[{color}]{cursor}{label}[/]")

            # Scroll indicator
            if len(self.items) > self._visible_rows:
                shown_end = self._scroll_offset + self._visible_rows
                lines.append(
                    f"[#444444]  {self._scroll_offset + 1}–{min(shown_end, len(self.items))} of {len(self.items)}[/]"
                )

        self.query_one("#todo-display", Static).update("\n".join(lines))

    def action_add_item(self) -> None:
        self._editing_index = None
        inp = self.query_one("#todo-input", Input)
        inp.value = ""
        inp.display = True
        inp.focus()

    def action_edit_item(self) -> None:
        if not self.items:
            return
        item = self.items[self._selected]
        label = item[4:] if (item.startswith("[x] ") or item.startswith("[ ] ")) else item
        self._editing_index = self._selected
        inp = self.query_one("#todo-input", Input)
        inp.value = label
        inp.display = True
        inp.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        # Escape Rich markup to prevent injection
        text = text.replace("[", r"\[")
        if self._editing_index is not None:
            if text:
                # Preserve done state when editing
                old = self.items[self._editing_index]
                prefix = "[x] " if old.startswith("[x] ") else "[ ] "
                self.items[self._editing_index] = prefix + text
                _save_todos(self.items)
            self._editing_index = None
        else:
            if text:
                self.items.append(f"[ ] {text}")
                _save_todos(self.items)
        event.input.clear()
        event.input.display = False
        self.focus()
        self._refresh_display()

    def on_key(self, event) -> None:
        if event.key == "escape":
            inp = self.query_one("#todo-input", Input)
            if inp.display:
                inp.clear()
                inp.display = False
                self.focus()
                event.stop()

    def action_move_up(self) -> None:
        if self._selected > 0:
            self._selected -= 1
            self._refresh_display()

    def action_move_down(self) -> None:
        if self._selected < len(self.items) - 1:
            self._selected += 1
            self._refresh_display()

    def action_toggle_item(self) -> None:
        if not self.items:
            return
        item = self.items[self._selected]
        if item.startswith("[x] "):
            self.items[self._selected] = "[ ] " + item[4:]
        elif item.startswith("[ ] "):
            self.items[self._selected] = "[x] " + item[4:]
        else:
            self.items[self._selected] = "[x] " + item
        _save_todos(self.items)
        self._refresh_display()

    def action_delete_item(self) -> None:
        if not self.items:
            return
        self.items.pop(self._selected)
        if self._selected >= len(self.items) and self._selected > 0:
            self._selected -= 1
        _save_todos(self.items)
        self._refresh_display()
