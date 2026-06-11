from __future__ import annotations

import json
from pathlib import Path

from .models import PhotoItem
from .paths import Paths

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp"}


def build_photo_manifest(paths: Paths) -> list[PhotoItem]:
    if not paths.photo_dir.exists():
        return []
    files = sorted(p for p in paths.photo_dir.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED)
    return [
        PhotoItem(index=i + 1, path=p.resolve(), filename=p.name, marker=f"[PHOTO: {i + 1:02d}]", caption=f"사진 {i + 1:02d}")
        for i, p in enumerate(files)
    ]


def write_photo_manifest(paths: Paths, photos: list[PhotoItem]) -> Path:
    out = paths.article_file("photo_manifest.json")
    out.write_text(json.dumps([p.to_dict() for p in photos], ensure_ascii=False, indent=2), encoding="utf-8")
    return out

