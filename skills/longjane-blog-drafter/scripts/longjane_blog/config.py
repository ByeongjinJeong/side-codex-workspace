from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    naver_client_id: str = ""
    naver_client_secret: str = ""
    naver_searchad_access_license: str = ""
    naver_searchad_secret_key: str = ""
    naver_searchad_customer_id: str = ""


def load_config() -> Config:
    load_dotenv(Path.cwd() / ".env")
    return Config(
        naver_client_id=os.environ.get("NAVER_CLIENT_ID", ""),
        naver_client_secret=os.environ.get("NAVER_CLIENT_SECRET", ""),
        naver_searchad_access_license=os.environ.get("NAVER_SEARCHAD_ACCESS_LICENSE", ""),
        naver_searchad_secret_key=os.environ.get("NAVER_SEARCHAD_SECRET_KEY", ""),
        naver_searchad_customer_id=os.environ.get("NAVER_SEARCHAD_CUSTOMER_ID", ""),
    )


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
