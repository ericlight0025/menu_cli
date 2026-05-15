from __future__ import annotations

import copy
import json

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import Frame, TextArea

from menu_data import load_menu_data, save_menu_data
from prompts import ask_fuzzy
from themes import get_prompt_style


def _flatten_menu(node: dict, path: list[str] | None = None, level: int = 0) -> list[dict]:
    path = path or [node.get("name", "首頁")]
    items = [{"path": path[:], "label": "  " * level + node.get("name", ""), "node": node}]
    for child in node.get("children", []) or []:
        items.extend(_flatten_menu(child, path + [child.get("name", "")], level + 1))
    return items


def _get_node(root: dict, path: list[str]) -> dict | None:
    node = root
    for name in path[1:]:
        children = node.get("children", []) or []
        node = next((child for child in children if child.get("name", "").strip() == name), None)
        if node is None:
            return None
    return node


def _replace_node(root: dict, path: list[str], new_node: dict) -> bool:
    if len(path) == 1:
        root.clear()
        root.update(new_node)
        return True

    parent = _get_node(root, path[:-1])
    if parent is None:
        return False

    target_name = path[-1]
    children = parent.get("children", []) or []
    for index, child in enumerate(children):
        if child.get("name", "").strip() == target_name:
            children[index] = new_node
            parent["children"] = children
            return True
    return False


def _build_content_text(node: dict) -> str:
    if "children" in node:
        return json.dumps(node.get("children", []), ensure_ascii=False, indent=2)
    if "action" in node:
        return json.dumps(node.get("action", {}), ensure_ascii=False, indent=2)
    return "{}"


def _detect_content_kind(node: dict) -> str:
    if "children" in node:
        return "children"
    if "action" in node:
        return "action"
    return "action"


def _select_menu_node(root: dict) -> list[str] | None:
    entries = _flatten_menu(root)
    choices = [{"name": entry["label"], "value": entry["path"]} for entry in entries]
    result = ask_fuzzy(choices, "選擇要編輯的選單", get_prompt_style("dark"))
    if not isinstance(result, list):
        return None
    return result


def _edit_node(root: dict, path: list[str]) -> bool:
    node = _get_node(root, path)
    if node is None:
        return False

    message = {"text": "  Ctrl+S 存檔，Ctrl+C 取消", "error": False}

    name_area = TextArea(text=node.get("name", ""), height=1, multiline=False)
    content_area = TextArea(
        text=_build_content_text(node),
        scrollbar=True,
        line_numbers=True,
        wrap_lines=False,
    )

    kind = _detect_content_kind(node)
    content_title = "children (submenu)" if kind == "children" else "action (leaf)"

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
        new_name = name_area.text.strip()
        if not new_name:
            message["text"] = "  [ERROR] 名稱不能是空白"
            message["error"] = True
            event.app.invalidate()
            return

        try:
            raw_content = json.loads(content_area.text)
        except Exception as exc:
            message["text"] = f"  [ERROR] 內容不是合法 JSON：{exc}"
            message["error"] = True
            event.app.invalidate()
            return

        new_node = copy.deepcopy(node)
        new_node["name"] = new_name

        if kind == "children":
            if not isinstance(raw_content, list):
                message["text"] = "  [ERROR] 子選單內容必須是 JSON 陣列"
                message["error"] = True
                event.app.invalidate()
                return
            new_node["children"] = raw_content
            new_node.pop("action", None)
        else:
            if not isinstance(raw_content, dict):
                message["text"] = "  [ERROR] 動作內容必須是 JSON 物件"
                message["error"] = True
                event.app.invalidate()
                return
            new_node["action"] = raw_content
            new_node.pop("children", None)

        if not _replace_node(root, path, new_node):
            message["text"] = "  [ERROR] 找不到對應的選單節點"
            message["error"] = True
            event.app.invalidate()
            return

        save_menu_data(root)
        message["text"] = "  [SAVED] menu_data.json"
        message["error"] = False
        event.app.exit(result=True)

    layout = Layout(
        HSplit(
            [
                Frame(
                    HSplit(
                        [
                            Window(FormattedTextControl(lambda: f"  路徑：{' / '.join(path)}"), height=1),
                            Window(FormattedTextControl(lambda: f"  編輯模式：{content_title}"), height=1),
                        ]
                    ),
                    title="選單項目",
                ),
                VSplit(
                    [
                        Frame(name_area, title="名稱"),
                        Frame(content_area, title="內容 JSON"),
                    ]
                ),
                Window(content=status_bar, height=1),
            ]
        )
    )

    app = Application(layout=layout, key_bindings=kb, full_screen=True)
    return bool(app.run())


def edit_menu_data() -> bool:
    root = load_menu_data()
    selected_path = _select_menu_node(root)
    if not selected_path:
        return False
    return _edit_node(root, selected_path)
