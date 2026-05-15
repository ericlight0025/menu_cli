from __future__ import annotations

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import Frame, TextArea

from prompts import describe_hotkey_keys, normalize_key_list
from state import MenuState


def edit_hotkeys(state: MenuState) -> bool:
    message = {"text": "  Ctrl+S 存檔，Ctrl+C 取消"}

    back_area = TextArea(text=",".join(state.hotkey_back_keys), height=1, multiline=False)
    forward_area = TextArea(text=",".join(state.hotkey_forward_keys), height=1, multiline=False)

    status_bar = FormattedTextControl(lambda: message["text"])
    kb = KeyBindings()

    @kb.add("tab")
    def _next(event) -> None:
        event.app.layout.focus_next()

    @kb.add("s-tab")
    def _prev(event) -> None:
        event.app.layout.focus_previous()

    @kb.add("c-c")
    def _cancel(event) -> None:
        event.app.exit(result=False)

    @kb.add("escape")
    def _escape(event) -> None:
        event.app.exit(result=False)

    @kb.add("c-s")
    def _save(event) -> None:
        back_keys = normalize_key_list(back_area.text)
        forward_keys = normalize_key_list(forward_area.text)
        if not back_keys or not forward_keys:
            message["text"] = "  [ERROR] 上/下頁按鍵不能空白"
            event.app.invalidate()
            return
        state.set_hotkey_keys(back_keys, forward_keys)
        message["text"] = (
            f"  [SAVED] 上頁：{describe_hotkey_keys(back_keys)} / 下頁：{describe_hotkey_keys(forward_keys)}"
        )
        event.app.exit(result=True)

    layout = Layout(
        HSplit(
            [
                Frame(
                    VSplit(
                        [
                            Frame(back_area, title="上一頁按鍵 (逗號分隔)", width=40),
                            Frame(forward_area, title="下一頁按鍵 (逗號分隔)", width=40),
                        ]
                    ),
                    title="快速鍵修改",
                ),
                Window(content=status_bar, height=1),
            ]
        )
    )

    app = Application(layout=layout, key_bindings=kb, full_screen=True)
    return bool(app.run())
