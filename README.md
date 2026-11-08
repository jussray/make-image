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
## Export a local composite to MakeVideo (no accounts, no uploads)

After rendering a MakeImage PNG and its matching local receipt, export an
ordinary MakeVideo storyboard. The importer reads the source but does not modify
or delete the PNG, receipt, or existing storyboard. It refuses an output filename
that already exists. The tool checks PNG bytes, dimensions, and SHA-256 against
the receipt before creating a bounded embedded JPEG preview.

```sh
python3 export_makevideo.py --image out/keyframe.png \
  --receipt out/keyframe.receipt.json \
  --output out/scene-for-makevideo.json \
  --title "Juss & Co scene" --format 9:16
```

Open the generated `.json` using **Import** in MakeVideo's browser studio, then
review the shot and export an animatic. MakeVideo's browser app also has a
separate **MakeImage proof handoff** control accepting the original PNG and
receipt directly (once that MakeVideo change is deployed).

The storyboard stores a compressed copy of the source image, plus a SHA-256 and
continuity note. It deliberately does not copy local filesystem paths from
receipts. A digest match confirms file integrity relative to the supplied
receipt, **not** the identity of its creator, AI generation, usage rights,
or permission to publish. Continue to human review and FCR authorization.
This is a local asset handoff, not a Cutaway plugin or remote AI backend.
