from __future__ import annotations

from InquirerPy.prompts.fuzzy import FuzzyPrompt

NAV_BACK = object()
NAV_FORWARD = object()

KEY_LABELS = {
    "alt-left": "Alt+←",
    "alt-right": "Alt+→",
    "c-b": "Ctrl+B",
    "c-f": "Ctrl+F",
    "pageup": "PageUp",
    "pagedown": "PageDown",
    "alt-h": "Alt+H",
    "alt-l": "Alt+L",
}


def describe_hotkey_keys(keys: list[str]) -> str:
    labels = [KEY_LABELS.get(key, key) for key in keys if key]
    return "/".join(labels) if labels else "未設定"


def normalize_key_list(text: str) -> list[str]:
    return [part.strip() for part in text.replace("，", ",").split(",") if part.strip()]


class NavigatorFuzzyPrompt(FuzzyPrompt):
    def __init__(
        self,
        *args,
        back_result=NAV_BACK,
        forward_result=NAV_FORWARD,
        back_keys=None,
        forward_keys=None,
        **kwargs,
    ):
        self._back_result = back_result
        self._forward_result = forward_result
        super().__init__(*args, **kwargs)
        self.kb_maps = {
            "nav-back": [{"key": key} for key in (back_keys or ["alt-left"])],
            "nav-forward": [{"key": key} for key in (forward_keys or ["alt-right"])],
        }
        self.kb_func_lookup = {
            "nav-back": [{"func": self._handle_nav_back}],
            "nav-forward": [{"func": self._handle_nav_forward}],
        }

    def _handle_nav_back(self, event) -> None:
        event.app.exit(result=self._back_result)

    def _handle_nav_forward(self, event) -> None:
        event.app.exit(result=self._forward_result)


def ask_fuzzy(
    choices: list,
    message: str,
    style,
    back_keys: list[str] | None = None,
    forward_keys: list[str] | None = None,
) -> dict | object | None:
    prompt = NavigatorFuzzyPrompt(
        message=message,
        choices=choices,
        match_exact=False,
        max_height="60%",
        instruction=" (輸入過濾)",
        long_instruction=f" {describe_hotkey_keys(back_keys or ['alt-left'])} 上頁 / {describe_hotkey_keys(forward_keys or ['alt-right'])} 下頁",
        style=style,
        vi_mode=False,
        back_keys=back_keys,
        forward_keys=forward_keys,
    )

    try:
        return prompt.execute()
    except KeyboardInterrupt:
        return None
