#!/usr/bin/env python3
"""
Fuzzy CLI Menu  ·  InquirerPy
  Alt + ← 上一頁   Alt + → 下一頁   Enter 進入/執行   Ctrl+C 離開
"""

from actions import execute_action
from menu_data import DEFAULT_MENU_DATA, load_menu_data, resolve_node
from prompts import NAV_BACK, NAV_FORWARD, ask_fuzzy
from state import MenuState
from themes import get_prompt_style
from ui import clear, draw_header


def _menu_label(node: dict) -> str:
    children = node.get("children", [])
    if children:
        return f"{node['name']}  ({len(children)})"
    return node["name"]


_DATA_MUTATING_ACTIONS = {"edit_menu", "csv_import"}


def run() -> None:
    state = MenuState()
    history: list[list[str]] = []
    future: list[list[str]] = []
    root = load_menu_data()
    current_path = [root.get("name", DEFAULT_MENU_DATA["name"])]

    def reset_to_root() -> None:
        nonlocal root
        root = load_menu_data()
        current_path[:] = [root.get("name", DEFAULT_MENU_DATA["name"])]
        history.clear()
        future.clear()

    while True:
        current_node = resolve_node(root, current_path)
        breadcrumb = current_path[:]
        children = current_node.get("children", [])
        if not children:
            action = current_node["action"]
            if execute_action(action, state):
                break
            if action.get("type") in _DATA_MUTATING_ACTIONS:
                reset_to_root()
                continue
            if history:
                current_path = history.pop()
            continue

        choices = [{"name": _menu_label(child), "value": child} for child in children]

        draw_header(breadcrumb, state.theme_name, state.hotkey_style, state.hotkey_back_keys, state.hotkey_forward_keys)
        result = ask_fuzzy(
            choices,
            breadcrumb[-1],
            get_prompt_style(state.theme_name),
            state.hotkey_back_keys,
            state.hotkey_forward_keys,
        )

        if result is NAV_BACK:
            if history:
                future.append(current_path[:])
                current_path = history.pop()
            continue

        if result is NAV_FORWARD:
            if future:
                history.append(current_path[:])
                current_path = future.pop()
            continue

        if result is None:
            break

        selected = result

        if "children" in selected:
            history.append(current_path[:])
            future.clear()
            current_path = current_path + [selected["name"].strip()]
        elif "action" in selected:
            future.clear()
            action = selected["action"]
            if execute_action(action, state):
                break
            if action.get("type") in _DATA_MUTATING_ACTIONS:
                reset_to_root()

    clear()
    print("\n  👋  再見！\n")


if __name__ == "__main__":
    run()
