#!/usr/bin/env python3
"""Augment OCR JSON files under newapp/PATRON with metadata hints."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

APP_ROOT = Path(__file__).resolve().parent
PATRON_ROOT = APP_ROOT / "PATRON"
EMOJI_PATTERN = re.compile(
    r"[\u2600-\u27BF\u2B50\u231A-\u231B\u23E9-\u23EC\u23F0\u23F3\u25FD-\u25FE"
    r"\U0001F004\U0001F0CF\U0001F170-\U0001F251\U0001F300-\U0001FAD6"
    r"\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\U0001FA70-\U0001FAFF]+",
    flags=re.UNICODE,
)
DIGIT_PATTERN = re.compile(r"\d+")
PAREN_CONTENT_PATTERN = re.compile(r"\(([^()]+)\)")


def discover_json_files(root: Path) -> List[Path]:
    root = root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"Root path not found: {root}")
    return sorted(root.rglob("Screenshot_*.json"))


def _prefer_parenthetical(text: str) -> str:
    """Return the inner text of the first parentheses if available."""
    match = PAREN_CONTENT_PATTERN.search(text)
    if match:
        inner = match.group(1).strip()
        if inner:
            return inner
    return text.strip()


def _strip_prefix(folder: str) -> str:
    parts = folder.split("-", 1)
    base = parts[1].strip() if len(parts) == 2 else folder
    return _prefer_parenthetical(base)


def _separate_emojis(text: str) -> tuple[str, str]:
    emojis = "".join(EMOJI_PATTERN.findall(text))
    base = EMOJI_PATTERN.sub("", text).strip()
    digits_only = DIGIT_PATTERN.fullmatch(base)
    if digits_only and emojis:
        digits = digits_only.group(0)
        if emojis.endswith(digits):
            emojis = emojis[:-len(digits)]
        base = base[len(digits):].strip()
    return (base or text.strip(), emojis)


def derive_metadata(path: Path) -> tuple[Dict[str, str], str]:
    relative_parts = path.relative_to(PATRON_ROOT).parts
    folders = list(relative_parts[:-1])

    metadata: Dict[str, str] = {}

    if len(folders) == 1:
        metadata["Recomendacion"] = "true"
    else:
        for folder in folders[:-1]:
            label_raw = _strip_prefix(folder)
            label_clean, emojis = _separate_emojis(label_raw)
            key = label_clean or label_raw
            metadata[key] = label_clean or label_raw
            if emojis:
                metadata[f"{key}_emoji"] = emojis

    profile = ""
    if folders:
        profile_base = _strip_prefix(folders[-1])
        profile_clean, profile_emoji = _separate_emojis(profile_base)
        profile = profile_clean
        if profile_emoji:
            metadata["profile_emoji"] = profile_emoji
    return metadata, profile


def process_json_file(json_path: Path, indent: int) -> None:
    data = json.loads(json_path.read_text())
    metadata, profile = derive_metadata(json_path)
    metadata_block = data.setdefault("metadata", {})

    # Drop stale *_emoji entries that are no longer produced.
    for key in list(metadata_block.keys()):
        if key.endswith("_emoji") and key not in metadata:
            metadata_block.pop(key, None)

    metadata_block.update(metadata)
    metadata_block = {
        k: v
        for k, v in metadata_block.items()
        if k.strip("- ").strip() and v.strip("- ").strip()
    }
    data["metadata"] = metadata_block
    if profile:
        data["profile"] = profile
    json_path.write_text(json.dumps(data, indent=indent, ensure_ascii=False))
    print(f"Updated {json_path}")


def main() -> None:
    files = discover_json_files(PATRON_ROOT)
    if not files:
        raise SystemExit(f"No Screenshot_*.json files found under {PATRON_ROOT}")

    for json_file in files:
        process_json_file(json_file, indent=2)


if __name__ == "__main__":
    main()
