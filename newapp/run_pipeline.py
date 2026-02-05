#!/usr/bin/env python3
"""Convenience runner that executes the entire OCR → metadata → consolidation → enrichment flow."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

APP_ROOT = Path(__file__).resolve().parent
DEFAULT_VENV_PYTHON = APP_ROOT.parent / ".venv" / "bin" / "python"

SCRIPT_OCR = APP_ROOT / "1-process_ocr.py"
SCRIPT_METADATA = APP_ROOT / "2-add_metadata.py"
SCRIPT_CONSOLIDATE = APP_ROOT / "3-consolidate_profiles.py"
SCRIPT_EXTEND = APP_ROOT / "4-extend_profiles.py"

DEFAULT_ROOT = APP_ROOT / "PATRON"
DEFAULT_CONSOLIDATED = APP_ROOT / "consolidated_profiles.json"
DEFAULT_PER_PROFILE = APP_ROOT / "consolidated"
DEFAULT_MEDIA_ROOT = APP_ROOT / "media_profiles"
DEFAULT_ENRICHED = APP_ROOT / "consolidated_profiles_enriched.json"


def resolve_python(explicit: Path | None) -> str:
    if explicit:
        if explicit.exists():
            return str(explicit)
        raise SystemExit(f"Python interpreter not found: {explicit}")
    if DEFAULT_VENV_PYTHON.exists():
        return str(DEFAULT_VENV_PYTHON)
    return sys.executable


def shlex_join(cmd: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)


def run_step(name: str, cmd: Sequence[str], dry_run: bool) -> None:
    print(f"\n==> {name}")
    print(f"    {shlex_join(cmd)}")
    if dry_run:
        return
    subprocess.run(cmd, check=True)


def ensure_scripts_exist() -> None:
    for script in (SCRIPT_OCR, SCRIPT_METADATA, SCRIPT_CONSOLIDATE, SCRIPT_EXTEND):
        if not script.exists():
            raise SystemExit(f"Required script missing: {script}")


def extend_with_flags(cmd: List[str], flag: str, values: Iterable[str] | None) -> None:
    if not values:
        return
    for value in values:
        cmd.extend([flag, value])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full OCR pipeline: OCR -> metadata -> consolidation -> enrichment.",
    )
    parser.add_argument("--python", type=Path, help="Python interpreter to run sub-commands.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Root folder containing Screenshot_*.jpg files.")
    parser.add_argument("--ollama-bin", default="ollama", help="Path to the Ollama binary.")
    parser.add_argument("--ocr-model", default="glm-ocr", help="Model used for OCR stage.")
    parser.add_argument("--ocr-timeout", type=int, default=300, help="Timeout per Ollama OCR call (seconds).")
    parser.add_argument(
        "--ocr-indent",
        type=int,
        default=2,
        help="Indentation for OCR JSON outputs when using 1-process_ocr.py.",
    )
    parser.add_argument(
        "--ocr-llm",
        action="append",
        help="Structured extraction LLM(s) for 1-process_ocr.py (repeat flag to add more).",
    )
    parser.add_argument("--ocr-coordinator", help="Consensus LLM used when more than one --ocr-llm is provided.")
    parser.add_argument("--ocr-overwrite", action="store_true", help="Force regeneration of Screenshot_*.json files.")

    parser.add_argument("--skip-ocr", action="store_true", help="Skip the OCR stage.")
    parser.add_argument("--skip-metadata", action="store_true", help="Skip metadata enrichment stage.")
    parser.add_argument("--skip-consolidate", action="store_true", help="Skip consolidation stage.")
    parser.add_argument("--skip-enrich", action="store_true", help="Skip structured enrichment stage.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")

    parser.add_argument(
        "--consolidated-output",
        type=Path,
        default=DEFAULT_CONSOLIDATED,
        help="Path for consolidated_profiles.json.",
    )
    parser.add_argument(
        "--per-profile-dir",
        type=Path,
        default=DEFAULT_PER_PROFILE,
        help="Directory to store individual consolidated profile JSON files.",
    )
    parser.add_argument(
        "--media-root",
        type=Path,
        default=DEFAULT_MEDIA_ROOT,
        help="Where consolidated media copies will live.",
    )
    parser.add_argument(
        "--enriched-output",
        type=Path,
        default=DEFAULT_ENRICHED,
        help="Path for consolidated_profiles_enriched.json.",
    )
    parser.add_argument("--enrich-model", default="qwen3-vl:235b-cloud", help="LLM model for profile enrichment.")
    parser.add_argument("--enrich-timeout", type=int, default=300, help="Timeout per enrichment request (seconds).")
    parser.add_argument("--enrich-limit", type=int, help="Limit number of profiles when running 4-extend_profiles.py.")
    parser.add_argument("--enrich-overwrite", action="store_true", help="Regenerate existing extraction blocks.")
    parser.add_argument("--enrich-skip-llm", action="store_true", help="Skip LLM calls during enrichment.")
    parser.add_argument(
        "--enrich-indent",
        type=int,
        default=2,
        help="Indentation for enriched JSON output.",
    )
    parser.add_argument(
        "--show-extractions",
        action="store_true",
        help="After running, print each profile's extraction JSON to stdout (from the enriched output).",
    )
    parser.add_argument(
        "--show-limit",
        type=int,
        help="When --show-extractions is set, limit output to the first N profiles with extraction data.",
    )
    return parser.parse_args()


def print_extractions(enriched_path: Path, limit: int | None) -> None:
    if not enriched_path.exists():
        print(f"[warn] Enriched file not found: {enriched_path}")
        return
    try:
        payload = json.loads(enriched_path.read_text())
    except json.JSONDecodeError as exc:
        print(f"[warn] Could not parse {enriched_path}: {exc}")
        return

    profiles = payload if isinstance(payload, list) else payload.get("profiles", [])
    if not profiles:
        print("[warn] No profiles with extraction data were found.")
        return

    shown = 0
    for profile in profiles:
        extraction = profile.get("extraction")
        if not extraction:
            continue
        name = profile.get("profile") or profile.get("id") or "(sin nombre)"
        print(f"\n--- {name} ---")
        print(json.dumps(extraction, ensure_ascii=False, indent=2))
        shown += 1
        if limit and shown >= limit:
            break
    if shown == 0:
        print("[info] Profiles did not contain extraction blocks to display.")
    else:
        print(f"\n[done] Displayed {shown} extraction block(s) from {enriched_path}.")


def main() -> None:
    ensure_scripts_exist()
    args = parse_args()
    python_bin = resolve_python(args.python)

    if not args.skip_ocr:
        ocr_cmd: List[str] = [
            python_bin,
            str(SCRIPT_OCR),
            "--root",
            str(args.root),
            "--ollama-bin",
            args.ollama_bin,
            "--ocr-model",
            args.ocr_model,
            "--timeout",
            str(args.ocr_timeout),
            "--indent",
            str(args.ocr_indent),
        ]
        extend_with_flags(ocr_cmd, "--llm", args.ocr_llm)
        if args.ocr_coordinator:
            ocr_cmd.extend(["--coordinator", args.ocr_coordinator])
        if args.ocr_overwrite:
            ocr_cmd.append("--overwrite")
        run_step("OCR extraction", ocr_cmd, args.dry_run)

    if not args.skip_metadata:
        metadata_cmd = [python_bin, str(SCRIPT_METADATA)]
        run_step("Metadata enrichment", metadata_cmd, args.dry_run)

    if not args.skip_consolidate:
        consolidate_cmd: List[str] = [
            python_bin,
            str(SCRIPT_CONSOLIDATE),
            "--root",
            str(args.root),
            "--output",
            str(args.consolidated_output),
            "--indent",
            "2",
        ]
        if args.per_profile_dir:
            consolidate_cmd.extend(["--per-profile-dir", str(args.per_profile_dir)])
        if args.media_root:
            consolidate_cmd.extend(["--media-output-root", str(args.media_root)])
        run_step("Consolidation", consolidate_cmd, args.dry_run)

    if not args.skip_enrich:
        enrich_cmd: List[str] = [
            python_bin,
            str(SCRIPT_EXTEND),
            "--input",
            str(args.consolidated_output),
            "--output",
            str(args.enriched_output),
            "--ollama-bin",
            args.ollama_bin,
            "--model",
            args.enrich_model,
            "--timeout",
            str(args.enrich_timeout),
            "--media-root",
            str(args.media_root),
            "--indent",
            str(args.enrich_indent),
        ]
        if args.enrich_limit:
            enrich_cmd.extend(["--limit", str(args.enrich_limit)])
        if args.enrich_overwrite:
            enrich_cmd.append("--overwrite")
        if args.enrich_skip_llm:
            enrich_cmd.append("--skip-llm")
        run_step("Enrichment", enrich_cmd, args.dry_run)

    print("\nPipeline completed.")
    if args.show_extractions:
        print_extractions(args.enriched_output, args.show_limit)


if __name__ == "__main__":
    main()
