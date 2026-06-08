from __future__ import annotations

import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

from config import APP_VERSION, BASE_DIR, MENU_DATA_FILE, STYLE_FILE
from csv_import import (
    CSV_IMPORT_FILE,
    CSV_EXPORT_FILE,
    CSV_TEMPLATE_FILE,
    ensure_csv_import_file,
    import_csv_to_menu,
    preview_csv_rows,
    read_csv_rows,
    write_csv_export_from_menu,
    write_csv_template_from_menu,
)
from editor import edit_menu_data
from hotkey_editor import edit_hotkeys
from prompts import ask_fuzzy, describe_hotkey_keys
from state import MenuState
from themes import ensure_custom_theme_file, get_prompt_style, get_theme_definition


def _show_line(symbol: str, text: str) -> None:
    print(f"\n  {symbol}  {text}\n")


def _info(text: str) -> None:
    _show_line("ℹ️", text)


def _error(text: str) -> None:
    _show_line("⚠️", text)


def _pause() -> None:
    input("  按 Enter 繼續...")


def _resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (BASE_DIR / path)


def _run_command(command: list[str] | str, cwd: Path, shell: bool = False) -> None:
    subprocess.run(command, cwd=str(cwd), shell=shell, check=False)


def open_custom_style_file() -> None:
    ensure_custom_theme_file()
    if hasattr(os, "startfile"):
        os.startfile(str(STYLE_FILE))
    else:
        webbrowser.open(STYLE_FILE.as_uri())


def open_menu_data_file() -> None:
    MENU_DATA_FILE.parent.mkdir(exist_ok=True)
    if not MENU_DATA_FILE.exists():
        from menu_data import DEFAULT_MENU_DATA, save_menu_data

        save_menu_data(DEFAULT_MENU_DATA)
    if hasattr(os, "startfile"):
        os.startfile(str(MENU_DATA_FILE))
    else:
        webbrowser.open(MENU_DATA_FILE.as_uri())


def open_csv_import_file() -> None:
    ensure_csv_import_file()
    if hasattr(os, "startfile"):
        os.startfile(str(CSV_IMPORT_FILE))
    else:
        webbrowser.open(CSV_IMPORT_FILE.as_uri())


def show_csv_preview() -> None:
    ensure_csv_import_file()
    rows = read_csv_rows()
    if not rows:
        print(f"\n  找不到 CSV 檔：{CSV_IMPORT_FILE}\n")
        _pause()
        return
    print("\n" + preview_csv_rows(rows) + "\n")
    _pause()


def import_csv_menu() -> None:
    ensure_csv_import_file()
    rows = read_csv_rows()
    if not rows:
        _error(f"找不到 CSV 檔：{CSV_IMPORT_FILE}")
        _pause()
        return
    _, errors = import_csv_to_menu(rows)
    if errors:
        print("\n  CSV 匯入完成，但有錯誤：")
        for error in errors:
            print(f"  - {error}")
        print()
        _pause()
        return
    _info(f"已匯入 CSV 到 {MENU_DATA_FILE}")


def download_csv_template() -> None:
    write_csv_template_from_menu()
    ensure_csv_import_file()
    if hasattr(os, "startfile"):
        os.startfile(str(CSV_IMPORT_FILE))
    else:
        webbrowser.open(CSV_IMPORT_FILE.as_uri())
    _info(f"已產生 CSV 範本：{CSV_IMPORT_FILE}")


def export_current_menu_csv() -> None:
    export_path = write_csv_export_from_menu()
    if hasattr(os, "startfile"):
        os.startfile(str(export_path))
    else:
        webbrowser.open(export_path.as_uri())
    _info(f"已匯出目前內容：{CSV_EXPORT_FILE}")


def choose_hotkey_style(state: MenuState) -> bool:
    choices = [
        {"name": "📎  標準", "value": "classic"},
        {"name": "✂️  簡潔", "value": "compact"},
        {"name": "🪟  框線", "value": "boxed"},
    ]
    result = ask_fuzzy(choices, "快速鍵樣式", get_prompt_style(state.theme_name))
    if not isinstance(result, dict):
        return False
    state.set_hotkey_style(result["value"])
    return True


def choose_hotkey_profile(state: MenuState) -> bool:
    return edit_hotkeys(state)


