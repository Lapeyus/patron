"""Image discovery helpers for locating screenshot inputs."""

from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

DEFAULT_EXTENSIONS: Sequence[str] = (
    ".png",
    ".jpg",
    ".jpeg",
    ".heic",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
)


def discover_images(
    root: Path,
    pattern: str = "Screenshot_*",
    *,
    extensions: Sequence[str] | None = DEFAULT_EXTENSIONS,
) -> List[Path]:
    """Recursively scan *root* for files matching *pattern* and extensions."""

    root = root.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        return []

    extension_set = {ext.lower() for ext in extensions} if extensions else None

    matches: List[Path] = []
    for candidate in root.rglob(pattern):
        if not candidate.is_file():
            continue
        if extension_set and candidate.suffix.lower() not in extension_set:
            continue
        matches.append(candidate)

    return sorted(matches)
