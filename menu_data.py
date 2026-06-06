from __future__ import annotations

import json

from config import MENU_DATA_FILE

DEFAULT_MENU_DATA = {
    "name": "首頁",
    "children": [
        {"name": "📘  功能說明", "action": {"type": "about"}},
        {
            "name": "📥  CSV 匯入",
            "children": [
                {"name": "📄  預覽 CSV", "action": {"type": "csv_preview"}},
                {"name": "📥  匯入 CSV", "action": {"type": "csv_import"}},
                {"name": "📋  下載範本", "action": {"type": "csv_template"}},
                {"name": "📤  匯出目前內容", "action": {"type": "csv_export"}},
            ],
        },
        {
            "name": "🎛️  樣式切換",
            "children": [
                {"name": "🌑  深色", "action": {"type": "theme", "theme": "dark"}},
                {"name": "🌕  淺色", "action": {"type": "theme", "theme": "light"}},
                {"name": "🟣  霓虹", "action": {"type": "theme", "theme": "neon"}},
                {"name": "✍️  自訂配色檔", "action": {"type": "theme", "theme": "custom"}},
                {"name": "📄  開啟配色檔", "action": {"type": "style_file"}},
            ],
        },
        {
            "name": "📁  開發工具",
            "children": [
                {"name": "🐍  啟動主程式", "action": {"type": "py", "path": "main.py"}},
                {"name": "🔧  安裝腳本", "action": {"type": "bat", "path": "setup.bat"}},
                {"name": "☕  執行 Jar", "action": {"type": "jar", "path": "app.jar"}},
                {"name": "🖥️  執行腳本2", "action": {"type": "py", "path": "tool.py"}},
            ],
        },
        {
            "name": "🌐  常用網址",
            "children": [
                {"name": "📖  官方文件", "action": {"type": "url", "url": "https://docs.example.com"}},
                {"name": "🔍  Google", "action": {"type": "url", "url": "https://google.com"}},
                {"name": "🐙  GitHub", "action": {"type": "url", "url": "https://github.com"}},
            ],
        },
        {
            "name": "⚙️  系統設定",
            "children": [
                {"name": "🎨  主題設定", "action": {"type": "py", "path": "theme.py"}},
                {"name": "⌨️  快速鍵樣式", "action": {"type": "hotkey_style"}},
                {"name": "⚡  快速鍵修改", "action": {"type": "hotkey_modify"}},
                {"name": "🔑  金鑰管理", "action": {"type": "py", "path": "keys.py"}},
                {"name": "📝  編輯選單資料（Ctrl+S）", "action": {"type": "edit_menu"}},
            ],
        },
        {"name": "📋  快速筆記", "action": {"type": "py", "path": "note.py"}},
        {"name": "🚪  離開", "action": {"type": "exit"}},
    ],
}


def _ensure_menu_data_file() -> None:
    MENU_DATA_FILE.parent.mkdir(exist_ok=True)
    if MENU_DATA_FILE.exists():
        return
    MENU_DATA_FILE.write_text(
        json.dumps(DEFAULT_MENU_DATA, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _normalize_legacy_actions(node: dict) -> dict:
    node = dict(node)
    action = node.get("action")
    if isinstance(action, dict) and action.get("type") == "menu_file":
        action = dict(action)
        action["type"] = "edit_menu"
        node["action"] = action

    children = node.get("children")
    if isinstance(children, list):
        node["children"] = [
            _normalize_legacy_actions(child) if isinstance(child, dict) else child
            for child in children
        ]
    return node


def load_menu_data() -> dict:
    _ensure_menu_data_file()
    try:
        data = json.loads(MENU_DATA_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("menu data must be a JSON object")
        normalized = _normalize_legacy_actions(data)
        if normalized != data:
            save_menu_data(normalized)
        return normalized
    except Exception:
        return dict(DEFAULT_MENU_DATA)


def save_menu_data(data: dict) -> None:
    _ensure_menu_data_file()
    data = _normalize_legacy_actions(data)
    MENU_DATA_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def resolve_node(root: dict, path: list[str]) -> dict:
    node = root
    for name in path[1:]:
        children = node.get("children", [])
        found = next((child for child in children if child.get("name", "").strip() == name), None)
        if found is None:
            return root
        node = found
    return node
