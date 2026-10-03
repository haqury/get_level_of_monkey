"""Load BrainLink Client settings into the game brainlink config section."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

FAULT_FIELDS = (
    "attention", "meditation", "signal", "delta", "theta",
    "low_alpha", "high_alpha", "low_beta", "high_beta", "low_gamma", "high_gamma",
)

EXPORT_FILENAME = "brainlink_export_for_game.json"
EXPORT_POLL_INTERVAL_S = 0.05
EXPORT_WAIT_SECONDS = 1.25

# Keys merged from client export / disk — game-only flags are never touched here.
SYNC_FROM_CLIENT_KEYS = (
    "prediction_mode",
    "history_path",
    "model_path",
    "confidence_threshold",
    "prediction_weights",
    "base_fault",
    "multi_fault",
    "multi_count",
)


def _appdata_export_path() -> Path:
    return Path(os.environ.get("APPDATA", os.path.expanduser("~"))) / "BrainLink" / EXPORT_FILENAME


def _read_json(path: Path) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except FileNotFoundError:
        return None
    except Exception as e:
        logger.warning("Failed to read %s: %s", path, e)
        return None


def _normalize_base_fault(raw: Any) -> Optional[dict]:
    if not isinstance(raw, dict):
        return None
    try:
        return {field: int(raw[field]) for field in FAULT_FIELDS}
    except (KeyError, TypeError, ValueError):
        return None


def _parse_fault_config_bundle(path: Path) -> Dict[str, Any]:
    """Read base_fault, multi_fault, multi_count from client fault JSON."""
    bundle: Dict[str, Any] = {}
    data = _read_json(path)
    if not data:
        return bundle
    if isinstance(data.get("base_fault"), dict):
        base = _normalize_base_fault(data["base_fault"])
        if base:
            bundle["base_fault"] = base
    elif "attention" in data and "meditation" in data:
        partial = {k: data[k] for k in FAULT_FIELDS if k in data}
        base = _normalize_base_fault(partial)
        if base:
            bundle["base_fault"] = base
    if isinstance(data.get("multi_fault"), dict):
        multi = _normalize_base_fault(data["multi_fault"])
        if multi:
            bundle["multi_fault"] = multi
    if "multi_count" in data:
        try:
            bundle["multi_count"] = max(1, int(data.get("multi_count") or 1))
        except (TypeError, ValueError):
            pass
    return bundle


def _load_fault_bundle_from_install_config(config_dir: Path) -> Dict[str, Any]:
    for name in ("config.json", "def_conf.json"):
        bundle = _parse_fault_config_bundle(config_dir / name)
        if bundle:
            return bundle
    return {}


def _load_history_path_from_client(config_dir: Path, client_root: Path) -> Optional[str]:
    data = _read_json(config_dir / "history_config.json")
    if data:
        raw = (data.get("history_path") or "").strip()
        if raw:
            return str(Path(raw).resolve())
    default = client_root / "data" / "history.json"
    if default.exists():
        return str(default.resolve())
    return None


def _resolve_fault_config_path(
    client_root: Optional[Path],
    export_doc: Optional[dict],
) -> Optional[Path]:
    candidates: list[Path] = []
    if export_doc:
        raw = (export_doc.get("fault_config_path") or "").strip()
        if raw:
            candidates.append(Path(raw))
    if client_root:
        ptr = _read_json(client_root / "config" / "fault_config_path.json")
        if ptr:
            raw = (ptr.get("fault_config_path") or "").strip()
            if raw:
                candidates.append(Path(raw))
    for path in candidates:
        try:
            resolved = path.resolve()
            if resolved.is_file():
                return resolved
        except OSError:
            continue
    return None


def _normalize_prediction_weights(raw: Any) -> Optional[list]:
    if not isinstance(raw, (list, tuple)):
        return None
    try:
        weights = [float(x) for x in raw[:5]]
    except (TypeError, ValueError):
        return None
    if len(weights) < 4:
        weights.extend([1.0] * (4 - len(weights)))
    return weights[:5] if len(weights) >= 5 else weights[:4]


def _brainlink_overrides_from_export(export_doc: dict) -> Optional[Dict[str, Any]]:
    if int(export_doc.get("export_version", 0)) < 1:
        return None
    bl = export_doc.get("brainlink")
    if not isinstance(bl, dict):
        return None

    overrides: Dict[str, Any] = {}
    base_fault = _normalize_base_fault(bl.get("base_fault"))
    if not base_fault:
        logger.warning("Export v1 missing valid brainlink.base_fault (11 int fields)")
        return None

    overrides["base_fault"] = base_fault

    mode = str(bl.get("prediction_mode", "")).strip().lower()
    if mode in ("base", "ml"):
        overrides["prediction_mode"] = mode

    for key in ("history_path", "model_path"):
        val = bl.get(key)
        if val is not None and str(val).strip():
            overrides[key] = str(val).strip()

    if "confidence_threshold" in bl:
        try:
            overrides["confidence_threshold"] = float(bl["confidence_threshold"])
        except (TypeError, ValueError):
            pass

    weights = _normalize_prediction_weights(bl.get("prediction_weights"))
    if weights is not None:
        overrides["prediction_weights"] = weights

    multi_fault = _normalize_base_fault(bl.get("multi_fault"))
    if multi_fault:
        overrides["multi_fault"] = multi_fault
    if "multi_count" in bl:
        try:
            overrides["multi_count"] = max(1, int(bl.get("multi_count") or 1))
        except (TypeError, ValueError):
            pass

    return overrides


def _fallback_disk_overrides(
    client_root: Optional[Path],
    export_doc: Optional[dict],
) -> Dict[str, Any]:
    overrides: Dict[str, Any] = {}
    if not client_root:
        return overrides

    config_dir = client_root / "config"
    fault_path = _resolve_fault_config_path(client_root, export_doc)
    bundle = _parse_fault_config_bundle(fault_path) if fault_path else {}
    if not bundle:
        bundle = _load_fault_bundle_from_install_config(config_dir)
    if bundle.get("base_fault"):
        overrides["base_fault"] = bundle["base_fault"]
        logger.info(
            "BrainLink base_fault from disk (path=%s, low_alpha=%s)",
            fault_path or config_dir,
            overrides["base_fault"].get("low_alpha"),
        )
    if bundle.get("multi_fault"):
        overrides["multi_fault"] = bundle["multi_fault"]
    if "multi_count" in bundle:
        overrides["multi_count"] = bundle["multi_count"]

    history_path = _load_history_path_from_client(config_dir, client_root)
    if history_path:
        overrides["history_path"] = history_path

    return overrides


def merge_into_brainlink_section(bl_section: dict, overrides: Dict[str, Any]) -> None:
    for key in SYNC_FROM_CLIENT_KEYS:
        if key not in overrides:
            continue
        val = overrides[key]
        if key in ("base_fault", "multi_fault") and isinstance(val, dict):
            merged = dict(bl_section.get(key) or {})
            merged.update(val)
            bl_section[key] = merged
        elif val is not None and val != "":
            bl_section[key] = val


def resolve_client_root(launcher) -> Optional[Path]:
    if launcher is None:
        return None
    path = getattr(launcher, "brainlink_path", None)
    if path:
        root = Path(path)
        if (root / "main.py").exists():
            return root
    find = getattr(launcher, "find_brainlink_client", None)
    if find:
        return find()
    return None


def _export_refresh_state(export_path: Path) -> Tuple[float, float]:
    mtime = export_path.stat().st_mtime if export_path.exists() else 0.0
    updated_at = 0.0
    if export_path.exists():
        doc = _read_json(export_path)
        if doc:
            try:
                updated_at = float(doc.get("updated_at") or 0.0)
            except (TypeError, ValueError):
                updated_at = 0.0
    return mtime, updated_at


def _export_was_refreshed(
    export_path: Path,
    mtime_before: float,
    updated_at_before: float,
) -> bool:
    if not export_path.exists():
        return False
    mtime_after, updated_at_after = _export_refresh_state(export_path)
    if mtime_after > mtime_before + 1e-6:
        return True
    if updated_at_after > updated_at_before + 1e-6:
        return True
    return False


def request_client_export(
    base,
    wait_seconds: float = EXPORT_WAIT_SECONDS,
) -> bool:
    """Ask running BrainLink Client to refresh export (COMMAND_TYPE 9) and poll file."""
    input_manager = getattr(base, "input_manager", None)
    if not input_manager:
        return False
    client = getattr(input_manager, "brainlink", None)
    if not client or not client.is_connected():
        return False
    send = getattr(client, "send_export_settings_command", None)
    if not send:
        return False

    export_path = _appdata_export_path()
    mtime_before, updated_at_before = _export_refresh_state(export_path)

    if not send():
        return False

    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if _export_was_refreshed(export_path, mtime_before, updated_at_before):
            logger.debug("BrainLink export refreshed after type 9")
            return True
        time.sleep(EXPORT_POLL_INTERVAL_S)

    if export_path.exists():
        logger.warning(
            "BrainLink export type 9 sent but file not refreshed within %.2fs",
            wait_seconds,
        )
        return True
    return False


def sync_brainlink_config_from_client(base) -> bool:
    """
    Pull BrainLink settings from the client into base.game_config['brainlink'] (in memory).
    Prefers export v1 (after type 9); falls back to fault_config_path / install config.
    """
    if not hasattr(base, "game_config"):
        return False

    export_path = _appdata_export_path()
    mtime_before, updated_at_before = _export_refresh_state(export_path)

    shm_client = None
    input_manager = getattr(base, "input_manager", None)
    if input_manager:
        shm_client = getattr(input_manager, "brainlink", None)
    connected = bool(shm_client and shm_client.is_connected())

    requested_export = False
    export_refreshed = False
    if connected:
        requested_export = request_client_export(base)
        export_refreshed = _export_was_refreshed(export_path, mtime_before, updated_at_before)

    export_doc = _read_json(export_path)
    launcher = getattr(base, "brainlink_launcher", None)
    client_root = resolve_client_root(launcher)

    bl_section = base.game_config.setdefault("brainlink", {})
    overrides: Dict[str, Any] = {}
    source = "none"

    use_export = bool(export_doc and int(export_doc.get("export_version", 0)) >= 1)
    if requested_export and not export_refreshed:
        use_export = False
        logger.warning("Skipping stale export after type 9; using disk fallback for fault")

    disk = _fallback_disk_overrides(
        client_root,
        export_doc if use_export else None,
    )

    if use_export and export_doc:
        from_export = _brainlink_overrides_from_export(export_doc)
        if from_export:
            overrides = from_export
            source = "export"
            bf = overrides.get("base_fault") or {}
            logger.info(
                "BrainLink settings from export (low_alpha=%s, multi_count=%s, fault_config_path=%s)",
                bf.get("low_alpha"),
                overrides.get("multi_count"),
                export_doc.get("fault_config_path"),
            )

    for key in ("base_fault", "multi_fault", "multi_count", "history_path"):
        if key not in overrides and key in disk:
            overrides[key] = disk[key]
            if source == "none":
                source = "disk_fault"

    # multi_count / multi_fault: prefer values from persisted fault JSON (export path or disk)
    fault_file = None
    if export_doc:
        fp_raw = (export_doc.get("fault_config_path") or "").strip()
        if fp_raw:
            fault_file = Path(fp_raw)
    if fault_file is None and client_root:
        fault_file = _resolve_fault_config_path(client_root, export_doc)
    if fault_file is not None:
        try:
            file_bundle = _parse_fault_config_bundle(fault_file)
            for key in ("multi_count", "multi_fault"):
                if key in file_bundle:
                    overrides[key] = file_bundle[key]
        except OSError:
            pass

    if not overrides:
        logger.debug("No BrainLink client settings to sync")
        return False

    merge_into_brainlink_section(bl_section, overrides)
    logger.info("BrainLink sync complete (source=%s, keys=%s)", source, list(overrides.keys()))
    return True
