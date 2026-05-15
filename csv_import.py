from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path

from config import DATA_DIR
from menu_data import DEFAULT_MENU_DATA, load_menu_data, save_menu_data

CSV_IMPORT_FILE = DATA_DIR / "menu_import.csv"
CSV_TEMPLATE_FILE = DATA_DIR / "menu_import_template.csv"
CSV_EXPORT_FILE = DATA_DIR / "menu_export.csv"
CSV_TEMPLATE_HEADERS = ["path", "name", "kind", "action"]

DEFAULT_CSV_ROWS = [
    {"path": "首頁", "name": "📘  功能說明", "kind": "action", "action": '{"type":"about"}'},
    {
        "path": "首頁/🎛️  樣式切換",
        "name": "🌑  深色",
        "kind": "action",
        "action": '{"type":"theme","theme":"dark"}',
    },
    {
        "path": "首頁/⚙️  系統設定",
        "name": "📥  CSV 匯入",
        "kind": "group",
        "action": "",
    },
]


def ensure_csv_import_file() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if CSV_IMPORT_FILE.exists():
        return
    root = load_menu_data()
    _write_csv_file(CSV_IMPORT_FILE, _menu_to_csv_rows(root, blank_actions=True))


def _write_csv_file(path: Path, rows: list[dict]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_TEMPLATE_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def read_csv_rows(path: Path | None = None) -> list[dict]:
    csv_path = path or CSV_IMPORT_FILE
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            if not any((value or "").strip() for value in row.values()):
                continue
            rows.append({key: (value or "").strip() for key, value in row.items()})
        return rows


def _split_path(path_value: str) -> list[str]:
    parts = [part.strip() for part in path_value.replace("\\", "/").split("/") if part.strip()]
    if parts and parts[0] == DEFAULT_MENU_DATA["name"]:
        parts = parts[1:]
    return parts


def _find_child(node: dict, name: str) -> dict | None:
    for child in node.get("children", []) or []:
        if child.get("name", "").strip() == name:
            return child
    return None


def _upsert_child(node: dict, new_child: dict) -> None:
    children = list(node.get("children", []) or [])
    for index, child in enumerate(children):
        if child.get("name", "").strip() == new_child.get("name", "").strip():
            children[index] = new_child
            node["children"] = children
            return
    children.append(new_child)
    node["children"] = children


def _ensure_path(root: dict, path_segments: list[str]) -> dict:
    node = root
    for segment in path_segments:
        child = _find_child(node, segment)
        if child is None:
            child = {"name": segment, "children": []}
            _upsert_child(node, child)
        node = child
    return node


def _parse_action(action_text: str) -> dict:
    action_text = action_text.strip()
    if not action_text:
        return {}
    action = json.loads(action_text)
    if not isinstance(action, dict):
        raise ValueError("action must be a JSON object")
    return action


def preview_csv_rows(rows: list[dict]) -> str:
    lines = [f"  CSV 項目數：{len(rows)}"]
    for index, row in enumerate(rows, start=1):
        lines.append(
            f"  {index:>2}. path={row.get('path', '')} | name={row.get('name', '')} | kind={row.get('kind', '')} | action={row.get('action', '')}"
        )
    return "\n".join(lines)


def _escape_action(action: dict | None, blank: bool) -> str:
    if blank or not action:
        return ""
    return json.dumps(action, ensure_ascii=False, separators=(",", ":"))


def _menu_to_csv_rows(node: dict, *, blank_actions: bool = False) -> list[dict]:
    rows: list[dict] = []

    def walk(current: dict, parent_path: list[str]) -> None:
        for child in current.get("children", []) or []:
            if not isinstance(child, dict):
                continue
            child_path = "/".join(parent_path)
            is_group = bool(child.get("children"))
            action = child.get("action") if isinstance(child.get("action"), dict) else None
            rows.append(
                {
                    "path": child_path,
                    "name": child.get("name", ""),
                    "kind": "group" if is_group else "action",
                    "action": _escape_action(action, blank_actions or is_group),
                }
            )
            if is_group:
                walk(child, parent_path + [child.get("name", "")])

    walk(node, [node.get("name", "首頁")])
    return rows


def write_csv_template_from_menu() -> Path:
    root = load_menu_data()
    _write_csv_file(CSV_TEMPLATE_FILE, _menu_to_csv_rows(root, blank_actions=True))
    return CSV_TEMPLATE_FILE


def write_csv_export_from_menu() -> Path:
    root = load_menu_data()
    _write_csv_file(CSV_EXPORT_FILE, _menu_to_csv_rows(root, blank_actions=False))
    return CSV_EXPORT_FILE


def import_csv_to_menu(rows: list[dict]) -> tuple[dict, list[str]]:
    root = deepcopy(load_menu_data())
    errors: list[str] = []

    for line_no, row in enumerate(rows, start=2):
        path_value = row.get("path", "").strip()
        name = row.get("name", "").strip()
        kind = (row.get("kind", "action") or "action").strip().lower()
        action_text = row.get("action", "").strip()

        if not name:
            errors.append(f"第 {line_no} 行：name 不能空白")
            continue

        if kind not in {"group", "action"}:
            errors.append(f"第 {line_no} 行：kind 只能是 group 或 action")
            continue

        try:
            path_segments = _split_path(path_value)
            parent = root if not path_segments else _ensure_path(root, path_segments)
            node = {"name": name}
            if kind == "group":
                node["children"] = []
            else:
                action = _parse_action(action_text)
                if not action or "type" not in action:
                    raise ValueError("action 必須是包含 type 的 JSON 物件")
                node["action"] = action
            _upsert_child(parent, node)
        except Exception as exc:
            errors.append(f"第 {line_no} 行：{exc}")

    if not errors:
        save_menu_data(root)
    return root, errors
