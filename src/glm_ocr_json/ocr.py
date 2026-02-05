"""Tools for invoking GLM-OCR through Ollama and structuring the output."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import re
from typing import Dict, List, Sequence

from pydantic import ValidationError

from .schema import ProfileSchema

_DURATION_SYNONYMS = {
    "1 hora": ["1 hora", "1hr", "1 hr", "1h", "una hora"],
    "2 horas": ["2 horas", "2hr", "2 hrs", "2h", "dos horas"],
    "3 horas": ["3 horas", "3hr", "3 hrs", "3h", "tres horas"],
    "Toda la noche": [
        "toda la noche",
        "noche completa",
        "overnight",
        "9:00 pm a 7:00 am",
        "9 pm a 7 am",
        "9pm a 7am",
        "7 pm a 8 am",
        "9 pm a 6 am",
    ],
}

_AGE_PATTERN = re.compile(r"edad\s*[:\-]?\s*(\d{1,2})", re.IGNORECASE)
_NUMBER_PATTERN = re.compile(r"(\d+(?:[.,]\d+)*)")
_WHATSAPP_REGEX = re.compile(r"whatsapp[\s:]*([\+\d][\d\s\-]{5,})", re.IGNORECASE)
_PHONE_REGEX = re.compile(r"(?:tel(?:efono)?|contact(?:o|a|ala|ela)?)\D*([\+\d][\d\s\-]{5,})", re.IGNORECASE)


class OCRTask(Enum):
    """Supported GLM-OCR tasks exposed via Ollama."""

    TEXT = ("Text Recognition", "text")
    TABLE = ("Table Recognition", "table")
    FIGURE = ("Figure Recognition", "figure")

    def __init__(self, command: str, slug: str) -> None:
        self.command = command
        self.slug = slug

    @classmethod
    def from_slug(cls, slug: str) -> "OCRTask":
        normalized = slug.strip().lower()
        for task in cls:
            if task.slug == normalized:
                return task
        valid = ", ".join(t.slug for t in cls)
        raise ValueError(f"Unsupported task '{slug}'. Valid options: {valid}.")


@dataclass
class OCRResult:
    """Structured representation of an OCR inference response."""

    image: str
    task: str
    raw_response: str
    lines: List[str]
    key_values: List[Dict[str, str]]

    bullets: List[str]
    structured_data: Dict | None = None

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize the result to a JSON string."""

        return json.dumps(asdict(self), indent=indent, ensure_ascii=False)


