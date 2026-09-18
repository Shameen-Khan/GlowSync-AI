# GlowSync — Expanded VS Code Project

A local beauty discovery website built with **Python, Java, HTML, CSS and vanilla JavaScript**. Open this folder in VS Code and run it. No React, Node application server, npm build, cloud database or API key is needed to use the app.

This is a **new, complete reconstruction** based on the documentation you supplied. The attachment set contained only eight root files; the original `backend/`, `templates/`, `static/` and `java/` directories were missing. The old website's exact layout and source could not be recovered from `http://127.0.0.1:8000`, which is an address on your computer. Your uploaded database and original files have not been changed.

## Start on Windows

1. Install **Python 3.12 or newer** and **Java JDK 17 or newer**. Enable “Add Python to PATH”. Restart VS Code after installation.
2. Extract the ZIP. Open the **GlowSync** folder using **File → Open Folder** in VS Code.
3. Double-click **start-windows.bat**. The first run creates a Python environment and installs two application dependencies.
4. Open **http://127.0.0.1:8000** in Chrome or Edge.
5. Choose **Sign in → New here? Create an account**. The first account is the local catalogue owner. Browsing and the studio work without an account.

Keep the terminal open. Press **Ctrl+C** to stop the services. To start again, double-click `start-windows.bat`.

Or run these commands in the VS Code terminal:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Do not use **Live Server** or open `index.html` directly: the Python and Java services must be running.

## What is in the catalogue?

The bundled data, retrieved on **18 September 2026**, contains **3,827 product listings** and **10,054 variant or range entries** across **11 brands**. “Listing” includes kits, accessories, offers and separate pack listings returned by a source; it does not mean 3,827 distinct cosmetic formulas. The 69 Maybelline/L'Oréal entries are range references, not exact saleable SKU variants.

| Brand | Bundled listings | Coverage |
|---|---:|---|
| Lakmé | 281 | Complete pagination of the accessible public feed |
| Swiss Beauty | 425 | Complete pagination of the accessible public feed |
| SUGAR Cosmetics | 390 | Complete pagination of the accessible public feed |
| Plum | 408 | Complete pagination of the accessible public feed |
| RENÉE | 325 | Complete pagination of the accessible public feed |
| MARS | 236 | Complete pagination of the accessible public feed |
| FACES CANADA | 241 | Complete pagination of the accessible public feed |
| Kiro | 318 | Complete pagination of the accessible public feed |
| Just Herbs | 1,134 | Complete pagination of the accessible public feed |
| Maybelline New York | 46 | Selected verified official India product pages |
| L’Oréal Paris | 23 | Selected verified official India product pages |

The brand directory also includes **Colorbar, Nykaa Cosmetics, Kay Beauty, M·A·C, Huda Beauty and e.l.f.** with an explicit “Supplier catalogue needed” state. These six brands have **no bundled product inventory**. They are not counted among the 11 brands with products.

**This does not contain every product from every cosmetic brand in India.** Complete coverage of brands without a usable public feed requires a manufacturer, distributor or authorized retailer catalogue. No invented products, shades, prices, ratings or stock have been used to fill those gaps. Some listed brands are international brands available to Indian shoppers, not Indian-owned brands.

The website exposes the same coverage information under **The brands**. Each listing includes an official source link. `data/catalogue.json` records the source URL, observation timestamp, original variant identity and image URL. Source prices from the nine feeds were accepted only after confirming each storefront's currency as INR. Prices are dated quotes and may already have changed.

## Connected features

