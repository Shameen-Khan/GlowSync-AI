# GlowSync AI

**Explore beauty products through an interactive shade studio.**

Choosing makeup online often means switching between product pages, shade names and photos that do not quite answer the same question: where should I start? GlowSync brings those pieces into one place. Capture or upload a photo, select a facial feature, explore relevant products and save the exact variants you want to revisit.

Built by **Shameen Khan**, GlowSync is a local full-stack application using Python, Java and vanilla JavaScript. Face landmarks run in the browser with MediaPipe; the catalogue, accounts and saved products are managed by a Flask backend and SQLite.

## What you can do

- **Explore by facial feature.** Tap the detected lips, eyes, eyebrows or face to see relevant product categories. Manual feature controls are also available.
- **Try the shade studio.** Get an approximate skin-tone suggestion from a photo, adjust tone and undertone yourself, and explore outfit- and occasion-based colour palettes.
- **Browse and compare.** Search products and published variant names, filter by brand, category, finish, budget or reported availability, and compare up to four products.
- **Save specific variants.** Create a local account, maintain a wishlist and keep your studio preferences between sessions.
- **Watch prices.** Enable watches for supported products and receive in-app alerts when a fresh quote meets the price-drop rules.
- **Manage the catalogue.** The local owner can refresh connected brand feeds, import supplier JSON and export catalogue data.
- **Visit the source.** Product links open the brand's website, where purchases take place.

## How the photo experience works

1. Open the shade studio and capture a photo or select a JPEG, PNG or WebP image.
2. MediaPipe finds facial landmarks on the captured or uploaded image.
3. Select an outlined feature to browse the corresponding products.
4. Review the suggested tone and adjust it if needed before exploring shade candidates.

| Selected feature | Product categories |
| --- | --- |
| Lips | Lipstick, lip gloss, lip liner and lip balm |
| Eyes | Mascara, eyeliner and eyeshadow |
| Eyebrows | Eyebrow products |
| Face | Face makeup categories configured in the catalogue |

The camera provides a live preview, but analysis runs on a **still image**, not continuously on the video. Photos and landmarks stay in browser memory; they are not uploaded to the backend. The bundled model runs locally, and manual controls remain available if detection fails.

Tone sampling depends on lighting, camera settings and makeup. Foundation suggestions use published shade names rather than a calibrated matching model. Treat them as candidates to swatch, not a guaranteed match. Undertone is a manual preference. GlowSync does not identify people or diagnose skin conditions.

## Run locally

You need **Python 3.12+** and **Java JDK 17+**. Install both and reopen your terminal so they are available on PATH.

```sh
git clone https://github.com/Shameen-Khan/GlowSync-AI.git
cd GlowSync-AI
```

### Windows

Double-click `start-windows.bat`, or run the following in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

### macOS and Linux

```sh
sh start-macos-linux.sh
```

Open **http://127.0.0.1:8000**. Keep the terminal open while using the app; press **Ctrl+C** to stop it.

The first run creates a local SQLite database and a private session key. There are no pre-created accounts. The first registered account becomes the local catalogue owner. Browsing and the studio work without signing in.

No cloud API key or Node application server is required. The first dependency installation needs internet access. Feed refreshes, live price checks, brand links and uncached product images also require a connection.

> Run the Python launcher rather than VS Code Live Server or `index.html` directly. The app needs both its Python and Java services.

## Technology

| Layer | Implementation |
| --- | --- |
| Interface | HTML, CSS and vanilla JavaScript |
| Face landmarks | Bundled MediaPipe Tasks Vision model and WebAssembly runtime |
| Backend | Python, Flask 3.1.2 and Waitress 3.0.2 |
| Local storage | SQLite |
| Palette service | Java 17 |
| Accounts | Hashed passwords, HttpOnly sessions, CSRF checks and sign-in throttling |
| Tests | Python integration suite; optional Node/jsdom interface tests |

## Catalogue and product data

The bundled snapshot is dated **18 September 2026** and contains **3,827 listings** with **10,054 variant or range entries** across **11 brands**. Listings include kits, accessories and pack offers; the count does not represent distinct cosmetic formulas.

Nine brands have connected public feeds: Lakmé, Swiss Beauty, SUGAR Cosmetics, Plum, RENÉE, MARS, FACES CANADA, Kiro and Just Herbs. Maybelline New York and L’Oréal Paris contribute 69 selected product-range references without connected prices or complete shade inventories.

The brand directory also lists brands awaiting supplier catalogues. Those entries do not imply that products are available in the app. Prices and availability are dated observations and can change. Product photographs show a range, not necessarily the selected shade.