class OCRProcessor:
    """Handles invocation of GLM-OCR through the Ollama CLI."""

    def __init__(
        self,
        *,
        ollama_bin: str = "ollama",
        model: str = "glm-ocr",
        structure_models: List[str] | None = None,
        timeout: int = 300,
    ) -> None:
        self.ollama_bin = ollama_bin
        self.model = model
        self.structure_models = structure_models or []
        self.timeout = timeout

    def run(self, image_path: Path, task: OCRTask = OCRTask.TEXT, context_hints: Dict | None = None) -> OCRResult:

        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        if not image_path.is_file():
            raise ValueError(f"Expected a file path, got directory: {image_path}")

        prompt = f"{task.command}: {image_path}"
        command: Sequence[str] = (
            self.ollama_bin,
            "run",
            self.model,
            prompt,
        )

        try:
            completed = subprocess.run(  # noqa: S603
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except FileNotFoundError as exc:  # pragma: no cover - runtime environment
            raise RuntimeError(
                "Ollama CLI not found. Please install Ollama 0.15.5+ and ensure it is on PATH."
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(exc.stderr.strip() or "Failed to run GLM-OCR") from exc

        raw_text = completed.stdout.strip()
        structured = _structure_text(raw_text)
        structured_payload = None
        for model_name in self.structure_models:
            structured_payload = self._structure_with_llm(model_name, raw_text, task, context_hints)
            if structured_payload:
                break
        if not structured_payload:
            structured_payload = self._baseline_profile(raw_text, structured, image_path)
        else:
            structured_payload = self._ensure_profile_defaults(structured_payload, image_path)

        return OCRResult(
            image=str(image_path),
            task=task.slug,
            raw_response=raw_text,
            lines=structured["lines"],
            key_values=structured["key_values"],
            bullets=structured["bullets"],
            structured_data=structured_payload,
        )

    def _structure_with_llm(self, model_name: str, raw_text: str, task: OCRTask, context_hints: Dict | None = None) -> Dict | None:
        """Use an LLM to structure the raw OCR text into JSON."""
        hints_str = ""
        if context_hints:
            hints_str = (
                f"\nCONTEXT HINTS (derived from folder structure):\n"
                f"- Name/Alias: {context_hints.get('name', 'Unknown')}\n"
                f"- Location: {context_hints.get('location', 'Unknown')}\n"
                f"- Suggested Age Group: {context_hints.get('age_group', 'Unknown')}\n"
                f"- Category/Tag: {context_hints.get('category', 'Unknown')}\n"
            )

        prompt = (
            f"You are an expert data extraction assistant for a Service Catalog. "
            f"The following text was OCR-scanned from a profile card or service menu.\n"
            f"{hints_str}\n"
            f"Your goal is to extract structured data into a JSON object matching this schema:\n"
            f"{{\n"
            f"  'name': string | null,\n"
            f"  'age': integer | null,\n"
            f"  'location': string | null,\n"
            f"  'prices': [ {{ 'duration': string, 'amount': integer, 'currency': 'CRC'|'USD' }} ],\n"
            f"  'services': [ string ],\n"
            f"  'contact': {{ 'whatsapp': string, 'phone': string, 'email': string, 'social': string }},\n"
            f"  'attributes': {{ 'height': string, 'weight': string, 'measurements': string, 'implants': boolean, 'hair_color': string, 'eye_color': string }},\n"
            f"  'raw_text': string\n"
            f"}}\n\n"
            f"Guidelines:\n"
            f"1. Normalize prices to numeric amounts. If '25 mil', amount is 25000.\n"
            f"2. Separate services from physical attributes.\n"
            f"3. Use 'CRC' for colones (₡) and 'USD' for dollars ($). Do NOT use 'EUR' or '€'.\n"
            f"4. If a field is missing, use null.\n"
            f"5. 'raw_text' MUST be a concise summary in Spanish, regardless of the input language.\n\n"
            f"RAW TEXT:\n{raw_text}\n\n"
            f"Response must be VALID JSON ONLY. Do not include 'Thinking...' or markdown blocks. Just the JSON."
        )

        command: Sequence[str] = (self.ollama_bin, "run", model_name, prompt)

        try:
            completed = subprocess.run(  # noqa: S603
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            response = completed.stdout
            # clean markdown
            clean_response = response.strip()
            if "```json" in clean_response:
                clean_response = clean_response.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_response:
                 clean_response = clean_response.split("```")[1].split("```")[0].strip()

            # Iterate all '{' to find valid JSON
            start_indices = [i for i, char in enumerate(clean_response) if char == '{']
            for idx in start_indices:
                try:
                    obj, _ = json.JSONDecoder().raw_decode(clean_response[idx:])
                    normalized = self._coerce_profile(obj, raw_text)
                    if normalized:
                        return normalized
                except json.JSONDecodeError:
                    continue
            
            # Fallback (likely fails if above loop didn't find anything)
            candidate = json.loads(clean_response)
            normalized = self._coerce_profile(candidate, raw_text)
            if normalized:
                return normalized

        except (subprocess.CalledProcessError, json.JSONDecodeError, Exception):
            return None

        return None

    def _coerce_profile(self, payload: Dict | None, raw_text: str) -> Dict | None:
        """Validate and normalize payload against ProfileSchema."""
        if not isinstance(payload, dict):
            return None
        data = payload.copy()
        data.setdefault("raw_text", raw_text)
        try:
            profile = ProfileSchema(**data)
            return profile.model_dump()
        except ValidationError:
            return None

    def _baseline_profile(self, raw_text: str, parsed: Dict[str, List[str]] | None, image_path: Path) -> Dict:
        """Heuristically populate schema fields using OCR key/value pairs."""
        key_values = (parsed or {}).get("key_values") or []
        lines = (parsed or {}).get("lines") or []
        payload: Dict = {
            "name": _derive_name_from_path(image_path),
            "age": _extract_age(key_values, raw_text),
            "location": _extract_location(key_values),
            "prices": _extract_prices(key_values, lines),
            "services": [],
            "attributes": _extract_attributes(key_values),
            "contact": _extract_contact_info(key_values, lines, raw_text),
            "raw_text": raw_text,
        }
        profile = ProfileSchema(**payload)
        return profile.model_dump()

    def _ensure_profile_defaults(self, payload: Dict, image_path: Path) -> Dict:
        """Fill in fallback fields (like name) when structuring output omits them."""
        data = payload.copy()
        if not data.get("name"):
            fallback = _derive_name_from_path(image_path)
            if fallback:
                data["name"] = fallback
        profile = ProfileSchema(**data)
        return profile.model_dump()

    def refine_existing(self, record: Dict, context_hints: Dict | None = None) -> Dict:
        raw_text = record.get("raw_response") or (record.get("structured_data") or {}).get("raw_text") or ""
        parsed = {
            "lines": record.get("lines") or [],
            "key_values": record.get("key_values") or [],
        }
        if not parsed["lines"] or not parsed["key_values"]:
            parsed = _structure_text(raw_text)
        task_slug = (record.get("task") or OCRTask.TEXT.slug).lower()
        try:
            task = OCRTask.from_slug(task_slug)
        except ValueError:
            task = OCRTask.TEXT

        structured_payload = None
        for model_name in self.structure_models:
            structured_payload = self._structure_with_llm(model_name, raw_text, task, context_hints)
            if structured_payload:
                break

        image_field = record.get("image") or record.get("ocr") or ""
        image_path = Path(image_field) if image_field else Path(".")

        if not structured_payload:
            structured_payload = self._baseline_profile(raw_text, parsed, image_path)
        else:
            structured_payload = self._ensure_profile_defaults(structured_payload, image_path)

        return structured_payload


def _structure_text(raw_text: str) -> Dict[str, List[str]]:
    """Best-effort conversion of free-form OCR text into JSON-friendly parts."""

    cleaned_lines = [line.strip() for line in raw_text.splitlines()]
    lines = [line for line in cleaned_lines if line]

    key_values: List[Dict[str, str]] = []
    bullets: List[str] = []

    for line in lines:
        normalized = line.lstrip("-•* ")
        if normalized != line:
            bullets.append(normalized)
        if ":" in normalized:
            key, value = normalized.split(":", 1)
            key_values.append({"key": key.strip(), "value": value.strip()})

    return {"lines": lines, "key_values": key_values, "bullets": bullets}


def _normalize_text(value: str) -> str:
    replacements = str.maketrans(
        "áéíóúäëïöüñÁÉÍÓÚÄËÏÖÜÑ¿?",
        "aeiouaeiounAEIOUAEIOUN  ",
    )
    return value.translate(replacements).lower().strip()


def _find_value(key_values: List[Dict[str, str]], aliases: List[str]) -> str | None:
    for entry in key_values:
        key = _normalize_text(entry.get("key", ""))
        for alias in aliases:
            if alias in key:
                return entry.get("value")
    return None


def _normalize_duration_from_text(text: str) -> str:
    if not text:
        return ""
    normalized = _normalize_text(text)
    for canonical, patterns in _DURATION_SYNONYMS.items():
        for pattern in patterns:
            if _normalize_text(pattern) in normalized:
                return canonical
    return ""


def _infer_currency(text: str) -> str:
    normalized = text.lower()
    if "usd" in normalized or "dolar" in normalized or "$" in normalized:
        return "USD"
    if "crc" in normalized or "col" in normalized or "₡" in text:
        return "CRC"
    return "CRC"


def _parse_amount_and_currency(text: str) -> tuple[int | None, str]:
    if not text:
        return (None, "CRC")
    currency = _infer_currency(text)
    normalized = text.lower()
    multiplier = 1000 if "mil" in normalized else 1
    number_match = _NUMBER_PATTERN.search(normalized)
    if not number_match:
        return (None, currency)
    number = number_match.group(1).replace(".", "").replace(",", ".")
    try:
        amount = float(number)
    except ValueError:
        return (None, currency)
    return (int(round(amount * multiplier)), currency)


def _extract_prices(
    key_values: List[Dict[str, str]],
    lines: List[str],
) -> List[Dict[str, str | int]]:
    prices: List[Dict[str, str | int]] = []
    seen = set()

    def add_price(duration: str, amount: int | None, currency: str) -> None:
        if amount is None:
            return
        key = (duration, amount, currency)
        if key in seen:
            return
        seen.add(key)
        prices.append({"duration": duration, "amount": amount, "currency": currency})

    for entry in key_values:
        combined = f"{entry.get('key', '')}: {entry.get('value', '')}"
        duration = _normalize_duration_from_text(combined)
        if not duration:
            continue
        amount, currency = _parse_amount_and_currency(entry.get("value", "") or combined)
        if amount is None:
            amount, currency = _parse_amount_and_currency(combined)
        add_price(duration, amount, currency)

    for line in lines:
        normalized_line = line.lstrip("-•* ").strip()
        duration = _normalize_duration_from_text(normalized_line)
        if not duration:
            continue
        amount, currency = _parse_amount_and_currency(normalized_line)
        if amount is None:
            parts = normalized_line.split(":", 1)
            if len(parts) == 2:
                amount, currency = _parse_amount_and_currency(parts[1])
        add_price(duration, amount, currency)

    return prices


def _extract_age(key_values: List[Dict[str, str]], raw_text: str) -> int | None:
    value = _find_value(key_values, ["edad"])
    if value:
        match = _NUMBER_PATTERN.search(value)
        if match:
            return int(match.group(1).split(",")[0])
    if raw_text:
        match = _AGE_PATTERN.search(raw_text)
        if match:
            return int(match.group(1))
    return None


def _extract_location(key_values: List[Dict[str, str]]) -> str | None:
    location = _find_value(key_values, ["zona donde vive", "ubicacion", "ubicacion actual"])
    if location:
        return location.strip()
    return None


def _boolean_from_spanish(value: str | None) -> bool | None:
    if not value:
        return None
    normalized = _normalize_text(value)
    if normalized.startswith("si"):
        return True
    if normalized.startswith("no"):
        return False
    return None


def _extract_attributes(key_values: List[Dict[str, str]]) -> Dict[str, str | bool | None]:
    attributes: Dict[str, str | bool | None] = {}
    height = _find_value(key_values, ["estatura", "altura"])
    if height:
        attributes["height"] = height.strip()
    weight = _find_value(key_values, ["peso"])
    if weight:
        attributes["weight"] = weight.strip()
    eye = _find_value(key_values, ["color de ojos", "color de ojo"])
    if eye:
        attributes["eye_color"] = eye.strip()
    hair = _find_value(key_values, ["color de cabello", "cabello"])
    if hair:
        attributes["hair_color"] = hair.strip()
    implants = _find_value(key_values, ["tenes implantes", "tenes implante", "tenes implantes", "implantes"])
    bool_implants = _boolean_from_spanish(implants)
    if bool_implants is not None:
        attributes["implants"] = bool_implants
    return attributes


def _clean_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if digits.startswith("00"):
        digits = digits[2:]
    return digits or None


def _extract_contact_info(
    key_values: List[Dict[str, str]],
    lines: List[str],
    raw_text: str,
) -> Dict[str, str]:
    contact: Dict[str, str] = {}
    sources = []
    for entry in key_values:
        sources.append(f"{entry.get('key', '')} {entry.get('value', '')}")
    sources.extend(lines)
    sources.append(raw_text)

    for source in sources:
        match = _WHATSAPP_REGEX.search(source)
        if match:
            digits = _clean_phone(match.group(1))
            if digits:
                contact["whatsapp"] = digits
                break

    for source in sources:
        match = _PHONE_REGEX.search(source)
        if match:
            digits = _clean_phone(match.group(1))
            if digits and digits != contact.get("whatsapp"):
                contact["phone"] = digits
                break

    return contact


def _derive_name_from_path(image_path: Path) -> str | None:
    try:
        parent_name = image_path.parent.name.strip()
    except Exception:
        return None
    candidate = re.sub(r"^[0-9]+[\s\-\)\(]*", "", parent_name).strip()
    candidate = candidate.strip("_- ")
    if candidate:
        return candidate
    return None