- Responsive homepage, product catalogue, shade studio, brand directory and saved collection.
- Search by brand, product and published variant name; brand, category, finish, budget and reported-stock filters; sorting and pagination.
- Variant selection, product details, source links and comparison of up to four selected products.
- Local account registration, login, logout, name editing and saved studio preferences.
- Password hashing, HttpOnly sessions, CSRF protection, sign-in throttling and user-isolated saved collections.
- Persistent wishlists for exact variants, up to 30 enabled price watches and in-app notifications.
- Browser camera preview/capture and JPEG/PNG/WebP upload. Local, bundled MediaPipe detects face outlines on a still photo.
- Tap detected lips, eyes, eyebrows or face to browse the relevant products; manual feature buttons work without a photo.
- Approximate cheek-pixel tone suggestions, editable tone/undertone settings, and Java-generated outfit/occasion colour palettes.
- Foundation suggestions from conservative interpretations of **published shade names**. Numeric-only shade labels are not assigned an invented tone. These are candidates to swatch, not calibrated matches.
- Owner-only public-feed refresh, supplier JSON import and catalogue JSON export.
- Atomic full-feed updates: a failed or repeated page cannot replace the catalogue with a partial result. Previously saved, discontinued records remain visible.

Purchases take place on the brand's website via **Visit brand**. GlowSync does not accept payments, place orders or claim retailer affiliation.

## Refresh and add more products

Sign in with the **local owner account**, open **The brands**, and use **Catalogue workspace**:

- **Refresh connected brands** loads every page of each configured public feed. Each brand has its own result. A network error retains the previous data.
- A brand's **Refresh** button refreshes just that brand.
- **Import product JSON** accepts an authorized supplier catalogue in the format shown in `data/import-example.json`.
- **Export catalogue** downloads the current active catalogue in the import format.

Imports update products by stable `id`; variants on that product are replaced by the supplied variant list. Omit no variants that you want to keep. Unmentioned products and saved records are retained. Imported prices remain dated snapshots and never trigger alerts. An imported item is not automatically treated as a verified live-feed product; refreshing its official connected feed restores its live-feed metadata.

To support another brand, add a record in `data/brands.json`, including verified HTTPS website, product-link hosts and image hosts, then restart. Only add `feed_base` for an INR storefront that actually exposes the expected public Shopify JSON format. Otherwise leave it `null` and import a supplier file. Do not add private-network addresses or credentials to URLs.

You can also run these commands with the app stopped:

```powershell
.\.venv\Scripts\python.exe tools\catalogue.py status
.\.venv\Scripts\python.exe tools\catalogue.py sync --brand swiss-beauty
.\.venv\Scripts\python.exe tools\catalogue.py import path\to\supplier-products.json
```

Imports require `schema_version: 1`, configured `brand`, stable `brand:product-id`, valid category, official `url`, an actual Unix `observed_at` timestamp and a `variants` array. Prices in import files use decimal **rupees**, such as `499.50`; internal stored prices use integer **paise**. Use `null` for unknown price or availability. Do not use a future date to make a quote appear fresh.

## Price watches

1. Save an exact product variant.
2. Open **Saved products** and enable **Watch this price**.
3. Select **Check watched prices**. The **first successful live check** sets the baseline; an old bundled price does not set it.
4. A later fresh, in-stock INR quote below the lowest price observed since enabling that watch creates an alert. Repeated identical quotes do not create duplicates.

The app also checks enabled watches every five minutes while the signed-in tab is visible. Checks require internet access and an available source; an error is shown and stale prices never create a new alert. There is no email delivery, browser push or background scheduling after the app closes. Watches are offered only for connected feed products; the 69 reference ranges have no price feed.

A live Lakmé price-check attempt during validation timed out and correctly retained the snapshot without setting a baseline or generating an alert. Successful price-drop behavior was verified with controlled source fixtures. Live source availability is not guaranteed.

## Photos, shades and privacy

The model, JavaScript runtime and WebAssembly files are bundled under `static/vendor/mediapipe/`; they do not need to download from an AI service at runtime. Photos and landmarks remain in browser memory and are never sent to Python, Java, a database or a third party. Removing a photo clears it. Switching away from the tab stops the camera.

Detection runs on a captured or uploaded **still photo**, not continuously on the preview. No-face, multiple-face and model-error states offer manual feature controls. Use a clear front-facing photo of one person. Lighting, camera settings and makeup affect colour sampling. Lip/eye/brow taps do not change the skin-tone control.

