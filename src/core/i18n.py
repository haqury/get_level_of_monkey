"""Simple JSON-based localization."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SUPPORTED_LOCALES = ("en", "ru")
_DEFAULT_LOCALE = "en"

_strings: dict[str, str] = {}
_current_locale = _DEFAULT_LOCALE


def _flatten(data: dict, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(_flatten(value, full_key))
        else:
            out[full_key] = str(value)
    return out


def _locale_path(locale: str) -> Path:
    return Path("config/locale") / f"{locale}.json"


def load_locale(locale: str) -> None:
    """Load translation strings for the given locale."""
    global _strings, _current_locale
    if locale not in SUPPORTED_LOCALES:
        locale = _DEFAULT_LOCALE
    path = _locale_path(locale)
    if not path.exists():
        logger.warning("Locale file not found: %s", path)
        if locale != _DEFAULT_LOCALE:
            load_locale(_DEFAULT_LOCALE)
            return
        _strings = {}
        _current_locale = locale
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _strings = _flatten(data)
    _current_locale = locale
    logger.info("Locale loaded: %s (%d strings)", locale, len(_strings))


def get_locale() -> str:
    return _current_locale


def t(key: str, **kwargs: Any) -> str:
    """Translate key; missing keys fall back to English then to the key itself."""
    text = _strings.get(key)
    if text is None and _current_locale != _DEFAULT_LOCALE:
        fallback_path = _locale_path(_DEFAULT_LOCALE)
        if fallback_path.exists():
            try:
                with open(fallback_path, "r", encoding="utf-8") as f:
                    fallback = _flatten(json.load(f))
                text = fallback.get(key)
            except Exception:
                pass
    if text is None:
        text = key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def resolve_dialog(dialog: dict) -> dict:
    """Resolve text/title/options from i18n keys for dialog_box.show()."""
    resolved = dict(dialog)
    if "text_key" in resolved:
        resolved["text"] = t(resolved.pop("text_key"))
    if "title_key" in resolved:
        resolved["title"] = t(resolved.pop("title_key"))
    if "options" not in resolved and "option_keys" in resolved:
        resolved["options"] = [
            (t(text_key), callback)
            for text_key, callback in resolved.pop("option_keys")
        ]
    return resolved
