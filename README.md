# GlowSync AI

GlowSync AI is a local-first beauty discovery and shade exploration platform. It combines a searchable cosmetics catalogue with a browser-based shade studio, saved collections, price watches, and transparent catalogue provenance.

The project runs entirely on your computer during development. It does not process payments, place orders, or claim affiliation with the brands listed in the catalogue.

## Highlights

- Search, filter, sort, compare, and save products and exact variants.
- Browse products by brand, category, finish, budget, and reported availability.
- Explore lip, eye, brow, and face products through the Shade Studio.
- Use a camera preview, photo upload, or manual feature selection.
- Run face-outline detection locally with bundled MediaPipe assets.
- Store accounts, preferences, wishlists, alerts, and catalogue data in SQLite.
- Enable price watches and receive in-app notifications for qualifying price drops.
- Refresh connected public feeds or import authorized supplier catalogues.
- Keep source URLs, observation timestamps, variant identities, and image provenance with catalogue records.

## Technology

| Layer | Technology |
| --- | --- |
| Backend | Python, Flask, Waitress |
| Frontend | HTML, CSS, vanilla JavaScript |
| Local data | SQLite |
| Shade service | Java 17 |
| Vision | MediaPipe Tasks, WebAssembly |
| Testing | Python integration tests; optional Node.js/jsdom UI tests |

## Requirements

- Python 3.12 or newer
- Java JDK 17 or newer
- A current Chrome or Edge browser
- Node.js 22 or newer (optional, for UI integration tests)

No React application, Node server, cloud database, or API key is required to run GlowSync locally.

## Quick start

### Windows

1. Open this folder in VS Code.
2. Run `start-windows.bat`.
3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000).
4. Create a local account from **Sign in**.

The launcher creates `.venv` on first run, installs `requirements.txt`, compiles the Java service when a JDK is available, and starts the local application. Keep the terminal open while using the app. Press `Ctrl+C` to stop it.

To set up manually:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

### macOS and Linux

```sh
sh start-macos-linux.sh
```

Do not open `templates/index.html` directly or use a static-file server. The Python and Java services must be running together.

## Catalogue coverage

The bundled snapshot contains product data from configured public sources and selected official brand pages. Coverage is intentionally explicit: brands without a usable public feed are shown in the directory but do not receive invented products, shades, prices, ratings, or stock.

Catalogue records include:

- Product and variant identity
- Brand, category, finish, and published shade name
- Source URL and observation timestamp
- Price and availability when reported
- Original image URL and local cached images where available

Prices are dated observations and can change on the source storefront. A product image represents the product range; it is not a guaranteed preview of the selected shade.

## Catalogue management

The local owner account can open **The brands** and use **Catalogue workspace** to manage data:

- **Refresh connected brands** loads configured public feeds.
- **Refresh** updates one brand without affecting other brands.
- **Import product JSON** loads an authorized supplier catalogue.
- **Export catalogue** downloads the current active catalogue.

The command-line helper exposes the same workflows:

```powershell
.\.venv\Scripts\python.exe tools\catalogue.py status
.\.venv\Scripts\python.exe tools\catalogue.py sync --brand swiss-beauty
.\.venv\Scripts\python.exe tools\catalogue.py import path\to\supplier-products.json
```

Imports use `schema_version: 1`, stable product IDs, an official HTTPS URL, a Unix `observed_at` timestamp, and a `variants` array. Prices are decimal rupees in import files and integer paise internally. Use `null` for an unknown price or availability.

To configure another brand, update `data/brands.json` with verified website, product-link, and image hosts. Only configure `feed_base` when the storefront actually exposes the expected public Shopify JSON format; otherwise use a supplier import.

## Privacy and security

- The launcher binds to `127.0.0.1` only.
- Accounts and saved data remain in the local SQLite database.
- Passwords are hashed; sessions use HttpOnly cookies and CSRF protection.
- Catalogue queries isolate each user's saved products and preferences.
- Camera frames, uploaded photos, and detected landmarks remain in browser memory.
- Photos are not sent to Python, Java, the database, or a third-party AI service.
- Switching away from the page stops the camera; removing a photo clears it.

Shade suggestions are approximate editorial guidance based on published shade names and optional cheek-pixel sampling. They are not calibrated measurements, identity recognition, skin diagnosis, or guaranteed matches. Always swatch products before buying.

## Price watches

1. Save an exact product variant.
2. Open **Saved products** and enable **Watch this price**.
3. Select **Check watched prices** to establish a live baseline.
4. Later qualifying price drops create an in-app notification.

Checks require an available source and internet access. Stale or failed responses do not create alerts. Watches are available for connected feed products; reference-only ranges do not have a live price feed.

## Project structure

```text
backend/                 Flask API, authentication, catalogue, and database code
data/                    Brand configuration and bundled catalogue snapshot
java/                    Java shade and colour-palette service
static/                  Styles, frontend modules, cached product images, MediaPipe assets
templates/               Application HTML
tests/                   Python integration and optional UI test runners
tools/                   Catalogue status, sync, import, and export utilities
run.py                   Local Python and Java service launcher
requirements.txt         Python dependencies
```

Important files:

- `backend/app.py` - API routes, accounts, saved products, alerts, and catalogue jobs
- `backend/catalogue.py` - feed pagination, normalization, imports, and shade-name tags
- `backend/db.py` - SQLite schema and additive migrations
- `java/ShadeService.java` - palette generation service
- `static/app.js` - catalogue, account, comparison, and API interactions
- `static/studio.js` - camera, photo upload, landmarks, hit testing, and sampling
- `data/brands.json` - source and coverage configuration
- `data/catalogue.json` - bundled product snapshot and provenance

## Testing

Run the Python integration suite:

```powershell
.\.venv\Scripts\python.exe tests\run.py
```

The suite uses disposable SQLite databases and a separate Java port, so it does not modify `local.db`.

Optional UI integration tests require Node.js:

```powershell
npm install --prefix tests
.\.venv\Scripts\python.exe tests\run_ui.py
```

These tests exercise the real frontend against temporary local services. They do not replace browser testing for camera permissions, device hardware, or visual layout.

## Local data files

The repository intentionally excludes runtime-only files such as:

- `.venv/`
- `local.db*`
- `.session-key`
- `.env`
- `__pycache__/`

The app creates `local.db` and `.session-key` on first run. To preserve an existing local account and saved data, stop the app, back up the old database, copy it into the project folder, and then start GlowSync again. Keep these files private and never commit them.

## Troubleshooting

- **Python or Java is not found:** install Python 3.12+ and JDK 17+, then restart VS Code.
- **A dependency is missing:** run `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- **A port is busy:** stop the existing process or set `GLOWSYNC_PORT` and `GLOWSYNC_JAVA_PORT`.
- **The camera is unavailable:** use the local HTTP URL, grant browser permission, close other camera applications, or upload a photo.
- **A brand refresh fails:** the source may be unavailable, rate-limited, changed, or offline; the previous catalogue remains available.
- **The interface looks stale:** restart the app and perform a hard refresh with `Ctrl+F5`.

GlowSync is packaged as a local development project. A production deployment would require HTTPS, hardened session settings, access controls, background-job supervision, monitoring, and a durable server database.

## License and third-party notices

See [THIRD-PARTY.md](THIRD-PARTY.md) for bundled third-party assets and notices.
