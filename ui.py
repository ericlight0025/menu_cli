from __future__ import annotations

import os
import shutil

from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.utils import get_cwidth

from prompts import describe_hotkey_keys
from themes import get_theme_definition, get_ui_style

W = 54

HOTKEY_HINTS = {
    "classic": " Alt+← 上頁  Alt+→ 下頁  Ctrl+C 離開",
    "compact": " ← 上頁  → 下頁  C-c 離開",
    "boxed": " [Alt+←] 上頁  [Alt+→] 下頁  [Ctrl+C] 離開",
}


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _fit(text: str, width: int) -> str:
    if width <= 1:
        return ""
    current = 0
    output = []
    for ch in text:
        ch_width = get_cwidth(ch)
        if current + ch_width > width - 1:
            break
        output.append(ch)
        current += ch_width
    fitted = "".join(output)
    return fitted if get_cwidth(text) <= width else fitted + "…"


def _pad_to_width(text: str, width: int) -> str:
    current = get_cwidth(text)
    if current >= width:
        return text
    return text + (" " * (width - current))


def draw_header(breadcrumb: list[str], theme_name: str, hotkey_style: str, back_keys: list[str], forward_keys: list[str]) -> None:
    clear()
    path = " › ".join(breadcrumb)
    theme = get_theme_definition(theme_name)
    style = get_ui_style(theme_name)
    title = "  ✦  MENU"
    back_label = describe_hotkey_keys(back_keys)
    forward_label = describe_hotkey_keys(forward_keys)
    nav_hint = f" 樣式：{theme['label']}  快捷：{back_label} / {forward_label}" + HOTKEY_HINTS.get(hotkey_style, HOTKEY_HINTS["classic"])
    term_width = shutil.get_terminal_size(fallback=(120, 40)).columns
    content_width = max(get_cwidth(title), get_cwidth(f"  📍 {path}"), get_cwidth(nav_hint), W)
    box_width = min(content_width, max(24, min(term_width - 14, 96)))
    border = "─" * box_width
    title_line = _fit(title, box_width)
    path_line = _fit(f"  📍 {path}", box_width)
    hint_line = _fit(nav_hint, box_width)
    print()
    print_formatted_text(FormattedText([("class:header.border", f"  ╭{border}╮")]), style=style)
    print_formatted_text(
        FormattedText(
            [
                ("class:header.border", "  │"),
                ("class:header.title", _pad_to_width(title_line, box_width)),
                ("class:header.border", "│"),
            ]
        ),
        style=style,
    )
    print_formatted_text(
        FormattedText(
            [
                ("class:header.border", "  │"),
                ("class:header.path", _pad_to_width(path_line, box_width)),
                ("class:header.border", "│"),
            ]
        ),
        style=style,
    )
    print_formatted_text(
        FormattedText(
            [
                ("class:header.border", "  │"),
                ("class:header.hint", _pad_to_width(hint_line, box_width)),
                ("class:header.border", "│"),
            ]
        ),
        style=style,
    )
    print_formatted_text(FormattedText([("class:header.border", f"  ╰{border}╯\n")]), style=style)
