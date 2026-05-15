from __future__ import annotations

from dataclasses import dataclass, field

from config import VALID_HOTKEY_STYLES, VALID_THEME_NAMES, load_settings, save_settings


@dataclass
class MenuState:
    settings: dict = field(default_factory=load_settings)
    theme_name: str = field(init=False)
    hotkey_style: str = field(init=False)
    hotkey_back_keys: list[str] = field(init=False)
    hotkey_forward_keys: list[str] = field(init=False)

    def __post_init__(self) -> None:
        theme_name = self.settings.get("theme", "dark")
        self.theme_name = theme_name if theme_name in VALID_THEME_NAMES else "dark"
        hotkey_style = self.settings.get("hotkey_style", "classic")
        self.hotkey_style = hotkey_style if hotkey_style in VALID_HOTKEY_STYLES else "classic"
        self.hotkey_back_keys = self._normalize_keys(self.settings.get("hotkey_back_keys"), ["alt-left"])
        self.hotkey_forward_keys = self._normalize_keys(self.settings.get("hotkey_forward_keys"), ["alt-right"])
        self.settings["theme"] = self.theme_name
        self.settings["hotkey_style"] = self.hotkey_style
        self.settings["hotkey_back_keys"] = self.hotkey_back_keys
        self.settings["hotkey_forward_keys"] = self.hotkey_forward_keys

    def _normalize_keys(self, value, fallback: list[str]) -> list[str]:
        if isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value):
            return [item.strip() for item in value]
        return list(fallback)

    def set_theme(self, theme_name: str) -> None:
        self.theme_name = theme_name if theme_name in VALID_THEME_NAMES else "dark"
        self.settings["theme"] = self.theme_name
        save_settings(self.settings)

    def set_hotkey_style(self, hotkey_style: str) -> None:
        self.hotkey_style = hotkey_style if hotkey_style in VALID_HOTKEY_STYLES else "classic"
        self.settings["hotkey_style"] = self.hotkey_style
        save_settings(self.settings)

    def set_hotkey_keys(self, back_keys: list[str], forward_keys: list[str]) -> None:
        self.hotkey_back_keys = self._normalize_keys(back_keys, ["alt-left"])
        self.hotkey_forward_keys = self._normalize_keys(forward_keys, ["alt-right"])
        self.settings["hotkey_back_keys"] = self.hotkey_back_keys
        self.settings["hotkey_forward_keys"] = self.hotkey_forward_keys
        save_settings(self.settings)
