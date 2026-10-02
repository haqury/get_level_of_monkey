"""Load UI font with Cyrillic / Unicode support."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from panda3d.core import DynamicTextFont, Filename, TextNode

logger = logging.getLogger(__name__)

def _bundled_font_paths() -> list[Path]:
    """Fonts shipped next to the exe / project root (assets/fonts/*.ttf)."""
    font_dir = Path.cwd() / "assets" / "fonts"
    if not font_dir.is_dir():
        return []
    return sorted(font_dir.glob("*.ttf"))

_WINDOWS_FONTS = [
    Path(r"C:/Windows/Fonts/segoeui.ttf"),
    Path(r"C:/Windows/Fonts/arial.ttf"),
    Path(r"C:/Windows/Fonts/tahoma.ttf"),
    Path(r"C:/Windows/Fonts/calibri.ttf"),
    Path(r"C:/Windows/Fonts/times.ttf"),
]


def _iter_font_paths() -> list[Path]:
    """Candidate font files, bundled first (works in exe), then OS fonts."""
    paths: list[Path] = list(_bundled_font_paths())
    if sys.platform == "win32":
        paths.extend(_WINDOWS_FONTS)
    elif sys.platform == "darwin":
        paths.extend([
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/Library/Fonts/Arial.ttf"),
        ])
    else:
        paths.extend([
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
        ])
    # Deduplicate while preserving order
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve() if path.exists() else path
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def load_cyrillic_font():
    """
    Load a Unicode-capable font for DirectGUI / OnscreenText.

    Panda3D 1.10.x expects DynamicTextFont(Filename), not DynamicTextFont().load().
    """
    for path in _iter_font_paths():
        if not path.exists():
            continue
        try:
            font = DynamicTextFont(Filename.fromOsSpecific(str(path.resolve())))
            if font and font.isValid():
                logger.info("Loaded UI font: %s", path)
                return font
            logger.warning("Font file invalid: %s", path)
        except Exception as exc:
            logger.warning("Failed to load font %s: %s", path, exc)
    logger.warning("No Unicode font found; Cyrillic may not render")
    return TextNode.getDefaultFont()


def apply_ui_font(font) -> None:
    """Apply font globally for TextNode and DirectGUI widgets."""
    if not font:
        return
    try:
        TextNode.setDefaultFont(font)
    except Exception as exc:
        logger.warning("TextNode.setDefaultFont failed: %s", exc)
    try:
        from direct.gui import DirectGuiGlobals as DGG
        DGG.setDefaultFont(font)
    except Exception as exc:
        logger.warning("DirectGuiGlobals.setDefaultFont failed: %s", exc)
