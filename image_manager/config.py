from __future__ import annotations

import json
from pathlib import Path

DEFAULT_CONFIG = {
    "image_dir": "C:/Users/YourName/Pictures/IM",
    "db_path": "image_index.db",
    "top_k": 24,
    "enable_semantic": True,
    "enable_caption": True,
    "enable_ocr": True,
}


def load_config(config_path: str | Path = ".image_manager_config.json") -> dict:
    path = Path(config_path)
    if not path.exists():
        return DEFAULT_CONFIG.copy()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return DEFAULT_CONFIG.copy()

    merged = DEFAULT_CONFIG.copy()
    merged.update({k: v for k, v in data.items() if k in DEFAULT_CONFIG})
    return merged


def save_config(config: dict, config_path: str | Path = ".image_manager_config.json") -> None:
    path = Path(config_path)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
