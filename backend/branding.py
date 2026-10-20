"""Where an organization's logo lives (data/brand/org_<id>.png, git-ignored) and how it's loaded."""

import os
from pathlib import Path

from config import PROJECT_DIR


def brand_dir() -> Path:
    # Tests and the demo server point this at a temp folder.
    return Path(os.getenv("THROUGH_LINE_BRAND_DIR") or PROJECT_DIR / "data" / "brand")


def load_logo(org_id: int) -> bytes | None:
    p = brand_dir() / f"org_{org_id}.png"
    return p.read_bytes() if p.exists() else None


def save_logo(org_id: int, png: bytes) -> None:
    brand_dir().mkdir(parents=True, exist_ok=True)
    (brand_dir() / f"org_{org_id}.png").write_bytes(png)
