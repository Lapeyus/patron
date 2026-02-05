#!/usr/bin/env python3
"""Batch OCR pipeline for Screenshot_*.jpg assets using Ollama."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Sequence

try:
    from tqdm import tqdm
except ImportError as exc:  # pragma: no cover - runtime dependency
    raise SystemExit(
        "Missing dependency: tqdm. Install it with 'pip install tqdm' before running this script."
    ) from exc

DEFAULT_PROMPT = """You are an expert data extractor. Given the OCR text from a document,
produce a compact JSON object with these keys: name, age, location, prices (array
of objects with duration, amount, currency), services (array of short strings),
contact (object with whatsapp, phone, email, social), attributes (object with
height, weight, hair_color, eye_color, implants, measurements), raw_text (a
concise Spanish summary). Use null when unknown. JSON only, no markdown.
TEXT:\n{raw_text}"""

CONSENSUS_PROMPT = """You are a coordinator model. Multiple LLMs extracted JSON from the
same OCR text. Review their proposals and output a single reconciled JSON object
described in the schema below.

Schema keys: name, age, location, prices[{duration, amount, currency}],
services[], contact{whatsapp, phone, email, social}, attributes{height, weight,
hair_color, eye_color, implants, measurements}, raw_text (concise summary in
Spanish).

Use the OCR text for reference when the proposals disagree. Prefer values with
the strongest agreement. Amounts like "100 mil" should be interpreted as 100000
in the detected currency.

OCR TEXT:\n{raw_text}

PROPOSALS:\n{proposals}

Return JSON only, no markdown."""


def run_ollama(ollama_bin: str, model: str, prompt: str, timeout: int) -> str:
    command: Sequence[str] = (ollama_bin, "run", model, prompt)
    completed = subprocess.run(  # noqa: S603
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return completed.stdout.strip()


def extract_json(block: str) -> Dict:
    cleaned = block.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1]
        cleaned = cleaned.split("```", 1)[0]
    elif cleaned.startswith("```"):
        cleaned = cleaned.split("```", 1)[1]
        cleaned = cleaned.split("```", 1)[0]
    start_idx = cleaned.find("{")
    if start_idx > 0:
        cleaned = cleaned[start_idx:]
    return json.loads(cleaned)


def structure_with_models(
    raw_text: str,
    ollama_bin: str,
    models: List[str],
    coordinator: str | None,
    timeout: int,
) -> Dict:
    proposals: List[Dict] = []
    for model in models:
        prompt = DEFAULT_PROMPT.format(raw_text=raw_text)
        resp = run_ollama(ollama_bin, model, prompt, timeout)
        proposals.append(extract_json(resp))
    if len(proposals) == 1 or not coordinator:
        return proposals[0]
    consensus_prompt = CONSENSUS_PROMPT.format(
        raw_text=raw_text,
        proposals=json.dumps(proposals, indent=2, ensure_ascii=False),
    )
    resp = run_ollama(ollama_bin, coordinator, consensus_prompt, timeout)
    return extract_json(resp)


def discover_images(root: Path) -> List[Path]:
    root = root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"Root path not found: {root}")
    return sorted(p for p in root.rglob("Screenshot_*.jpg") if p.is_file())


def save_json(target: Path, payload: Dict, indent: int) -> None:
    target.write_text(json.dumps(payload, indent=indent, ensure_ascii=False))


def process_image(
    image_path: Path,
    args: argparse.Namespace,
) -> None:
    target = image_path.with_suffix(".json")
    if target.exists() and not args.overwrite:
        return

    prompt = f"Text Recognition: {image_path}"
    raw_text = run_ollama(args.ollama_bin, args.ocr_model, prompt, args.timeout)

    structured = None
    if args.llm:
        structured = structure_with_models(
            raw_text,
            args.ollama_bin,
            args.llm,
            args.coordinator,
            args.timeout,
        )
    cleaned_text = DISCLAIMER_PATTERN.sub("", raw_text).strip().replace("€", "₡")

    image_str = str(image_path)
    record = {
        "ocr": image_str,
        "image": image_str,
        "task": "text",
        "raw_response": cleaned_text,
        "structured_data": structured,
    }
    save_json(target, record, args.indent)
    print(f"Wrote {target}")


APP_ROOT = Path(__file__).resolve().parent
DEFAULT_ROOT = APP_ROOT / "PATRON"
DISCLAIMER_PATTERN = re.compile(
    r"INFORMACIÓN EMANADA DIRECTAMENTE[\s\S]*?CLUB PATR[ÓO]N[\s\S]*?se limita a proporcionarle el contacto\.\s*",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate OCR JSON files for Screenshot_*.jpg using Ollama.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help=f"Root directory to scan for Screenshot_*.jpg files (default: {DEFAULT_ROOT}).",
    )
    parser.add_argument(
        "--ollama-bin",
        default="ollama",
        help="Path to the Ollama binary (default: ollama).",
    )
    parser.add_argument(
        "--ocr-model",
        default="glm-ocr",
        help="Ollama model used for OCR text extraction (default: glm-ocr).",
    )
    parser.add_argument(
        "--llm",
        action="append",
        help="One or more LLMs to transform OCR text into structured JSON. Repeat flag for multiple models.",
    )
    parser.add_argument(
        "--coordinator",
        help="LLM responsible for building consensus when multiple --llm values are provided.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout (seconds) for each Ollama invocation.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation for saved files.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing Screenshot_*.json files (default: skip already processed images).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.llm and len(args.llm) > 1 and not args.coordinator:
        raise SystemExit("--coordinator is required when multiple --llm values are provided.")
    llms: List[str] = []
    if args.llm:
        for entry in args.llm:
            parts = [p.strip() for p in entry.split(",") if p.strip()]
            llms.extend(parts)
    args.llm = llms

    images = discover_images(args.root)
    if not images:
        raise SystemExit(f"No Screenshot_*.jpg files found under {args.root}")
    print(f"Found {len(images)} images under {args.root}")

    progress = tqdm(images, desc="Processing", unit="img")
    for image in progress:
        try:
            process_image(image, args)
        except subprocess.CalledProcessError as exc:
            print(f"Failed on {image}: {exc}")
        except Exception as exc:  # noqa: BLE001
            print(f"Unexpected error for {image}: {exc}")


if __name__ == "__main__":
    main()
