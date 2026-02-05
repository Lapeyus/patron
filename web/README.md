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

## Reviews

Profiles can optionally include a `reviews` array (strings) in `catalog.json`. If present, the profile modal will show a “Reseñas/Reviews” section.

Example:

```json
{
  "profile": "055",
  "reviews": ["Excelente experiencia, volvería a repetir."]
}
```
