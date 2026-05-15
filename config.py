from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_VERSION = "0.7.0"
DATA_DIR = BASE_DIR / "data"
SETTINGS_FILE = DATA_DIR / "menu_settings.json"
STYLE_FILE = DATA_DIR / "menu_theme.json"
MENU_DATA_FILE = DATA_DIR / "menu_data.json"

DEFAULT_SETTINGS = {
    "theme": "dark",
    "hotkey_style": "classic",
    "hotkey_back_keys": ["alt-left"],
    "hotkey_forward_keys": ["alt-right"],
}
VALID_THEME_NAMES = {"dark", "light", "neon", "custom"}
VALID_HOTKEY_STYLES = {"classic", "compact", "boxed"}

HOTKEY_PRESETS = {
    "arrows": {"label": "方向鍵", "back": ["alt-left"], "forward": ["alt-right"]},
    "ctrl": {"label": "Ctrl+B / Ctrl+F", "back": ["c-b"], "forward": ["c-f"]},
    "page": {"label": "PageUp / PageDown", "back": ["pageup"], "forward": ["pagedown"]},
    "vim": {"label": "Alt+H / Alt+L", "back": ["alt-h"], "forward": ["alt-l"]},
}


def _read_json(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return dict(fallback)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(fallback)
    return data if isinstance(data, dict) else dict(fallback)


def save_settings(settings: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_settings() -> dict:
    settings = {**DEFAULT_SETTINGS, **_read_json(SETTINGS_FILE, DEFAULT_SETTINGS)}
    if settings.get("theme") not in VALID_THEME_NAMES:
        settings["theme"] = DEFAULT_SETTINGS["theme"]
    if settings.get("hotkey_style") not in VALID_HOTKEY_STYLES:
        settings["hotkey_style"] = DEFAULT_SETTINGS["hotkey_style"]

    profile = settings.get("hotkey_profile")
    if not isinstance(settings.get("hotkey_back_keys"), list):
        preset = HOTKEY_PRESETS.get(profile, HOTKEY_PRESETS["arrows"])
        settings["hotkey_back_keys"] = list(preset["back"])
    if not isinstance(settings.get("hotkey_forward_keys"), list):
        preset = HOTKEY_PRESETS.get(profile, HOTKEY_PRESETS["arrows"])
        settings["hotkey_forward_keys"] = list(preset["forward"])

    settings.pop("hotkey_profile", None)
    save_settings(settings)
    return settings
