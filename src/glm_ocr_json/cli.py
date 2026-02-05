"""Command-line entry point for GLM-OCR JSON conversion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from .discovery import discover_images
from .ocr import OCRProcessor, OCRTask, OCRResult
from .pipeline import JobManager


import subprocess
from typing import Dict, Any

def _analyze_path_context(path_parts: List[str], ollama_bin: str, model: str, timeout: int) -> Dict[str, Any]:
    """Ask LLM to interpret folder semantic meaning."""
    path_str = " > ".join(path_parts)
    prompt = (
        f"You are a filesystem metadata analyzer.\n"
        f"Analyze the following folder path structure for a service catalog:\n"
        f"PATH: {path_str}\n\n"
        f"Extract key attributes implied by the folder names. The names might refer to:\n"
        f"- Service Provider Name (e.g. 'Angel', 'Kimberly')\n"
        f"- Age Group (e.g. '18 - 19 - 20 años')\n"
        f"- Location/Province (e.g. 'ALAJUELA')\n"
        f"- Ethnicity/Category (e.g. 'VENEZOLANA' is 'Venezolana' ethnicity, 'COSPLAYER' is a category, 'AFROCARIBEÑAS' is ethnicity)\n"
        f"- Status (e.g. 'nuevas fotos', 'cortesía')\n\n"
        f"Return ONLY a clean JSON object with keys: 'name', 'age_group', 'location', 'category', 'ethnicity'.\n"
        f"Use null if not found. Do NOT hallucinate names if the folder is just a category."
    )
    
    try:
        completed = subprocess.run(
            [ollama_bin, "run", model, prompt],
            capture_output=True, text=True, timeout=timeout
        )
        response = completed.stdout.strip()
        # Clean markdown
        start = response.find('{')
        if start != -1:
            try:
                obj, _ = json.JSONDecoder().raw_decode(response[start:])
                return obj
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"Warning: Failed to analyze path context: {e}")
    
    return {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run GLM-OCR via Ollama and convert the response to structured JSON.",
    )
    parser.add_argument(
        "images",
        nargs="*",
        help="Optional path(s) to image files to process. "
        "When omitted, the CLI discovers screenshot files automatically.",
    )
    parser.add_argument(
        "--task",
        choices=[task.slug for task in OCRTask],
        default=OCRTask.TEXT.slug,
        help="Which GLM-OCR mode to use.",
    )
    parser.add_argument(
        "--ollama-bin",
        default="ollama",
        help="Path to the Ollama CLI binary (defaults to 'ollama').",
    )
    parser.add_argument(
        "--model",
        default="glm-ocr",
        help="Name of the Ollama model to invoke.",
    )
    parser.add_argument(
        "--structure-model",
        action="append",
        help="Optional Ollama model(s) to use for structuring the OCR output (e.g., '--structure-model llama3' or '--structure-model qwen --structure-model mistral').",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Seconds to wait for each Ollama invocation.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional directory where JSON files should be written.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Number of spaces used when pretty-printing JSON.",
    )
    parser.add_argument(
        "--scan-root",
        type=Path,
        help=(
            "Root directory to recursively scan for screenshot images when no explicit "
            "paths are provided. Defaults to '@patron', then 'PATRON', then the current "
            "working directory."
        ),
    )
    parser.add_argument(
        "--pattern",
        help="Filename glob used during recursive discovery (defaults to 'Screenshot_*').",
    )
    parser.add_argument(
        "--reprocess-json",
        nargs="+",
        help="Path(s) to JSON files or directories to reprocess using structuring models without re-running OCR.",
    )
    parser.add_argument(
        "--pipeline-db",
        type=Path,
        help="Optional path to a SQLite database for state tracking (enables sequential processing).",
    )
    return parser


def _default_scan_root() -> Path:
    for candidate in ("@patron", "PATRON"):
        path = Path(candidate)
        if path.exists():
            return path
    return Path.cwd()


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    task = OCRTask.from_slug(args.task)
    structure_models: List[str] | None = None
    if args.structure_model:
        structure_models = []
        for entry in args.structure_model:
            parts = [part.strip() for part in entry.split(",") if part.strip()]
            structure_models.extend(parts)
        if not structure_models:
            structure_models = None

    processor = OCRProcessor(
        ollama_bin=args.ollama_bin,
        model=args.model,
        structure_models=structure_models,
        timeout=args.timeout,
    )

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    scan_root = (args.scan_root or _default_scan_root()).resolve()

    if args.reprocess_json:
        if args.output_dir:
            args.output_dir.mkdir(parents=True, exist_ok=True)

        target_files: List[Path] = []
        for path_str in args.reprocess_json:
            target = Path(path_str)
            if target.is_dir():
                target_files.extend(sorted(target.glob("*.json")))
            elif target.is_file():
                target_files.append(target)
            else:
                parser.error(f"Reprocess target not found: {path_str}")

        if not target_files:
            parser.error("No JSON files found for reprocessing.")

        for json_path in target_files:
            try:
                record = json.loads(json_path.read_text())
            except Exception as exc:
                print(f"Skipping {json_path}: {exc}")
                continue

            metadata = record.get("path_metadata") or []
            context_hints = {}
            if metadata and processor.structure_models:
                try:
                    context_hints = _analyze_path_context(
                        metadata,
                        args.ollama_bin,
                        processor.structure_models[0],
                        processor.timeout,
                    )
                except Exception as exc:
                    context_hints = {}
                    print(f"Warning: context analysis failed for {json_path.name}: {exc}")

            new_structured = processor.refine_existing(record, context_hints or None)
            record["structured_data"] = new_structured

            if args.output_dir:
                out_path = args.output_dir / json_path.name
            else:
                out_path = json_path

            out_path.write_text(json.dumps(record, indent=args.indent, ensure_ascii=False))
            print(f"Reprocessed {json_path} -> {out_path}")

        return

    if args.pipeline_db:
        # --- Sequential Pipeline Mode ---
        db_path = args.pipeline_db
        print(f"Using pipeline DB: {db_path}")
        manager = JobManager(db_path)

        # 1. Discovery & Registration
        if args.images:
            candidates = [Path(p) for p in args.images]
        else:
            pattern = args.pattern or "Screenshot_*"
            print(f"Scanning {scan_root} for pattern {pattern!r}...")
            candidates = discover_images(scan_root, pattern)
        
        new_count = 0
        for path in candidates:
            if manager.register_image(path, scan_root):
                new_count += 1
        
        stats = manager.get_stats()
        print(f"Pipeline Stats: {stats}. Added {new_count} new images.")

        # 2. Sequential Processing Loop
        while True:
            job = manager.get_next_pending()
            if not job:
                print("No pending jobs found. All done!")
                break
            
            file_hash, path_str, metadata = job
            path = Path(path_str)
            print(f"Processing: {path.name} (Metadata: {metadata})...")

            try:
                # Analyze path context using LLM (if structure_model provided)
                context_hints = {}
                if args.structure_model and metadata:
                     context_hints = _analyze_path_context(
                        metadata, 
                        args.ollama_bin, 
                        args.structure_model, 
                        processor.timeout
                    )
                    
                result = processor.run(path, task, context_hints=context_hints)
                
                # Enrich result with metadata
                result_dict = json.loads(result.to_json(indent=args.indent))
                result_dict["path_metadata"] = metadata
                
                # Save to disk if requested
                if args.output_dir:
                    # Use hash or original name? Using original name might overwrite if duplicates exist in different folders
                    # but the user wanted structured json. Let's use name + partial hash or keep original structure in output_dir
                    # For now: flat output with safe name
                    out_name = f"{path.stem}_{file_hash[:8]}.json"
                    outfile = args.output_dir / out_name
                    outfile.write_text(json.dumps(result_dict, indent=args.indent, ensure_ascii=False))
                    print(f"  -> Saved to {outfile}")

                manager.mark_completed(file_hash, result_dict)
            except Exception as e:
                print(f"  -> ERROR: {e}")
                manager.mark_failed(file_hash, str(e))
                # Optional: break or continue? Continue is better for batch processing.

        return

    # --- Original One-Shot Mode ---
    if args.images:
        image_paths = [Path(image) for image in args.images]
    else:
        pattern = args.pattern or "Screenshot_*"
        image_paths = discover_images(scan_root, pattern)
        if not image_paths:
            parser.error(
                f"No images found under {scan_root} matching pattern {pattern!r}."
            )

    results = []
    for image_path in image_paths:
        result = processor.run(Path(image_path), task)
        results.append(result)
        if args.output_dir:
            outfile = args.output_dir / f"{Path(image_path).stem}.{task.slug}.json"
            outfile.write_text(result.to_json(indent=args.indent))
            print(f"Wrote {outfile}")

    if not args.output_dir:
        payload = [json.loads(r.to_json(indent=args.indent)) for r in results]
        if len(payload) == 1:
            print(json.dumps(payload[0], indent=args.indent, ensure_ascii=False))
        else:
            print(json.dumps(payload, indent=args.indent, ensure_ascii=False))


if __name__ == "__main__":
    main()
