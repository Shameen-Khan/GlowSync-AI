# Source and third-party assets

## MediaPipe

MediaPipe Tasks Vision **0.10.21**, including `vision_bundle.mjs` and SIMD/non-SIMD WebAssembly files, is bundled unmodified from the official package distribution:

- https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.21/
- Apache-2.0 license: `static/vendor/mediapipe/LICENSE`, sourced from https://raw.githubusercontent.com/google-ai-edge/mediapipe/v0.10.21/LICENSE
- Face Landmarker float16 model, version 1: https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
- Documentation: https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/web_js

Only on-device landmarks are requested, with at most two faces for rejecting group photos. No identity classification, blendshapes or facial transformation matrices are requested.

## Catalogue sources

Product facts were retrieved on 18 September 2026. Every normalized listing records its exact source URL and observation timestamp in `data/catalogue.json`. Original product identifiers and source variant identifiers are retained for the nine feed brands. Long marketing descriptions have not been copied.

| Brand | Public source |
|---|---|
| Lakmé | https://www.lakmeindia.com/products.json |
| Swiss Beauty | https://swissbeauty.in/products.json |
| SUGAR Cosmetics | https://in.sugarcosmetics.com/products.json |
| Plum | https://plumgoodness.com/products.json |
| RENÉE | https://www.reneecosmetics.in/products.json |
| MARS | https://marscosmetics.in/products.json |
| FACES CANADA | https://www.facescanada.com/products.json |
| Kiro | https://kirobeauty.com/products.json |
| Just Herbs | https://www.justherbs.in/products.json |
| Maybelline | https://www.maybelline.co.in/all-products |
| L’Oréal Paris | https://www.lorealparis.co.in/makeup |

Feed pagination used `limit=250&page=N` and continued until an empty page. Currency was verified with each store's `/meta.json`. “Complete feed” describes that response set, not a guarantee that the manufacturer exposes its entire portfolio.

Maybelline and L’Oréal entries come from selected verified official India product pages. Their stock, price and complete shade inventories were not connected. The application does not synthesize extra shades.

## Product imagery

Product photographs, brand names and marks belong to their respective owners. Images are used to identify the source product range; this project does not claim ownership, endorsement or a blanket commercial redistribution licence. The original image URL for every entry appears in `data/catalogue.json`. Cached filenames use the first 24 hex characters of the SHA-256 of that URL, followed by `.jpg`.

Cached photos are resized to at most 420 × 420 pixels and JPEG-compressed without recolouring or creating synthetic shade variants. Images that are not cached use their original remote source and require internet access. Photos identify ranges, not every shade.

The homepage uses two cached source photos: Lakmé 9to5 Hya Matte Foundation + Hyaluronic Acid (`hero-one.jpg`) and Swiss Beauty Moist Heist Lip Oil (`hero-two.jpg`). The original source URLs are present on their catalogue entries.

## Application dependencies

Flask 3.1.2 (BSD-3-Clause), Waitress 3.0.2 (ZPL-2.1), and Flask's transitive dependencies are installed with pip, not vendored. Java is provided by the user’s installed JDK/JRE. Python, HTML, CSS, JavaScript and Java application code in this reconstruction was written for this project.
