from __future__ import annotations

import json

from InquirerPy import get_style
from prompt_toolkit.styles import Style as PromptToolkitStyle

from config import STYLE_FILE

BUILTIN_THEMES = {
    "dark": {
        "label": "深色",
        "ui": {"accent": "#5fd7ff", "border": "#333333"},
        "prompt": {
            "questionmark": "#5fd7ff bold",
            "answermark": "#5fff87",
            "answer": "#5fff87 bold",
            "input": "#ffffff",
            "question": "#5fd7ff bold",
            "instruction": "#555555 italic",
            "fuzzy_prompt": "#5fd7ff bold",
            "fuzzy_info": "#555555 italic",
            "fuzzy_border": "#333333",
            "fuzzy_match": "#ff5f87 bold underline",
            "marker": "#5fd7ff",
            "pointer": "#ff5f87 bold",
        },
    },
    "light": {
        "label": "淺色",
        "ui": {"accent": "#005f87", "border": "#c8c8c8"},
        "prompt": {
            "questionmark": "#005f87 bold",
            "answermark": "#00875f",
            "answer": "#00875f bold",
            "input": "#202020",
            "question": "#005f87 bold",
            "instruction": "#7a7a7a italic",
            "fuzzy_prompt": "#005f87 bold",
            "fuzzy_info": "#7a7a7a italic",
            "fuzzy_border": "#c8c8c8",
            "fuzzy_match": "#d7005f bold underline",
            "marker": "#005f87",
            "pointer": "#d7005f bold",
        },
    },
    "neon": {
        "label": "霓虹",
        "ui": {"accent": "#ff5fff", "border": "#7a00ff"},
        "prompt": {
            "questionmark": "#ff5fff bold",
            "answermark": "#00ffaf",
            "answer": "#00ffaf bold",
            "input": "#ffffff",
            "question": "#ff5fff bold",
            "instruction": "#7f7f7f italic",
            "fuzzy_prompt": "#ff5fff bold",
            "fuzzy_info": "#7f7f7f italic",
            "fuzzy_border": "#7a00ff",
            "fuzzy_match": "#00ffaf bold underline",
            "marker": "#ff5fff",
            "pointer": "#00ffaf bold",
        },
    },
}

DEFAULT_CUSTOM_THEME = {
    "label": "自訂",
    "ui": {"accent": "#ffd700", "border": "#666666"},
    "prompt": {
        "questionmark": "#ffd700 bold",
        "answermark": "#00d7af",
        "answer": "#00d7af bold",
        "input": "#ffffff",
        "question": "#ffd700 bold",
        "instruction": "#808080 italic",
        "fuzzy_prompt": "#ffd700 bold",
        "fuzzy_info": "#808080 italic",
        "fuzzy_border": "#666666",
        "fuzzy_match": "#ff5f87 bold underline",
        "marker": "#ffd700",
        "pointer": "#ff5f87 bold",
    },
}


def merge_dict(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def ensure_custom_theme_file() -> None:
    STYLE_FILE.parent.mkdir(exist_ok=True)
    if STYLE_FILE.exists():
        return
    STYLE_FILE.write_text(
        json.dumps(DEFAULT_CUSTOM_THEME, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_custom_theme() -> dict:
    ensure_custom_theme_file()
    try:
        data = json.loads(STYLE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("custom theme must be a JSON object")
    except Exception:
        return dict(DEFAULT_CUSTOM_THEME)
    return merge_dict(DEFAULT_CUSTOM_THEME, data)


def get_theme_definition(theme_name: str) -> dict:
    if theme_name == "custom":
        return load_custom_theme()
    return BUILTIN_THEMES.get(theme_name, BUILTIN_THEMES["dark"])


def get_ui_style(theme_name: str):
    theme = get_theme_definition(theme_name)
    ui = theme.get("ui", {})
    accent = ui.get("accent", "#5fd7ff")
    return PromptToolkitStyle.from_dict(
        {
            "header.title": f"{accent} bold",
            "header.path": accent,
            "header.hint": f"{accent} italic",
            "header.border": ui.get("border", "#333333"),
        }
    )


def get_prompt_style(theme_name: str):
    return get_style(get_theme_definition(theme_name)["prompt"], style_override=False)
