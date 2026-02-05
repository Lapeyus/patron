# Patron OCR + Catalog Builder

This workspace wraps the `glm-ocr` Ollama model, converts the raw text into JSON, and assembles an interactive catalog site so the extracted data is easy to browse.

## Requirements

- **Python 3.10+** (the provided `.venv` uses 3.13)
- **Ollama 0.15.5+** with the `glm-ocr` family pulled locally (e.g. `ollama pull glm-ocr:latest`)
- Optional: any Ollama LLM you want to use for folder-context analysis (e.g. `gpt-oss:120b-cloud`)

> ℹ️ If the machine cannot reach PyPI, run the CLI via `PYTHONPATH=src python -m glm_ocr_json.cli …` instead of installing the package.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .              # requires PyPI access
ollama serve &                # ensure the daemon is reachable on 127.0.0.1:11434
```

## Running the OCR CLI

The CLI can either take explicit paths or recursively scan the Patron asset tree for `Screenshot_*` files.

### Quick scan (auto-discovery)

```bash
PYTHONPATH=src .venv/bin/python -m glm_ocr_json.cli --task text
```

- Searches `@patron/`, then `PATRON/`, then the CWD for matching screenshots.
- Prints structured JSON to STDOUT unless `--output-dir` is provided.

### Single file

```bash
PYTHONPATH=src .venv/bin/python -m glm_ocr_json.cli \
  "PATRON/2 - LESKY/Screenshot_20251213_160505_Gmail.jpg" \
  --task table \
  --output-dir output
```

> Replace the path above with the actual screenshot you want to process; the command will raise `FileNotFoundError` if the file does not exist.

### Pipeline mode (sequential processing + resume + multi-LLM structuring)

```bash
PYTHONPATH=src .venv/bin/python -m glm_ocr_json.cli \
  --task table \
  --scan-root "PATRON" \
  --pattern "Screenshot_*" \
  --output-dir output \
  --pipeline-db pipeline.db \
  --structure-model gpt-oss:120b-cloud \
  --structure-model llama3
```

- `--pipeline-db` enables the SQLite-backed queue that deduplicates screenshots and keeps track of completed jobs.
- `--structure-model` now accepts multiple entries; the CLI will try each LLM in order until one produces a valid `structured_data` payload. If all fail, heuristic parsing still runs so key fields (name, age, prices, location, contact) never come back empty.

### Common flags

| Flag | Description |
| ---- | ----------- |
| `--task` | `text`, `table`, or `figure` (maps to GLM-OCR prompt templates). |
| `--ollama-bin` / `--model` | Override the Ollama binary or pick a specific GLM-OCR variant (`glm-ocr:q8_0`, etc.). |
| `--structure-model` | One or more Ollama models for post-processing (repeat flag to chain multiple models). |
| `--scan-root`, `--pattern` | Control discovery root/pattern (defaults: scan `@patron`/`PATRON` for `Screenshot_*`). |
| `--output-dir`, `--indent` | Save prettified JSON artifacts instead of printing to STDOUT. |
| `--pipeline-db` | Persist job state across runs. |
| `--reprocess-json` | Re-run structuring on existing JSON files/directories without calling GLM-OCR. |

## Output Schema

Each screenshot produces a JSON payload similar to:

```json
{
  "image": "PATRON/2 - LESKY/Screenshot_20251213_160505_Gmail.jpg",
  "task": "text",
  "raw_response": "<LLM output>",
  "lines": ["Subject: Invoice Reminder", "Total due: $123.45"],
  "key_values": [
    {"key": "Subject", "value": "Invoice Reminder"}
  ],
  "bullets": ["Next payment due: January 15"],
  "structured_data": {
    "name": "Lesky",
    "age": 23,
    "location": "San José",
    "prices": [{"duration": "1 hora", "amount": 100000, "currency": "CRC"}],
    "standard_prices": {
      "one_hour": 100000,
      "two_hours": null,
      "three_hours": null,
      "overnight": null
    },
    "services": ["Coordinar con previo aviso"],
    "contact": {"whatsapp": "+506..." },
    "attributes": {"height": "1.61 m", "implants": "Sí"},
    "raw_text": "Full descriptive block…"
  },
  "path_metadata": ["2 - LESKY"]
}
```

The `structured_data` block is produced by heuristics plus optional LLM hints. You can expand this in `src/glm_ocr_json/ocr.py` and `build_catalog.py`.

## Building the Web Catalog

Once `output/` is populated, generate the consolidated dataset and open the gallery:

```bash
python build_catalog.py --output-dir output --web-dir web
open web/index.html
```

Features:

- Filters for location and services driven by the structured JSON.
- Cards show name + age when available and omit missing data (“Location Unknown”/“Hide” never appear).
- Clicking a card opens a lightbox with all extracted attributes, prices, services, and the free-form description.
- Use ←/→ keys (or the thumbnails) to switch images within the modal; Escape closes it.

## Reprocessing existing JSON (structure-only refresh)

If you already have OCR outputs under `output/` but want to re-run only the structuring pass (e.g., after adding better LLMs or parser upgrades), point the CLI at those JSON files or directories:

```bash
src .venv/bin/python -m glm_ocr_json.cli \
  --reprocess-json output \
  --structure-model kimi-k2:1t-cloud \
  --structure-model qwen3-vl:235b-cloud
python build_catalog.py --output-dir output --web-dir web
 
```

- Every `*.json` in `output/` is reloaded, the structuring models are invoked (in order) without calling GLM-OCR again, and the heuristics still fill any missing fields (name, age, prices, location, contact).
- Omit `--output-dir` to overwrite in place. Otherwise the new JSON lands in the provided directory with the same filenames.
- After reprocessing, rebuild the catalog (`python build_catalog.py --output-dir output_refined --web-dir web`) so the gallery reflects the enriched data.

## Testing

```bash
pytest
```

The tests focus on the text-structuring helpers and image discovery logic; add integration tests as needed when you customize the pipeline.

## Troubleshooting

- **`ModuleNotFoundError`**: Activate the venv or use `PYTHONPATH=src` when running without installing the package.
- **`dial tcp 127.0.0.1:11434: connect: operation not permitted`**: Start the Ollama daemon on the host; sandboxed shells must reach `127.0.0.1:11434`.
- **`pip install -e .` fails**: Supply local wheels for `setuptools`/`wheel` or skip installation and run via `PYTHONPATH` as shown above.
