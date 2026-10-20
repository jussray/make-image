# MakeImage | Juss & Co.

**Current status:** A functioning, local image compositing demo with a verified PNG output. This is **not** an AI image-generation model, an approved image release, or proof that an external provider is connected. The current `main` branch was previously a README-only placeholder; the older `export/make-image-contract` PR remains separate and review-only.

## Run an actual image flow

Requires Python 3.10+ and Pillow.

```bash
python3 -m pip install -r requirements.txt
python3 demo.py --title "Original visual" --subtitle "From storyboard to reference frame" --output out/keyframe.png --receipt out/keyframe.receipt.json
```

This renders an original 1280×720 PNG with a reproducible art seed and writes an independent JSON proof receipt. To render from a local creator-owned photo or artwork (original reference is never changed):

```bash
python3 demo.py --reference ./my-owned-reference.jpg --title "Scene one" --output out/scene-one.png --receipt out/scene-one.receipt.json
```

Supported source formats: local JPEG, PNG, WebP, 16 MiB max, max 24 megapixels. Output dimensions configurable using `--width` and `--height`. There is no network call, model call, API credential, remote upload, biometric identity matching, or publication. The original reference is opened read-only, the output strips source EXIF metadata, and both outputs refuse to overwrite a source or existing target. Read the rendered result before approving its use.

Long or unfit brand claims now fail closed rather than silently clipping text. Shorten the title or subtitle when the renderer reports a layout constraint.

## Actual flow and proof boundary

`source image (optional) / original local procedure -> validated composition -> PNG pixels on disk -> PNG readback -> SHA-256 provenance receipt -> human visual review -> separate publishing authority`.

Receipts include an input digest, output digest, continuity fingerprint and non-authorizing continuity cookie. They **do not** establish that an AI image provider rendered anything, nor do they grant likeness, copyright, or publication rights. Cross-product character continuity, when added, must match approved project-scoped, versioned references; do not infer it from a filename or generated resemblance. FCR holds external publication authorization. ULTRATHINK/JussOS governs evidence and authority, but remains a separate system. MakeVideo, StoryEngine, and other products remain peers.

## Verify

```bash
python3 -m unittest discover -s tests -v
```

The GitHub Actions image demo check runs the same tests. A passing test demonstrates local image export and provenance; external AI generation and UI Playwright proof are not claimed.