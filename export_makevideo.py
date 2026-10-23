#!/usr/bin/env python3
"""Export a verified local MakeImage PNG as a portable MakeVideo storyboard.

The receipt proves only matching local file bytes, NOT trusted provenance,
AI inference, asset rights, or approval to publish. Never modifies inputs.
"""
from __future__ import annotations

import argparse
import base64
from io import BytesIO
import json
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
from PIL import Image, ImageOps, UnidentifiedImageError
from demo import sha256

RECEIPT_SCHEMA = "makeimage/local-composite/v1"
STORYBOARD_SCHEMA = "makevideo/storyboard/v1"
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
FORMAT_SIZE = {"16:9": (960, 540), "9:16": (540, 960), "1:1": (720, 720)}
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_RECEIPT_BYTES = 64 * 1024
MAX_IMAGE_CHARS = 105_000


class HandoffError(ValueError):
    """A source or output failed explicit validation."""


def _receipt(path: Path) -> dict:
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_RECEIPT_BYTES:
        raise HandoffError("MakeImage receipt must be a local JSON file <= 64 KiB.")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise HandoffError("MakeImage receipt is not valid JSON.") from exc
    if not isinstance(value, dict):
        raise HandoffError("MakeImage receipt must be a JSON object.")
    if value.get("schema") != RECEIPT_SCHEMA or value.get("state") != "VERIFIED_LOCAL_RENDER":
        raise HandoffError("Unsupported or unverified MakeImage receipt.")
    output = value.get("output")
    if not isinstance(output, dict) or output.get("format") != "PNG":
        raise HandoffError("MakeImage receipt must identify PNG output.")
    digest = output.get("sha256")
    if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
        raise HandoffError("MakeImage receipt is missing a valid SHA-256 digest.")
    fingerprint = value.get("continuity_fingerprint")
    if not isinstance(fingerprint, str) or not SHA_RE.fullmatch(fingerprint):
        raise HandoffError("MakeImage receipt lacks a valid continuity fingerprint.")
    if value.get("continuity_cookie", {}).get("publish_authority") is not False:
        raise HandoffError("MakeImage receipt must not claim publishing authority.")
    return value


def export_storyboard(image: Path, receipt: Path, output: Path, *,
                      title: str = "MakeImage scene", aspect: str = "16:9") -> dict:
    if aspect not in FORMAT_SIZE:
        raise HandoffError("Unsupported aspect ratio.")
    if not isinstance(title, str) or not title.strip() or len(title) > 100:
        raise HandoffError("Project title must be 1 to 100 characters.")
    image = image.expanduser().resolve(strict=True)
    receipt = receipt.expanduser().resolve(strict=True)
    output = output.expanduser().resolve()
    if len({image, receipt, output}) != 3:
        raise HandoffError("Input files and output must have distinct paths.")
    if image.suffix.lower() != ".png" or not 0 < image.stat().st_size <= MAX_IMAGE_BYTES:
        raise HandoffError("Image must be a local PNG <= 8 MiB.")
    if output.suffix.lower() != ".json":
        raise HandoffError("Storyboard must be saved as JSON.")
    if output.exists():
        raise HandoffError("Refusing to overwrite an existing storyboard.")

    proof = _receipt(receipt)
    if sha256(image) != proof["output"]["sha256"]:
        raise HandoffError("Image bytes do not match the MakeImage receipt.")
    try:
        with Image.open(image) as opened:
            if opened.format != "PNG" or opened.width * opened.height > 20_000_000:
                raise HandoffError("Expected a PNG with at most 20 megapixels.")
            if opened.size != (proof["output"].get("width"), proof["output"].get("height")):
                raise HandoffError("PNG dimensions differ from the receipt.")
            canvas = ImageOps.fit(opened.convert("RGB"), FORMAT_SIZE[aspect],
                                  method=Image.Resampling.LANCZOS)
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        if isinstance(exc, HandoffError):
            raise
        raise HandoffError("PNG could not be decoded safely.") from exc

    data_url = None
    for quality in (80, 70, 60, 50, 40, 30, 20):
        encoded = BytesIO()
        canvas.save(encoded, format="JPEG", quality=quality, optimize=True)
        candidate = "data:image/jpeg;base64," + base64.b64encode(encoded.getvalue()).decode("ascii")
        if len(candidate) <= MAX_IMAGE_CHARS:
            data_url = candidate
            break
    if data_url is None:
        raise HandoffError("Image cannot fit within MakeVideo's per-shot size limit.")

    digest = proof["output"]["sha256"]
    fingerprint = proof["continuity_fingerprint"]
    continuity = (
        f"Source: MakeImage local PNG composite; original SHA-256 {digest}; "
        f"continuity {fingerprint}. File bytes matched receipt; not an "
        "authenticated producer, AI generation, rights grant, or publish approval."
    )
    project = {
        "schema": STORYBOARD_SCHEMA,
        "title": title.strip(), "format": aspect,
        "goal": "", "audience": "", "cta": "",
        "shots": [{
            "id": "makeimage-" + digest[:24],
            "title": "MakeImage scene", "duration": 4,
            "visual": "Imported MakeImage local composite. Review source and rights.",
            "caption": "", "narration": "",
            "continuity": continuity, "palette": "midnight",
            "imageData": data_url
        }],
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects files produced by the user or another run.
    with output.open("x", encoding="utf-8") as target:
        json.dump(project, target, indent=2, ensure_ascii=False)
        target.write("\n")
    return {"storyboard": str(output), "source_sha256": digest,
            "schema": STORYBOARD_SCHEMA, "publication_authorized": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path, help="Local MakeImage PNG")
    parser.add_argument("--receipt", required=True, type=Path, help="Matching MakeImage receipt JSON")
    parser.add_argument("--output", required=True, type=Path, help="New MakeVideo storyboard JSON")
    parser.add_argument("--title", default="MakeImage scene")
    parser.add_argument("--format", choices=sorted(FORMAT_SIZE), default="16:9")
    args = parser.parse_args()
    try:
        print(json.dumps(export_storyboard(args.image, args.receipt, args.output,
                                           title=args.title, aspect=args.format), indent=2))
        return 0
    except (HandoffError, FileNotFoundError, FileExistsError) as exc:
        print(f"MakeImage handoff blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
