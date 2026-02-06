#!/usr/bin/env python3
"""Move media files from a source tree into profile folders without duplicates.

Default layout:
  source: web/PATRON
  target: web/media_profiles

Behavior:
- Finds media recursively under source.
- Resolves destination profile folder by matching folder names (with normalization).
- Moves files into destination folders.
- Skips screenshot images named `Screenshot_*.jpg` / `Screenshot_*.jpeg`.
- Prevents duplicates using content fingerprint (size + sha1).
- If content already exists in destination folder, source file is deleted (or would be in dry-run).
- In apply mode, updates catalog metadata based on git-status deltas:
  - existing profile folder with new media -> metadata.nuevas_fotos_videos = true
  - new profile folder -> append profile block with metadata.nuevo_ingreso = true
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

SUPPORTED_MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".mp4",
    ".mov",
    ".m4v",
    ".webm",
}

CHUNK_SIZE = 1024 * 1024
FALLBACK_EXCLUDED_KEYS = {
    "perfiles",
    "perfil",
    "cortesia",
    "anuncios",
    "comunidad",
    "provincia",
    "patron",
}


@dataclass
class Stats:
    scanned_media_files: int = 0
    skipped_screenshot: int = 0
    moved: int = 0
    duplicates_deleted: int = 0
    renamed_on_move: int = 0
    unresolved: int = 0
    errors: int = 0
    catalog_profiles_updated: int = 0
    catalog_profiles_added: int = 0
    catalog_updated: bool = False
    unresolved_examples: List[str] = field(default_factory=list)
    error_examples: List[str] = field(default_factory=list)


@dataclass
class GitMediaSnapshot:
    added_media_folders: Set[str] = field(default_factory=set)
    added_target_dirs: Set[str] = field(default_factory=set)


@dataclass
class CatalogUpdateResult:
    updated_profiles: int = 0
    added_profiles: int = 0
    updated: bool = False


class FingerprintCache:
    def __init__(self) -> None:
        self._cache: Dict[Path, Tuple[int, str]] = {}

    def get(self, file_path: Path) -> Tuple[int, str]:
        cached = self._cache.get(file_path)
        if cached is not None:
            return cached

        size = file_path.stat().st_size
        sha1 = hashlib.sha1()
        with file_path.open("rb") as fh:
            while True:
                chunk = fh.read(CHUNK_SIZE)
                if not chunk:
                    break
                sha1.update(chunk)
        fingerprint = (size, sha1.hexdigest())
        self._cache[file_path] = fingerprint
        return fingerprint


def normalize_token(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.strip().lower()
    value = value.replace("&", " and ")
    value = value.replace("_", " ")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


def candidate_names(component: str) -> List[str]:
    raw = component.strip()
    out: List[str] = []

    def add(item: str) -> None:
        item = item.strip()
        if item and item not in out:
            out.append(item)

    add(raw)

    # Example: "4 - KIMBERLY ⭐⭐⭐⭐⭐" -> "KIMBERLY ⭐⭐⭐⭐⭐"
    add(re.sub(r"^\d+\s*[-.)]\s*", "", raw))

    # Example: "1 (diosa)" -> "diosa"
    for inner in re.findall(r"\(([^)]+)\)", raw):
        add(inner)

    # Split on dash and use right-most meaningful part for labels like "0 - TIKAS".
    if "-" in raw:
        parts = [part.strip() for part in raw.split("-") if part.strip()]
        if parts:
            add(parts[-1])

    return out


def build_target_key_index(target_root: Path) -> Dict[str, List[Path]]:
    index: Dict[str, List[Path]] = {}
    for entry in sorted(target_root.iterdir()):
        if not entry.is_dir():
            continue
        add_target_to_key_index(index, entry)
    return index


def add_target_to_key_index(index: Dict[str, List[Path]], target_dir: Path) -> None:
    labels = {target_dir.name}
    labels.update(candidate_names(target_dir.name))
    for label in labels:
        key = normalize_token(label)
        if not key:
            continue
        paths = index.setdefault(key, [])
        if target_dir not in paths:
            paths.append(target_dir)


def is_media_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_MEDIA_EXTENSIONS


def is_media_name(file_name: str) -> bool:
    return Path(file_name).suffix.lower() in SUPPORTED_MEDIA_EXTENSIONS


def is_screenshot_image(path: Path) -> bool:
    lower_name = path.name.lower()
    return lower_name.startswith("screenshot_") and path.suffix.lower() in {".jpg", ".jpeg"}


def is_screenshot_name(file_name: str) -> bool:
    lower_name = file_name.lower()
    return lower_name.startswith("screenshot_") and Path(file_name).suffix.lower() in {".jpg", ".jpeg"}


def iter_media_files(source_root: Path) -> Iterable[Path]:
    for path in source_root.rglob("*"):
        if is_media_file(path):
            yield path


def resolve_target_dir(file_path: Path, source_root: Path, key_index: Dict[str, List[Path]]) -> Optional[Path]:
    rel_parent = file_path.parent.relative_to(source_root)
    components = list(rel_parent.parts)

    for component in reversed(components):
        for label in candidate_names(component):
            key = normalize_token(label)
            if not key:
                continue
            matches = key_index.get(key, [])
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                exact = [m for m in matches if normalize_token(m.name) == key]
                if len(exact) == 1:
                    return exact[0]

    return None


def sanitize_folder_name(raw: str) -> str:
    value = raw.strip()
    value = re.sub(r"[\\\\/]+", "_", value)
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"_+", "_", value).strip("._ ")
    return value


def is_excluded_fallback_key(leaf_key: str) -> bool:
    tokens = {token for token in leaf_key.split("_") if token}
    return any(token in FALLBACK_EXCLUDED_KEYS for token in tokens)


def resolve_or_create_target_dir(
    file_path: Path,
    source_root: Path,
    target_root: Path,
    key_index: Dict[str, List[Path]],
    apply: bool,
    create_missing_targets: bool,
) -> Optional[Path]:
    target_dir = resolve_target_dir(file_path, source_root, key_index)
    if target_dir is not None:
        return target_dir

    if not create_missing_targets:
        return None

    rel_parent = file_path.parent.relative_to(source_root)
    # Require at least one parent folder to infer profile name.
    if len(rel_parent.parts) < 1:
        return None

    leaf_folder = rel_parent.parts[-1]
    leaf_key = normalize_token(leaf_folder)
    if not leaf_key or is_excluded_fallback_key(leaf_key):
        return None

    folder_name = sanitize_folder_name(leaf_folder)
    if not folder_name:
        return None

    created = target_root / folder_name
    if apply:
        created.mkdir(parents=True, exist_ok=True)
    add_target_to_key_index(key_index, created)
    return created


def ensure_unique_path(destination: Path) -> Path:
    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    idx = 1
    while True:
        candidate = parent / f"{stem}_moved{idx}{suffix}"
        if not candidate.exists():
            return candidate
        idx += 1


def build_target_fingerprint_index(
    target_dir: Path,
    fp_cache: FingerprintCache,
) -> Dict[Tuple[int, str], Path]:
    fp_index: Dict[Tuple[int, str], Path] = {}
    if not target_dir.exists() or not target_dir.is_dir():
        return fp_index
    for existing in target_dir.iterdir():
        if not is_media_file(existing):
            continue
        fp = fp_cache.get(existing)
        fp_index.setdefault(fp, existing)
    return fp_index


def move_media(
    source_root: Path,
    target_root: Path,
    apply: bool,
    create_missing_targets: bool,
    cleanup_empty_dirs: bool,
    verbose: bool,
) -> Stats:
    stats = Stats()
    fp_cache = FingerprintCache()
    key_index = build_target_key_index(target_root)

    target_fp_indexes: Dict[Path, Dict[Tuple[int, str], Path]] = {}

    media_files = sorted(iter_media_files(source_root))
    stats.scanned_media_files = len(media_files)

    for src_file in media_files:
        if is_screenshot_image(src_file):
            stats.skipped_screenshot += 1
            if verbose:
                print(f"SKIP SCREENSHOT: {src_file}")
            continue

        target_dir = resolve_or_create_target_dir(
            file_path=src_file,
            source_root=source_root,
            target_root=target_root,
            key_index=key_index,
            apply=apply,
            create_missing_targets=create_missing_targets,
        )
        if target_dir is None:
            stats.unresolved += 1
            if len(stats.unresolved_examples) < 20:
                stats.unresolved_examples.append(str(src_file.relative_to(source_root)))
            continue

        if apply and not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)

        if target_dir not in target_fp_indexes:
            target_fp_indexes[target_dir] = build_target_fingerprint_index(target_dir, fp_cache)
        fp_index = target_fp_indexes[target_dir]

        try:
            src_fp = fp_cache.get(src_file)
        except Exception as exc:  # pragma: no cover
            stats.errors += 1
            if len(stats.error_examples) < 20:
                stats.error_examples.append(f"{src_file}: fingerprint error: {exc}")
            continue

        existing_with_same_content = fp_index.get(src_fp)
        if existing_with_same_content is not None:
            if verbose:
                print(
                    f"DUPLICATE {'DELETE' if apply else 'SKIP'}: {src_file}"
                    f" (already in {existing_with_same_content})"
                )
            if apply:
                src_file.unlink()
            stats.duplicates_deleted += 1
            continue

        destination = target_dir / src_file.name
        renamed = False
        if destination.exists():
            destination = ensure_unique_path(destination)
            renamed = True

        if verbose:
            print(f"MOVE {'APPLY' if apply else 'PLAN'}: {src_file} -> {destination}")

        if apply:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_file), str(destination))

        fp_index[src_fp] = destination
        stats.moved += 1
        if renamed:
            stats.renamed_on_move += 1

    if apply and cleanup_empty_dirs:
        remove_empty_dirs(source_root, verbose=verbose)

    return stats


def remove_empty_dirs(root: Path, verbose: bool) -> None:
    # Remove empty directories from deepest to shallowest.
    for directory in sorted([p for p in root.rglob("*") if p.is_dir()], key=lambda p: len(p.parts), reverse=True):
        try:
            next(directory.iterdir())
        except StopIteration:
            directory.rmdir()
            if verbose:
                print(f"RMDIR: {directory}")
        except Exception:
            pass


def to_posix_path(value: str) -> str:
    return value.replace(os.sep, "/")


def find_git_repo_root(any_path: Path) -> Optional[Path]:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(any_path), "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return None
    if not output:
        return None
    return Path(output)


def collect_git_media_snapshot(repo_root: Path, target_root: Path) -> GitMediaSnapshot:
    snapshot = GitMediaSnapshot()

    target_rel = to_posix_path(os.path.relpath(target_root, repo_root))
    target_prefix = f"{target_rel.rstrip('/')}/"

    output = subprocess.check_output(
        [
            "git",
            "-C",
            str(repo_root),
            "status",
            "--porcelain",
            "-z",
            "--untracked-files=all",
            "--",
            target_rel,
        ],
        text=False,
    )

    for raw_entry in output.split(b"\0"):
        if not raw_entry:
            continue
        entry = raw_entry.decode("utf-8", errors="replace")
        if len(entry) < 4:
            continue

        status = entry[:2]
        # Added to index or untracked in working tree.
        if status != "??" and status[0] != "A" and status[1] != "A":
            continue

        path = entry[3:]
        if not path.startswith(target_prefix):
            continue

        relative_under_target = path[len(target_prefix) :]
        if not relative_under_target:
            continue

        parts = [part for part in relative_under_target.split("/") if part]
        if not parts:
            continue

        folder = parts[0]

        # Explicit directory entries can appear for empty untracked dirs.
        if path.endswith("/"):
            snapshot.added_target_dirs.add(folder)
            continue

        if len(parts) == 1:
            # A top-level file directly under media_profiles; ignore for profile mapping.
            continue

        file_name = parts[-1]
        if is_media_name(file_name) and not is_screenshot_name(file_name):
            snapshot.added_media_folders.add(folder)

    return snapshot


def profile_folder_keys(profile: dict) -> Set[str]:
    keys: Set[str] = set()

    raw_profile_id = profile.get("profile")
    if isinstance(raw_profile_id, str) and raw_profile_id.strip():
        keys.add(raw_profile_id.strip())

    raw_roots = profile.get("media_roots")
    if not isinstance(raw_roots, list):
        return keys

    for root in raw_roots:
        if not isinstance(root, str):
            continue
        normalized = root.replace("\\", "/").strip().strip("/")
        if not normalized:
            continue
        keys.add(normalized.split("/")[-1])

    return keys


def list_media_entries_for_folder(catalog_dir: Path, target_root: Path, folder_name: str) -> List[str]:
    folder_path = target_root / folder_name
    if not folder_path.exists() or not folder_path.is_dir():
        return []

    media_root_rel = to_posix_path(os.path.relpath(folder_path, catalog_dir))
    entries: List[str] = []

    for file_path in sorted(folder_path.iterdir(), key=lambda item: item.name.lower()):
        if not is_media_file(file_path):
            continue
        if is_screenshot_image(file_path):
            continue
        entries.append(f"{media_root_rel}/{file_path.name}")

    return entries


def build_new_profile_block(catalog_dir: Path, target_root: Path, folder_name: str) -> dict:
    media_root_rel = to_posix_path(os.path.relpath(target_root / folder_name, catalog_dir))
    media_entries = list_media_entries_for_folder(catalog_dir, target_root, folder_name)

    return {
        "metadata": {
            "labels": [],
            "ubicacion": None,
            "edad_rango": None,
            "nuevo_ingreso": True,
            "sin_experiencia": False,
            "cortesia": False,
            "nuevas_fotos_videos": False,
        },
        "profile": folder_name,
        "discreet_list": True,
        "extraction": {
            "name": folder_name,
            "age": None,
            "height": None,
            "weight": None,
            "hair_color": None,
            "eye_color": None,
            "location": None,
            "availability": None,
            "contact": None,
            "prices": {
                "one_hour": None,
                "two_hours": None,
                "three_hours": None,
                "overnight": None,
            },
            "implants": None,
            "uber": None,
            "cosmetic_surgeries": None,
            "other_attributes": {},
        },
        "enabled": True,
        "media_roots": [media_root_rel],
        "media": media_entries,
    }


def update_catalog_from_git_delta(
    catalog_path: Path,
    target_root: Path,
    pre_snapshot: GitMediaSnapshot,
    post_snapshot: GitMediaSnapshot,
    verbose: bool,
) -> CatalogUpdateResult:
    result = CatalogUpdateResult()

    delta_media_folders = post_snapshot.added_media_folders - pre_snapshot.added_media_folders
    delta_added_dirs = post_snapshot.added_target_dirs - pre_snapshot.added_target_dirs

    if not delta_media_folders and not delta_added_dirs:
        return result

    if not catalog_path.exists():
        raise FileNotFoundError(f"Catalog not found: {catalog_path}")

    with catalog_path.open("r", encoding="utf-8") as fh:
        catalog = json.load(fh)

    profiles = catalog.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("Invalid catalog format: expected { profiles: [] }")

    folder_to_profile_indexes: Dict[str, List[int]] = {}
    for idx, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            continue
        for key in profile_folder_keys(profile):
            folder_to_profile_indexes.setdefault(key, []).append(idx)

    changed = False
    updated_indexes: Set[int] = set()

    for folder in sorted(delta_media_folders):
        indexes = folder_to_profile_indexes.get(folder, [])
        for idx in indexes:
            profile = profiles[idx]
            if not isinstance(profile, dict):
                continue

            metadata = profile.get("metadata")
            if not isinstance(metadata, dict):
                metadata = {}
                profile["metadata"] = metadata

            if metadata.get("nuevas_fotos_videos") is not True:
                metadata["nuevas_fotos_videos"] = True
                changed = True

            updated_indexes.add(idx)

    result.updated_profiles = len(updated_indexes)

    new_profile_candidates = sorted((delta_media_folders | delta_added_dirs) - set(folder_to_profile_indexes.keys()))
    for folder in new_profile_candidates:
        new_profile = build_new_profile_block(catalog_path.parent, target_root, folder)
        profiles.append(new_profile)
        folder_to_profile_indexes.setdefault(folder, []).append(len(profiles) - 1)
        result.added_profiles += 1
        changed = True
        if verbose:
            print(f"CATALOG ADD PROFILE: {folder}")

    if not changed:
        return result

    with catalog_path.open("w", encoding="utf-8") as fh:
        json.dump(catalog, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    result.updated = True
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Move media files from PATRON into media_profiles without creating duplicates."
    )
    parser.add_argument(
        "--source",
        default="web/PATRON",
        help="Source root to scan recursively (default: web/PATRON)",
    )
    parser.add_argument(
        "--target",
        default="web/media_profiles",
        help="Target media_profiles root (default: web/media_profiles)",
    )
    parser.add_argument(
        "--catalog",
        default=None,
        help="Catalog JSON path (default: <target_parent>/catalog.json)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Execute move/delete operations. Without this flag, runs as dry-run.",
    )
    parser.add_argument(
        "--create-missing-targets",
        action="store_true",
        help="Create missing media_profiles/<name> when a profile-like folder has no target match.",
    )
    parser.add_argument(
        "--no-catalog-update",
        action="store_true",
        help="Do not update catalog.json metadata after apply mode move operation.",
    )
    parser.add_argument(
        "--no-cleanup-empty-dirs",
        action="store_true",
        help="Do not remove empty directories in source after apply.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each planned/applied operation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    source_root = Path(args.source).resolve()
    target_root = Path(args.target).resolve()
    catalog_path = Path(args.catalog).resolve() if args.catalog else (target_root.parent / "catalog.json").resolve()

    if not source_root.exists() or not source_root.is_dir():
        print(f"ERROR: source folder not found or not a directory: {source_root}", file=sys.stderr)
        return 1
    if not target_root.exists() or not target_root.is_dir():
        print(f"ERROR: target folder not found or not a directory: {target_root}", file=sys.stderr)
        return 1

    pre_snapshot = GitMediaSnapshot()
    repo_root: Optional[Path] = None

    if args.apply and not args.no_catalog_update:
        repo_root = find_git_repo_root(target_root)
        if repo_root is None:
            print("WARN: git repository not found from target path; skipping catalog auto-update")
        else:
            pre_snapshot = collect_git_media_snapshot(repo_root, target_root)

    stats = move_media(
        source_root=source_root,
        target_root=target_root,
        apply=args.apply,
        create_missing_targets=args.create_missing_targets,
        cleanup_empty_dirs=not args.no_cleanup_empty_dirs,
        verbose=args.verbose,
    )

    if args.apply and not args.no_catalog_update and repo_root is not None:
        try:
            post_snapshot = collect_git_media_snapshot(repo_root, target_root)
            catalog_result = update_catalog_from_git_delta(
                catalog_path=catalog_path,
                target_root=target_root,
                pre_snapshot=pre_snapshot,
                post_snapshot=post_snapshot,
                verbose=args.verbose,
            )
            stats.catalog_profiles_updated = catalog_result.updated_profiles
            stats.catalog_profiles_added = catalog_result.added_profiles
            stats.catalog_updated = catalog_result.updated
        except Exception as exc:  # pragma: no cover
            stats.errors += 1
            stats.error_examples.append(f"catalog update error: {exc}")

    mode = "APPLY" if args.apply else "DRY_RUN"
    print(
        f"{mode} summary: scanned={stats.scanned_media_files}, skipped_screenshot={stats.skipped_screenshot}, moved={stats.moved}, "
        f"duplicates_deleted={stats.duplicates_deleted}, renamed_on_move={stats.renamed_on_move}, "
        f"unresolved={stats.unresolved}, errors={stats.errors}, "
        f"catalog_profiles_updated={stats.catalog_profiles_updated}, catalog_profiles_added={stats.catalog_profiles_added}, "
        f"catalog_updated={'yes' if stats.catalog_updated else 'no'}"
    )

    if stats.unresolved_examples:
        print("Unresolved examples (first 20):")
        for item in stats.unresolved_examples:
            print(f"  - {item}")

    if stats.error_examples:
        print("Errors (first 20):")
        for item in stats.error_examples:
            print(f"  - {item}")

    return 0 if stats.errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
