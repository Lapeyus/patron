# Patron Catalog (web)

This folder contains a single-page static UI (`index.html`) that loads `catalog.json`.

## Password gate

`index.html` includes a client-side password prompt that **blocks loading `catalog.json`** until the correct password is entered.

- Default password: `set`
- Optional: **Remember on this device** (stores an auth marker in `localStorage`)
- Password hash constant: `AUTH_SHA256_B64` (stored in `index.html`)

### Change the password

Generate a new SHA-256 Base64 hash and replace `AUTH_SHA256_B64` in `index.html`:

```bash
python - <<'PY'
import hashlib, base64
pw = "YOUR_NEW_PASSWORD".encode()
print(base64.b64encode(hashlib.sha256(pw).digest()).decode())
PY
```

### “Remember on this device” details

When checked, the page stores a value in:

- `localStorage["patron_auth_sha256_b64_v1"]`

To “log out” / force re-authentication on the same browser:

```js
localStorage.removeItem("patron_auth_sha256_b64_v1");
location.reload();
```

## Legal disclaimer

After you authenticate, the UI shows an “Aviso legal / Legal notice” modal (one-time per device).

- Stored in: `localStorage["patron_disclaimer_ack_v2"]`

To show it again:

```js
localStorage.removeItem("patron_disclaimer_ack_v2");
location.reload();
```

## Running locally

Because the page fetches `catalog.json`, it should be served from a local web server (not opened via `file://`).

Example:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000/`.

## Media folder references (optional)

You can keep folder sources and expanded media paths separated:

```json
{
  "media_roots": ["media_profiles/Yansy"],
  "media": [
    "media_profiles/Yansy/IMG-20260202-WA0123.jpg",
    "media_profiles/Yansy/IMG-20260202-WA0124.jpg"
  ]
}
```

The script uses `media_roots` to build/refresh `media`:

- GitHub Actions deploy workflow (automatic)
- Local script (manual), when needed:

From `/Users/jvillarreal/Documents/Projects/patron/newapp`:
```bash
node ../web/scripts/expand-catalog-media.js --input ../web/catalog.json --output ../web/catalog.json --media-root ../web
```

From `/Users/jvillarreal/Documents/Projects/patron`:
```bash
node web/scripts/expand-catalog-media.js --input web/catalog.json --output web/catalog.json --media-root web
```

From `/Users/jvillarreal/Documents/Projects/patron/web`:
```bash
node scripts/expand-catalog-media.js --input catalog.json --output catalog.json --media-root .
```

Strict validation (fails when a profile has local media files but empty/missing `media_roots`):
```bash
node scripts/expand-catalog-media.js --input catalog.json --output catalog.json --media-root . --require-media-roots
```

Ad media interleaving (default from `media_profiles/000`):
```bash
node scripts/expand-catalog-media.js --input catalog.json --output catalog.json --media-root . --ads-root media_profiles/000 --require-media-roots
```
Rules:
- Ad images are injected once per profile library.
- Ad media is interleaved in deterministic pseudo-random order.
- If the profile has its own media, the first item is never an ad.
- Profiles without own media are left unchanged by ad injection.

Notes:

- Supported media extensions: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.mp4`, `.mov`, `.m4v`, `.webm`
- Folder references support both forms: `media_profiles/Yansy` and `media_profiles/Yansy/`
- Folder expansion is non-recursive (files directly in that folder only)
- Missing folder references fail fast in CI to catch typos
- If `media_roots` is missing, the script can derive roots from existing `media` file paths for backward compatibility
- CI deploy uses strict mode (`--require-media-roots`)

## Move media from `PATRON` into `media_profiles` (no duplicates)

Use the Python mover script to relocate photos/videos into profile folders and avoid duplicates by content:

```bash
python3 /Users/jvillarreal/Documents/Projects/patron/web/scripts/move_patron_media.py \
  --source /Users/jvillarreal/Documents/Projects/patron/web/PATRON \
  --target /Users/jvillarreal/Documents/Projects/patron/web/media_profiles \
  --create-missing-targets \
  --apply
```

Note: the mover skips screenshot images named `Screenshot_*.jpg` / `Screenshot_*.jpeg`.

After moving files, rebuild `catalog.json` media entries:

```bash
node scripts/expand-catalog-media.js --input catalog.json --output catalog.json --media-root . --require-media-roots
```

## Security note

This is a lightweight **UI gate** (client-side). It is not a replacement for real server-side authentication if you publish this catalog to the internet.

## Profile enable/disable flag

Each profile in `catalog.json` can be hidden from the UI by setting:

- `"enabled": false`

If the field is missing, it defaults to enabled/visible. (For convenience, `"disabled": true` is also supported.)

Example:

```json
{
  "profile": "011",
  "enabled": false
}
```

## WhatsApp contact links

If a profile has `extraction.contact` set to something like:

```json
{ "contact": "WhatsApp 62 40 45 12" }
```

the UI will render it as a clickable WhatsApp link and prefill a short message.

Notes:

- The link uses `https://wa.me/<E164>?text=...`.
- If the contact only contains **8 digits**, the UI assumes Costa Rica and prefixes `+506`.
- If `extraction.contact` is explicitly `null`, the UI shows a “Solicitar contacto / Ask for contact” button that opens WhatsApp to `+506 8409 8222` with a prefilled template.
