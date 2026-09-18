# GlowSync expanded package — validation

Validated on 18 September 2026 in Linux with Python 3.12, Java 17 and Node 24.19.0.

## Backend integration

**11 integration tests passed** using isolated SQLite databases and the real Java HTTP service. The delivered `tests/run.py` covers:

- Complete Swiss Beauty pagination with 425 distinct listing IDs and the bundled catalogue totals.
- Region/category exclusion, brand/accent-aware search, variant-aware budget filtering, price sorting, unknown-price exclusion and invalid-query handling.
- Registration, password hashing, login/logout, CSRF, HttpOnly/SameSite sessions and authentication after database reopen.
- Owner assignment, access restrictions, wishlist deduplication, invalid-product rejection and cross-account isolation.
- Fresh, exact-variant, in-stock INR price-alert rules; baseline establishment; stale/imported/snapshot/out-of-stock suppression; new-low behavior and duplicate-alert prevention.
- JSON import validation, atomic rejection of an invalid file, stable-ID merging and authenticated export.
- Real Java palette responses, distinct undertone directions, published shade-name suggestions and profile persistence.
- Feed pagination completion, repeated-page rejection and non-INR rejection with controlled source fixtures.
- Source URLs, unique product/variant IDs, nonnegative integer prices and local application/model asset responses.
- Host/origin checks, rate limiting, unauthenticated access rejection and a representative additive legacy-schema migration.

## Interface integration

The actual `static/app.js` was executed in **jsdom** against real temporary Python and Java servers. The flow completed **19 HTTP requests without JavaScript errors or server errors**, checking:

- Initial product loading; catalogue navigation; brand filtering; empty search state; filter reset.
- Sign-up and resuming a save action that required an account.
- Product details, variant selection, official source links and two-product comparison.
- Persistent wishlist display and price-watch controls.
- Real Java palette generation and region-specific product browsing.
- Brand coverage display, owner catalogue controls and sign-out.

Both application JavaScript modules passed Node syntax checks. The interface test sources are included as optional development tests.

## Source and asset checks

- Nine public source feeds were fetched through every page until empty, yielding **3,758 listings**. Each source storefront returned **INR** from its metadata endpoint.
- Added **46 Maybelline** and **23 L’Oréal Paris** verified official India product-page references. They expose no invented live price, stock state or full shade list.
- Final seed: **3,827 listings** and **10,054 published variant/range entries** across **11 brands with products**. Six additional directory brands explicitly have no imported catalogue.
- **1,531 cached product photographs** plus two homepage copies are included. Other listings load their original remote image; failed loads have a text fallback. Not every listing has an offline image.
- The seven bundled MediaPipe files are nonempty and have SHA-256 checksums in `data/vendor-checksums.json`.
- The application launcher started both services successfully using the bundled Java 17 class and local Python environment.
- The final ZIP was extracted into a fresh temporary folder. It created a clean database, started Python and Java, reported the expected 3,827/10,054 catalogue counts, and served the homepage, script, hero image and model successfully.
- A real Lakmé price-watch check timed out. It retained the saved snapshot, left the watch awaiting a first successful live quote and generated no alert. Positive price-drop behavior was tested with controlled fixtures, not claimed as a successful live retailer check.

## Limits

The remote browser was unable to reach the local runtime and its URL policy blocked a local-file preview. **No real-browser visual, camera or MediaPipe inference validation was completed in this session.** The jsdom tests simulate the DOM and dialog/camera entry points; they do not test rendering, real camera permissions, photo uploads, detected landmark accuracy or WebAssembly inference in Chrome.

Windows execution, physical mobile devices, Safari/Firefox, multiple-face detection with a real group image, and visual breakpoints were not exercised. The responsive CSS, still-photo landmark logic and manual fallbacks are implemented but should be checked on your actual computer. The uploaded private database was not used for authentication testing.

Source availability, complete worldwide brand portfolios, live prices and image delivery are not guaranteed. Maybelline/L’Oréal coverage is partial; the six supplier-needed brands have no product inventory. No production deployment, payment integration, email delivery, password-recovery service or after-close scheduling was performed.