def show_about() -> None:
    print(
        "\n"
        f"  📘 功能說明 v{APP_VERSION}\n"
        "  ─────────────────────────────────────────────\n"
        "  這是一個用鍵盤操作的終端機選單工具。\n"
        "  主要用途是：快速切換常用功能、執行腳本、管理選單內容。\n"
        "\n"
        "  【技術】\n"
        "  • Python 3.12\n"
        "  • InquirerPy + prompt_toolkit\n"
        "  • csv / json 標準函式庫\n"
        "  • JSON 設定檔與資料檔\n"
        "  • Git 版本管理\n"
        "  • MIT 授權\n"
        "\n"
        "  【功能】\n"
        "  • 樣式切換：切換整體顏色主題。\n"
        "  • 快速鍵樣式：只改畫面上的提示文字長相，不改實際按鍵。\n"
        "  • 快速鍵修改：切換上一頁 / 下一頁的實際按鍵組合。\n"
        "  • CSV 匯入：用 CSV 批次建立或更新選單。\n"
        "  • CSV 預覽：先看 CSV 會怎麼匯入，不會修改資料。\n"
        "  • CSV 範本：下載目前範本。\n"
        "  • CSV 匯出：把目前選單內容輸出成 CSV。\n"
        "  • 功能說明：顯示本專案用途、技術與版本。\n"
        "  • 編輯選單資料：用內建編輯器修改選單名稱與內容，按 Ctrl+S 存檔。\n"
        "  • 快速鍵修改：直接編輯上一頁 / 下一頁按鍵。\n"
        "  • 開發工具：執行 .py / .bat / .jar 檔。\n"
        "  • 常用網址：直接開啟網站。\n"
        "  • 快速筆記：啟動筆記腳本。\n"
        "\n"
        "  【版本演進】\n"
        f"  • {APP_VERSION}：加入 CSV 匯入/匯出與可編輯快捷鍵。\n"
        "  • v0.4.0：快捷鍵樣式與快捷鍵切換。\n"
        "  • v0.3.0：內建選單編輯器與資料檔化。\n"
        "  • v0.2.0：主題切換與自訂配色。\n"
        "  • v0.1.0：基本 fuzzy 選單。\n"
    )
    _pause()


def execute_action(action: dict, state: MenuState) -> bool:
    action_type = action.get("type")

    if action_type == "exit":
        _info("再見！")
        return True

    if action_type == "theme":
        theme_name = action.get("theme", "dark")
        if theme_name == "custom":
            ensure_custom_theme_file()
        state.set_theme(theme_name)
        _info(f"已切換樣式：{get_theme_definition(theme_name)['label']}")
        return False

    if action_type == "style_file":
        open_custom_style_file()
        _info(f"已開啟：{STYLE_FILE}")
        return False

    if action_type == "menu_file":
        open_menu_data_file()
        _info(f"已開啟：{MENU_DATA_FILE}（按 Ctrl+S 存檔）")
        return False

    if action_type == "edit_menu":
        saved = edit_menu_data()
        _info("已存檔 menu_data.json" if saved else "已取消編輯")
        return False

    if action_type == "csv_preview":
        show_csv_preview()
        return False

    if action_type == "csv_import":
        import_csv_menu()
        return False

    if action_type == "csv_template":
        download_csv_template()
        return False

    if action_type == "csv_export":
        export_current_menu_csv()
        return False

    if action_type == "hotkey_style":
        if choose_hotkey_style(state):
            _info(f"已切換快速鍵樣式：{state.hotkey_style}")
        return False

    if action_type == "hotkey_modify":
        if choose_hotkey_profile(state):
            _info(
                f"已切換快速鍵：上頁 {describe_hotkey_keys(state.hotkey_back_keys)} / 下頁 {describe_hotkey_keys(state.hotkey_forward_keys)}"
            )
        return False

    if action_type == "about":
        show_about()
        return False

    if action_type == "url":
        webbrowser.open(action["url"])
        _info(f"已開啟：{action['url']}")
        _pause()
        return False

    if action_type in {"py", "bat", "jar"}:
        path = _resolve_path(action["path"])
        if not path.exists():
            _error(f"找不到檔案：{path}")
            _pause()
            return False

        _info(f"執行中：{path.name}")
        try:
            if action_type == "py":
                _run_command([sys.executable, str(path)], cwd=path.parent)
            elif action_type == "bat":
                _run_command(str(path), cwd=path.parent, shell=True)
            elif action_type == "jar":
                java = shutil.which("java") or "java"
                _run_command([java, "-jar", str(path)], cwd=path.parent)
        except Exception as exc:
            _error(f"執行失敗：{exc}")
        _pause()
        return False

    _error(f"未知動作：{action_type}")
    _pause()
    return False