Source URLs and observation timestamps are stored in `data/catalogue.json`. See [THIRD-PARTY.md](THIRD-PARTY.md) for source details and asset attribution.

### Refresh or import products

Sign in as the local owner and open **The brands → Catalogue workspace** to refresh connected feeds, import a supplier file or export the catalogue. A failed feed refresh retains the previous data.

For command-line maintenance, stop the app first. These commands use the Windows virtual environment; on macOS/Linux use `.venv/bin/python` instead.

```powershell
.\.venv\Scripts\python.exe tools\catalogue.py status
.\.venv\Scripts\python.exe tools\catalogue.py sync --brand swiss-beauty
.\.venv\Scripts\python.exe tools\catalogue.py import path\to\supplier-products.json
```

Use [data/import-example.json](data/import-example.json) as the import template. Import prices are decimal rupees; stored prices use integer paise. Use `null` for unknown prices or availability. Imports update products by stable ID and replace the supplied product's variant list, so include every variant you intend to keep. Unmentioned products are retained.

## How price watches work

Save a product variant, enable **Watch this price**, then choose **Check watched prices**. The first successful live check establishes the baseline. A later fresh, in-stock INR quote below the lowest observed price since enabling the watch creates an in-app alert. Repeated identical quotes do not create duplicate alerts.

The app supports up to 30 enabled watches and checks them every five minutes while the signed-in tab is visible. Only products with a connected feed support watches. Imported or stale prices do not trigger alerts.

**This version does not send email or Gmail notifications, browser push notifications, or scheduled alerts after the app closes.** A working source feed and internet connection are required for live checks.

## Project layout

| Path | Purpose |
| --- | --- |
| `run.py` | Starts and stops the Python and Java services |
| `backend/` | API routes, accounts, database and catalogue processing |
| `java/ShadeService.java` | Colour-palette service |
| `templates/index.html` | Page structure and dialogs |
| `static/app.js` | Catalogue, account, comparison and wishlist interactions |
| `static/studio.js` | Camera, photo analysis and facial-feature selection |
| `static/style.css` | Responsive styling |
| `static/vendor/mediapipe/` | Face model, runtime and third-party licence |
| `static/products/` | Cached product-range photographs |
| `data/` | Brand configuration, catalogue snapshot and import example |
| `tools/catalogue.py` | Catalogue maintenance commands |
| `tests/` | Backend/Java integration and simulated interface tests |

The Java 17 compiled class is included with the source. The launcher recompiles when `javac` is available; otherwise it checks the source checksum before using the bundled class.

## Tests

Run the Python integration suite from the project root:

```powershell
.\.venv\Scripts\python.exe tests\run.py
```

The tests use temporary databases and a separate Java port. They cover catalogue queries, accounts, saved variants, price-alert logic and other backend flows without changing your local account database.

Optional interface tests require **Node.js 22+**:

```sh
npm install --prefix tests
```

```powershell
.\.venv\Scripts\python.exe tests\run_ui.py
```

These interface tests use a simulated DOM. Camera permissions, actual model detection and responsive layout still need real-browser testing. [TEST-RESULTS.md](TEST-RESULTS.md) contains the validation notes supplied with the project; live source availability is not guaranteed by fixture-based tests.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Python or Java is missing | Install the required versions, restart the terminal, and check `python --version`, `java -version` and `javac -version`. |
| A port is already in use | Stop the other instance, or set different `GLOWSYNC_PORT` and `GLOWSYNC_JAVA_PORT` values before launching. Defaults are 8000 and 8081. |
| Camera will not open | Use the localhost address, allow camera access, close other camera apps, or upload a photo. |
| A feed refresh fails | Check the connection and source availability. The existing snapshot remains usable. |
| A product has no shade suggestion | Its published shade name may not support a reliable classification. Browse the relevant category manually. |

## Development and deployment

This repository is configured for **local use**. Both services bind to loopback, and the backend rejects non-local hosts. Pushing the code to GitHub does not deploy the website; GitHub Pages cannot run the Python and Java backend.

A hosted release needs deliberate deployment work, including HTTPS, host configuration, secure session settings, controlled owner provisioning, durable storage and supervised jobs. Keep `local.db`, `.session-key`, environment files and credentials out of commits; the repository's `.gitignore` excludes local runtime data.

To contribute, describe the behaviour you want to improve in an issue or pull request and include relevant verification. Keep product facts traceable to their sources and document the limits of any new matching or notification feature.

## Credits

Created by [Shameen Khan](https://github.com/Shameen-Khan).

MediaPipe and other dependencies retain their respective licences. Product photographs, brand names and marks belong to their owners. See [THIRD-PARTY.md](THIRD-PARTY.md) for attribution. This repository does not include a project-wide open-source licence.
