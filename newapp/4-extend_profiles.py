#!/usr/bin/env python3
"""Extend consolidated profile data using Ollama + Pydantic validation."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import ollama
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: ollama. Install it with 'pip install ollama'.") from exc

from pydantic import BaseModel, Field, ValidationError

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - convenience message
    raise SystemExit(
        "Missing dependency: tqdm. Install it with 'pip install tqdm' before running this script."
    )

APP_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = APP_ROOT / "consolidated_profiles.json"
DEFAULT_OUTPUT = APP_ROOT / "consolidated_profiles_enriched.json"
DEFAULT_MEDIA_ROOT = APP_ROOT / "media_profiles"
SCHEMA_DESCRIPTION = (
    "Extrae métricas de acompañantes (estatura, peso, edad, nombre, color de cabello, "
    "color de ojos, tarifas y datos de contacto)."
)


class PriceSlots(BaseModel):
    one_hour: Optional[str] = Field(
        None,
        description="Monto y moneda para 1 hora (ej. '100000 CRC' o '$200').",
    )
    two_hours: Optional[str] = Field(None, description="Monto para 2 horas.")
    three_hours: Optional[str] = Field(None, description="Monto para 3 horas.")
    overnight: Optional[str] = Field(None, description="Monto para toda la noche.")


def slugify(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    safe = safe.strip("_")
    return safe or "profile"


def _default_priceslots() -> PriceSlots:
    return PriceSlots(one_hour=None, two_hours=None, three_hours=None, overnight=None)


class ProfileExtraction(BaseModel):
    name: Optional[str] = Field(None, description="Nombre o alias principal.")
    age: Optional[int] = Field(None, description="Edad en años si está presente.")
    height: Optional[str] = Field(None, description="Estatura, conservar unidades originales.")
    weight: Optional[str] = Field(None, description="Peso, conservar unidades originales.")
    hair_color: Optional[str] = Field(None, description="Color de cabello.")
    eye_color: Optional[str] = Field(None, description="Color de ojos.")
    location: Optional[str] = Field(None, description="Ubicación o zona.")
    availability: Optional[str] = Field(None, description="Texto sobre horarios/disponibilidad.")
    contact: Optional[str] = Field(None, description="Información de contacto relevante.")
    prices: PriceSlots = Field(default_factory=_default_priceslots)
    implants: Optional[bool] = Field(None, description="Indica si tiene implantes.")
    uber: Optional[bool] = Field(None, description="Indica si requiere Uber.")
    cosmetic_surgeries: Optional[bool] = Field(None, description="Indica si ha tenido cirugías estéticas.")
    other_attributes: Optional[Dict[str, Any]] = Field(
        None,
        description="Cualquier otro atributo relevante no cubierto por los campos anteriores.",
    )


SCHEMA_JSON = json.dumps(
    ProfileExtraction.model_json_schema(),
    ensure_ascii=False,
    indent=2,
)

PROMPT_TEMPLATE = """Eres un analista experto en información de acompañantes.
Usa el texto disponible para llenar un JSON que cumpla estrictamente con el siguiente
esquema Pydantic:
{schema}

Instrucciones clave:
- Conserva nombres propios, zonas y formatos originales cuando existan.
- Si no hay dato, usa null.
- Las tarifas deben incluir el monto y la moneda textual disponible (por ejemplo "100 mil CRC").
- Devuelve solo JSON válido, sin explicaciones adicionales.

