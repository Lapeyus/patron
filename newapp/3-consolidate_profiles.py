#!/usr/bin/env python3
"""Consolidate duplicated profile JSON files under newapp/PATRON."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

APP_ROOT = Path(__file__).resolve().parent
DEFAULT_ROOT = APP_ROOT / "PATRON"
DEFAULT_OUTPUT = APP_ROOT / "consolidated_profiles.json"
MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".heic",
    ".mp4",
    ".mov",
    ".m4v",
    ".avi",
    ".mkv",
    ".webm",
}
MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".bmp",
    ".heic",
    ".mp4",
    ".mov",
    ".m4v",
    ".avi",
    ".mkv",
    ".webm",
}


def discover_json_files(root: Path) -> List[Path]:
    root = root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"Root path not found: {root}")
    return sorted(p for p in root.rglob("Screenshot_*.json") if p.is_file())


PAREN_CONTENT_PATTERN = re.compile(r"\(([^()]+)\)")


def _prefer_parenthetical(text: str) -> str:
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


def _normalize_string(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
    return None


def canonical_profile(path: Path, payload: Dict[str, Any]) -> Tuple[str, str]:
    metadata = payload.get("metadata") or {}
    structured = payload.get("structured_data") or {}
    candidates = [
        payload.get("profile"),
        structured.get("name") if isinstance(structured, dict) else None,
        metadata.get("profile"),
        metadata.get("Recomendacion"),
    ]
    for candidate in candidates:
        normalized = _normalize_string(candidate)
        if normalized and normalized.lower() != "true":
            return normalized.casefold(), normalized
    folder_name = _strip_prefix(path.parent.name)
    fallback = _normalize_string(folder_name) or path.stem
    return fallback.casefold(), fallback


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set)):
        return len(value) == 0
    if isinstance(value, dict):
        return len(value) == 0
    return False


def _serialize_for_set(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _merge_dict(
    target: Dict[str, Any],
    incoming: Dict[str, Any],
    conflicts: List[Dict[str, Any]],
    path: List[str],
    source: str,
) -> None:
    for key, value in incoming.items():
        if _is_blank(value):
            continue
        field_path = path + [key]
        if isinstance(value, dict):
            current = target.get(key)
            if current is None or not isinstance(current, dict):
                if current is not None and current != value:
                    conflicts.append(
                        {
                            "field": ".".join(field_path),
                            "existing": current,
                            "candidate": value,
                            "source": source,
                        }
                    )
                    continue
                target[key] = {}
            _merge_dict(target[key], value, conflicts, field_path, source)
        elif isinstance(value, list):
            current = target.setdefault(key, [])
            if not isinstance(current, list):
                conflicts.append(
                    {
                        "field": ".".join(field_path),
                        "existing": current,
                        "candidate": value,
                        "source": source,
                    }
                )
                continue
            seen = {_serialize_for_set(item) for item in current}
            for item in value:
                marker = _serialize_for_set(item)
                if marker not in seen:
                    current.append(item)
                    seen.add(marker)
        else:
            if key not in target or _is_blank(target[key]):
                target[key] = value
            elif target[key] != value:
                conflicts.append(
                    {
                        "field": ".".join(field_path),
                        "existing": target[key],
                        "candidate": value,
                        "source": source,
                    }
                )


def consolidate_profiles(files: List[Path], root: Path) -> Dict[str, Any]:
    buckets: Dict[str, Dict[str, Any]] = {}
    for json_file in files:
        payload = json.loads(json_file.read_text())
        canonical_key, display_name = canonical_profile(json_file, payload)
        rel_path = str(json_file.relative_to(root))
        bucket = buckets.setdefault(
            canonical_key,
            {
                "profile": display_name,
                "sources": [],
                "raw_responses": [],
                "merged_metadata": {},
                "merged_structured_data": {},
                "conflicts": [],
                "media": [],
                "_media_seen": set(),
            },
        )
        # prefer earlier display name unless empty, otherwise keep first seen
        if not bucket["profile"] and display_name:
            bucket["profile"] = display_name
        image_path_raw = payload.get("image") or payload.get("ocr")
        exclude_media: Set[str] = set()
        if image_path_raw:
            try:
                exclude_media.add(str(Path(image_path_raw).resolve()))
            except FileNotFoundError:
                exclude_media.add(str(Path(image_path_raw)))
        profile_folder = json_file.parent
        media_items = _list_media_files(profile_folder, root, exclude_media)
        entry = {
            "path": rel_path,
            "folders": list(json_file.relative_to(root).parts[:-1]),
            "ocr": image_path_raw,
            "media": media_items,
            "raw_response": payload.get("raw_response"),
        }
        bucket["sources"].append(entry)
        for media_item in media_items:
            if media_item not in bucket["_media_seen"]:
                bucket["media"].append(media_item)
                bucket["_media_seen"].add(media_item)
        raw_text = payload.get("raw_response")
        if raw_text and raw_text not in bucket["raw_responses"]:
            bucket["raw_responses"].append(raw_text)
        metadata = payload.get("metadata")
        if isinstance(metadata, dict):
            _merge_dict(
                bucket["merged_metadata"],
                metadata,
                bucket["conflicts"],
                ["metadata"],
                rel_path,
            )
        structured = payload.get("structured_data")
        if isinstance(structured, dict):
            _merge_dict(
                bucket["merged_structured_data"],
                structured,
                bucket["conflicts"],
                ["structured_data"],
                rel_path,
            )
    profiles = []
    for key in sorted(buckets.keys()):
        bucket = buckets[key]
        profiles.append(
            {
                "profile": bucket["profile"],
                "occurrence_count": len(bucket["sources"]),
                "sources": bucket["sources"],
                "raw_responses": bucket["raw_responses"],
                "merged_metadata": bucket["merged_metadata"] or None,
                "merged_structured_data": bucket["merged_structured_data"] or None,
                "conflicts": bucket["conflicts"] or None,
                "media": bucket["media"],
            }
        )
    payload = {
        "summary": {
            "root": str(root),
            "total_files": len(files),
            "unique_profiles": len(profiles),
        },
        "profiles": profiles,
    }
    return payload


def _list_media_files(folder: Path, root: Path, exclude: Set[str]) -> List[str]:
    media: List[str] = []
    if not folder.exists():
        return media
    for candidate in sorted(folder.rglob("*")):
        if not candidate.is_file():
            continue
        if candidate.suffix.lower() not in MEDIA_EXTENSIONS:
            continue
        try:
            candidate_resolved = str(candidate.resolve())
        except FileNotFoundError:
            candidate_resolved = str(candidate)
        if candidate_resolved in exclude:
            continue
        try:
            rel = str(candidate.relative_to(root))
        except ValueError:
            rel = str(candidate)
        media.append(rel)
    return media


def slugify(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    safe = safe.strip("_")
    return safe or "profile"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolidate duplicate Screenshot_*.json profile files.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help=f"Root directory that contains Screenshot_*.json files (default: {DEFAULT_ROOT}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Path to the consolidated summary JSON (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--per-profile-dir",
        type=Path,
        help="Optional directory where individual consolidated profile files will be written.",
    )
    parser.add_argument(
        "--media-output-root",
        type=Path,
        help="Optional root directory to copy each profile's media assets into profile-specific folders.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentation used for generated JSON files (default: 2).",
    )
    return parser.parse_args()


def write_outputs(
    consolidated: Dict[str, Any],
    output_file: Path,
    per_profile_dir: Path | None,
    indent: int,
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(consolidated, indent=indent, ensure_ascii=False))
    if per_profile_dir:
        per_profile_dir.mkdir(parents=True, exist_ok=True)
        used_names: Dict[str, int] = {}
        for idx, profile in enumerate(consolidated["profiles"], start=1):
            display = profile.get("profile") or f"profile_{idx}"
            base = slugify(display)
            counter = used_names.get(base, 0)
            used_names[base] = counter + 1
            filename = base if counter == 0 else f"{base}_{counter+1}"
            target = per_profile_dir / f"{filename}.json"
            target.write_text(json.dumps(profile, indent=indent, ensure_ascii=False))


def export_profile_media(
    profiles: List[Dict[str, Any]],
    root: Path,
    media_root: Path,
) -> None:
    media_root.mkdir(parents=True, exist_ok=True)
    used_names: Dict[str, int] = {}
    name_map: Dict[str, str] = {}
    for idx, profile in enumerate(profiles, start=1):
        display = profile.get("profile") or f"profile_{idx}"
        normalized_name = display.strip().lower()
        if normalized_name and normalized_name in name_map:
            folder_name = name_map[normalized_name]
        else:
            base = slugify(display)
            count = used_names.get(base, 0)
            used_names[base] = count + 1
            folder_name = base if count == 0 else f"{base}_{count+1}"
            if normalized_name:
                name_map[normalized_name] = folder_name
        profile_dir = media_root / folder_name
        profile_dir.mkdir(parents=True, exist_ok=True)
        seen_sources: Set[str] = set()
        for media_rel in profile.get("media") or []:
            source_path = Path(media_rel)
            if not source_path.is_absolute():
                source_path = root / media_rel
            try:
                source_resolved = str(source_path.resolve())
            except FileNotFoundError:
                source_resolved = str(source_path)
                source_path = Path(source_resolved)
            if source_resolved in seen_sources:
                continue
            seen_sources.add(source_resolved)
            if not Path(source_resolved).exists():
                continue
            candidate = Path(source_resolved)
            if not candidate.is_file():
                continue
            dest_name = candidate.name
            stem = candidate.stem
            suffix = candidate.suffix
            counter = 1
            dest_path = profile_dir / dest_name
            while dest_path.exists():
                if dest_path.samefile(candidate):
                    break
                dest_name = f"{stem}_{counter}{suffix}"
                dest_path = profile_dir / dest_name
                counter += 1
            if not dest_path.exists() or not dest_path.samefile(candidate):
                shutil.copy2(candidate, dest_path)


def main() -> None:
    args = parse_args()
    files = discover_json_files(args.root)
    if not files:
        raise SystemExit(f"No Screenshot_*.json files found under {args.root}")
    consolidated = consolidate_profiles(files, args.root)
    write_outputs(consolidated, args.output, args.per_profile_dir, args.indent)
    if args.media_output_root:
        export_profile_media(consolidated["profiles"], args.root, args.media_output_root)
    print(
        f"Consolidated {consolidated['summary']['total_files']} files into "
        f"{consolidated['summary']['unique_profiles']} unique profiles."
    )


if __name__ == "__main__":
    main()