Product cards use real range photos. **A range photo is not a preview of the selected shade.** Many photos are bundled locally; other product images load from the source image host and need internet access. Failed images show “Photo unavailable”. No product photo is recoloured to simulate another variant.

Tone hints and name-based foundation suggestions are editorial approximations, not physical shade measurements, identity recognition, skin diagnosis or guaranteed matches. Undertone remains a manual preference. Swatch products before buying.

## Keep your existing account data

The delivered ZIP contains **no user database, session secret or pre-created account**. The app creates a clean `local.db` and private `.session-key` on first run.

If you want to use your previous local accounts and saved records:

1. Stop both versions of GlowSync.
2. Make a backup of your original `local.db`.
3. Copy that database into this folder **before starting the new app**.
4. Run `start-windows.bat`. The additive SQLite migration preserves the old users, password hashes, wishlist and notification records, and assigns the earliest existing account as local owner.

Old saved product IDs may not exist in the expanded catalogue. They remain as “Previously saved product” records instead of being silently mapped to another item. Sign in again after migration. Password hash compatibility depends on the original app's hashing format; the uploaded private account records were not used for testing. A representative legacy-schema migration was tested.

## Folder guide

| File / folder | Purpose |
|---|---|
| `run.py` | Starts and stops the local Python and Java services |
| `backend/app.py` | Flask API, accounts, product queries, saved variants, alerts and import jobs |
| `backend/catalogue.py` | Feed pagination, normalization, import validation and editorial shade-name tags |
| `backend/db.py` | SQLite schema and additive migration |
| `java/ShadeService.java` | Java colour-palette service |
| `templates/index.html` | Page structure and dialogs |
| `static/style.css` | Responsive visual design |
| `static/app.js` | Search, filters, dialogs, accounts, comparisons and API calls |
| `static/studio.js` | Camera, local photos, landmarks, hit testing and sampling |
| `data/brands.json` | Source and coverage configuration |
| `data/catalogue.json` | Bundled product snapshot and provenance |
| `static/products/` | Locally cached range photographs |
| `tests/run.py` | Python integration tests using the real Java service |
| `tools/catalogue.py` | Catalogue refresh/import/status command line interface |

Java source and its matching Java 17 `.class` are included. The launcher recompiles when `javac` is installed and otherwise checks the bundled class against `java/source.sha256`. Install a full JDK to edit Java code.

## Tests

```powershell
.\.venv\Scripts\python.exe tests\run.py
```

Tests use disposable SQLite databases and a separate Java port. They never touch your `local.db`. See `TEST-RESULTS.md` for the tested scope and limits.

Optional interface integration tests use Node 22+ and jsdom **only for testing**:

```powershell
npm install --prefix tests
.\.venv\Scripts\python.exe tests\run_ui.py
```

These tests execute the real frontend against temporary Python/Java servers in a simulated DOM. They do not replace testing camera permissions and page layout in a real browser.

## macOS / Linux

Install Python 3.12+ and JDK 17+, then run:

```sh
sh start-macos-linux.sh
```

## Troubleshooting

- **Python or Java not found:** install both, restart VS Code, then check `py --version`, `java -version` and `javac -version`.
- **Dependency missing:** run `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- **Port busy:** stop the old app. Or set `$env:GLOWSYNC_PORT='8002'` and `$env:GLOWSYNC_JAVA_PORT='8082'` before running `run.py`.
- **Camera unavailable:** use the local HTTP address, allow the browser camera permission, close other camera apps or upload a photo.
- **No shade suggestions:** a matching published shade name may not be available. Browse all face products rather than changing your tone to force a result.
- **No price at your budget:** variants with unknown prices are deliberately excluded; the hidden count is shown.
- **Brand refresh fails:** internet access, source changes, rate limits or source restrictions may prevent a refresh. The existing data remains usable.
- **Styling seems old:** restart and press **Ctrl+F5**. Copy the entire folder, not just the launcher.

The launcher binds to **127.0.0.1 only**. This package is a local development project, not a production deployment. Hosting would require HTTPS, production session settings, access controls, background-job supervision and a durable server database. The original running website has not been changed.