Texto de referencia:
{context}
"""


def run_ollama(ollama_host: Optional[str], model: str, prompt: str, timeout: int) -> str:
    client = ollama.Client(host=_normalize_host(ollama_host)) if ollama_host else ollama
    response = client.generate(model=model, prompt=prompt, stream=False)
    content = response.get("response")
    if isinstance(content, str):
        return content.strip()
    if content is None:
        return ""
    return str(content).strip()


def _normalize_host(host: Optional[str]) -> Optional[str]:
    if not host or host == "ollama":
        return None
    if host.startswith("http://") or host.startswith("https://"):
        return host
    return f"http://{host}"


def clean_response(text: str) -> str:
    cleaned = text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1]
        cleaned = cleaned.split("```", 1)[0]
    elif cleaned.startswith("```"):
        cleaned = cleaned.split("```", 1)[1]
        cleaned = cleaned.split("```", 1)[0]
    cleaned = _slice_json_object(cleaned)
    return cleaned.strip()


def _slice_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end >= start:
        return text[start : end + 1]
    return text


def ensure_json_payload(text: str) -> str:
    candidate = _slice_json_object(text.strip())
    if not candidate:
        return text
    try:
        json.loads(candidate)
        return candidate
    except json.JSONDecodeError:
        pass
    try:
        data = ast.literal_eval(candidate)
        return json.dumps(data, ensure_ascii=False)
    except (ValueError, SyntaxError):
        return candidate


def build_context(profile: Dict[str, Any]) -> str:
    sections: List[str] = []
    raw_responses = profile.get("raw_responses") or []
    if raw_responses:
        sections.append("\n\n".join(raw_responses))
    merged_struct = profile.get("merged_structured_data")
    if merged_struct:
        sections.append("Datos estructurados existentes:\n" + json.dumps(merged_struct, ensure_ascii=False))
    metadata = profile.get("merged_metadata")
    if metadata:
        meta_items = ", ".join(f"{k}: {v}" for k, v in metadata.items())
        sections.append(f"Metadatos de carpetas: {meta_items}")
    return "\n\n".join(sections).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=SCHEMA_DESCRIPTION)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Ruta a consolidated_profiles.json.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Archivo destino para el JSON enriquecido.",
    )
    parser.add_argument(
        "--ollama-bin",
        default=None,
        help="Host/URL de Ollama (por compatibilidad con banderas previas; default: http://127.0.0.1:11434).",
    )
    parser.add_argument("--model", default="mistral-nemo:latest", help="Modelo Ollama para extracción estructurada.")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout en segundos por solicitud al modelo.")
    parser.add_argument(
        "--limit",
        type=int,
        help="Procesar solo los primeros N perfiles (útil para pruebas).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Si existe un bloque 'extraction' previo, volver a generarlo.",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Omitir llamadas a LLM y solo reescribir metadatos/medios.",
    )
    parser.add_argument(
        "--fill-missing-only",
        action="store_true",
        help="Solo invocar el LLM si faltan campos clave en una extracción existente.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentación para el JSON de salida.",
    )
    parser.add_argument(
        "--media-root",
        type=Path,
        default=DEFAULT_MEDIA_ROOT,
        help="Directorio base donde viven las copias multimedia (default: media_profiles dentro de newapp).",
    )
    return parser.parse_args()


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set)):
        return len(value) == 0 or all(_is_blank(v) for v in value)
    if isinstance(value, dict):
        return len(value) == 0 or all(_is_blank(v) for v in value.values())
    return False


def extraction_has_gaps(extraction: Dict[str, Any]) -> bool:
    if not extraction:
        return True
    critical_fields = [
        "name",
        "age",
        "height",
        "weight",
        "hair_color",
        "eye_color",
        "location",
        "availability",
        "contact",
    ]
    for field in critical_fields:
        if _is_blank(extraction.get(field)):
            return True
    prices = extraction.get("prices") or {}
    standard_slots = ["one_hour", "two_hours", "three_hours", "overnight"]
    if all(_is_blank(prices.get(slot)) for slot in standard_slots):
        return True
    return False


def assign_media_folders(profiles: List[Dict[str, Any]]) -> None:
    slug_counts: Dict[str, int] = {}
    name_map: Dict[str, str] = {}
    for idx, profile in enumerate(profiles, start=1):
        display = profile.get("profile") or f"profile_{idx}"
        normalized_name = display.strip().lower()
        base = slugify(display)
        if normalized_name and normalized_name in name_map:
            profile["_media_folder"] = name_map[normalized_name]
            continue
        counter = slug_counts.get(base, 0)
        slug_counts[base] = counter + 1
        folder = base if counter == 0 else f"{base}_{counter + 1}"
        profile["_media_folder"] = folder
        if normalized_name:
            name_map[normalized_name] = folder


def rewrite_media_paths(profiles: List[Dict[str, Any]], media_root: Path) -> None:
    prefix = Path(media_root.name) if media_root.name else Path("media_profiles")
    for profile in profiles:
        folder = profile.pop("_media_folder", None)
        if not folder:
            continue
        folder_path = media_root / folder
        if not folder_path.exists():
            continue
        entries: List[str] = []
        canonical_seen: Set[str] = set()
        for candidate in sorted(folder_path.iterdir()):
            if not candidate.is_file():
                continue
            rel = str(prefix / folder / candidate.name)
            canonical_name = _canonical_media_name(candidate.name)
            if canonical_name in canonical_seen:
                continue
            canonical_seen.add(canonical_name)
            entries.append(rel)
        if entries:
            if profile.get("media") and "source_media" not in profile:
                profile["source_media"] = profile["media"]
            profile["media"] = entries
            profile["media_folder"] = str(prefix / folder)
        else:
            profile.setdefault("media", [])
            profile["media_folder"] = str(prefix / folder)


def _canonical_media_name(name: str) -> str:
    stem, dot, ext = name.partition(".")
    canonical_stem = re.sub(r"_\d+$", "", stem)
    return (canonical_stem + (dot + ext if dot else "")).lower()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"No se encontró el archivo de entrada: {args.input}")

    data = json.loads(args.input.read_text())
    profiles = data.get("profiles", [])
    if not profiles:
        raise SystemExit("El archivo no contiene perfiles para procesar.")

    assign_media_folders(profiles)
    processed = 0
    iterator = tqdm(profiles, desc="Enriqueciendo perfiles", unit="perfil")
    for profile in iterator:
        if args.limit and processed >= args.limit:
            break

        if args.skip_llm:
            continue

        existing_extraction = profile.get("extraction")
        if existing_extraction and not args.overwrite:
            if args.fill_missing_only:
                if not extraction_has_gaps(existing_extraction):
                    continue
            else:
                continue

        context = build_context(profile)
        if not context:
            profile["extraction"] = None
            continue

        prompt = PROMPT_TEMPLATE.format(schema=SCHEMA_JSON, context=context)
        try:
            response = run_ollama(args.ollama_bin, args.model, prompt, args.timeout)
            cleaned = clean_response(response)
            normalized = ensure_json_payload(cleaned)
            extraction = ProfileExtraction.model_validate_json(normalized)
        except ValidationError as exc:
            profile["extraction_error"] = f"Validation error: {exc}"
            continue
        except json.JSONDecodeError as exc:
            profile["extraction_error"] = f"JSON decode error: {exc}"
            continue
        except Exception as exc:  # noqa: BLE001
            profile["extraction_error"] = f"Ollama failed: {exc}"
            continue

        profile["extraction"] = extraction.model_dump()
        profile.pop("extraction_error", None)
        processed += 1

    rewrite_media_paths(profiles, args.media_root)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=args.indent))
    print(f"Perfiles enriquecidos escritos en {args.output}")


if __name__ == "__main__":
    main()
