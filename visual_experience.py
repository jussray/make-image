#!/usr/bin/env python3
"""Render source-labeled Juss & Co visual-experience manifests to inspected PNGs.

This is local image composition, NOT GitHub/API proof, AI generation, or publication.
The input manifest claims are user-supplied and never independently authenticated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

SCHEMA = "jussco/visual-experience/v1"
KINDS = {"architecture", "playtest", "canon"}
STATES = {"VERIFIED_SOURCE", "INFERRED", "UNKNOWN", "BLOCKED"}
COLORS = {"VERIFIED_SOURCE": "#76ecc0", "INFERRED": "#f8cd79", "UNKNOWN": "#aaaec9", "BLOCKED": "#ff9aab"}
DARK = "#08091f"


def digest(file: Path) -> str:
    h = hashlib.sha256()
    with file.open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate(raw: object) -> dict:
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        raise ValueError("Expected jussco/visual-experience/v1 manifest")
    kind = raw.get("kind")
    if kind not in KINDS:
        raise ValueError("Unsupported experience kind")
    title = raw.get("title")
    items = raw.get("items")
    if not isinstance(title, str) or not title.strip() or len(title) > 100:
        raise ValueError("Title must contain 1–100 characters")
    if not isinstance(items, list) or not 1 <= len(items) <= 12:
        raise ValueError("Items must contain 1–12 entries")
    ids = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Item must be an object")
        if not isinstance(item.get("id"), str) or not re.fullmatch(r"[a-z0-9_-]{1,30}", item["id"]):
            raise ValueError("Item ID must be short lowercase identifier")
        if item["id"] in ids:
            raise ValueError("Item IDs must be unique")
        ids.add(item["id"])
        for field, limit in (("title", 90), ("summary", 240)):
            if not isinstance(item.get(field), str) or not item[field].strip() or len(item[field]) > limit:
                raise ValueError(f"Every item needs a short {field}")
        if item.get("state") not in STATES:
            raise ValueError("Item evidence state must be explicit")
    edges = raw.get("edges", [])
    if not isinstance(edges, list) or len(edges) > 24:
        raise ValueError("Too many edges")
    for edge in edges:
        if not isinstance(edge, dict) or edge.get("from") not in ids or edge.get("to") not in ids:
            raise ValueError("Edge endpoints must refer to existing items")
        if not isinstance(edge.get("label", ""), str) or len(edge.get("label", "")) > 90:
            raise ValueError("Edge label too long")
    return raw


def face(size: int, bold: bool = False):
    path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    if Path(path).is_file():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def fit_text(draw, text, max_width, font_size, bold=False):
    for n in range(font_size, 11, -1):
        f = face(n, bold)
        if draw.textbbox((0, 0), text, font=f)[2] <= max_width:
            return f
    raise ValueError("Text cannot fit safely on the canvas; shorten the label")


def wrap(draw, text, font, max_width, max_lines=3):
    words = text.split()
    lines, current = [], ''
    for word in words:
        tryline = (current + ' ' + word).strip()
        if draw.textbbox((0, 0), tryline, font=font)[2] <= max_width:
            current = tryline
        else:
            if draw.textbbox((0, 0), word, font=font)[2] > max_width:
                raise ValueError("Item summary cannot fit its visual card; shorten the summary")
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        # Fail closed on long text, do not silently trim factual or brand claims.
        raise ValueError("Item summary cannot fit its visual card; shorten the summary")
    return lines


def render_manifest(manifest_path: Path, output: Path, receipt: Path, *, before: Path | None = None, after: Path | None = None) -> dict:
    manifest_path = manifest_path.expanduser().resolve(strict=True)
    if manifest_path.stat().st_size > 64 * 1024:
        raise ValueError("Manifest exceeds 64 KiB")
    raw = validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    output, receipt = output.expanduser().resolve(), receipt.expanduser().resolve()
    originals = {manifest_path}
    if raw["kind"] == "canon":
        if not before or not after:
            raise ValueError("Canon comparison requires explicit --before and --after screenshots")
        before, after = before.expanduser().resolve(strict=True), after.expanduser().resolve(strict=True)
        for img in (before, after):
            if img.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp'} or not 100 <= img.stat().st_size <= 16*1024*1024:
                raise ValueError("Screenshot must be local PNG/JPEG/WebP within 16 MiB")
            with Image.open(img) as src:
                if src.width*src.height > 24_000_000:
                    raise ValueError("Screenshot exceeds 24 megapixels")
                src.verify()
        if before == after:
            raise ValueError("Canon comparison requires two distinct source screenshots")
        originals |= {before, after}
    if output.suffix.lower() != '.png' or receipt.suffix.lower() != '.json' or len({output, receipt, *originals}) < len(originals)+2:
        raise ValueError("PNG and receipt JSON paths must be distinct and not overwrite sources")
    if output.exists() or receipt.exists():
        raise ValueError("Existing output or receipt protected against overwrite")
    W = 1440
    item_count = len(raw['items'])
    if raw['kind'] == 'canon':
        H = 910
    else:
        H = max(900, 330 + ((item_count+1)//2)*188 + 125)
    if W * H > 10_000_000:
        raise ValueError("Visual experience exceeds canvas pixel limit")
    img = Image.new('RGB', (W,H), DARK)
    d = ImageDraw.Draw(img)
    for i in range(H):
        p = i / max(H,1)
        d.line((0,i,W,i), fill=(10+int(8*p), 8+int(7*p), 29+int(22*p)))
    d.rounded_rectangle((36,34,W-36,H-42),28,fill='#141430',outline='#514278',width=2)
    d.text((78,68),'JUSS & CO.  /  MAKEIMAGE',font=face(18,True),fill='#F5C778')
    d.text((78,119), raw['title'],font=fit_text(d,raw['title'],W-160,47,True), fill='#F7F2FF')
    d.text((78,185), f"{raw['kind'].upper()}  ·  {len(raw['items'])} SOURCE-LABELED ITEMS",font=face(19),fill='#A7ADDD')
    d.line((78,239,W-78,239), fill='#4A4468',width=2)
    if raw['kind'] == 'canon':
        for path, left, caption in [(before,78,'BEFORE / SUPPLIED SCREENSHOT'),(after,738,'AFTER / SUPPLIED SCREENSHOT')]:
            with Image.open(path) as src:
                frame = ImageOps.contain(ImageOps.exif_transpose(src).convert('RGB'),(620,480))
            x = left+(620-frame.width)//2
            y = 286+(480-frame.height)//2
            img.paste(frame,(x,y))
            d.rectangle((left-1,285,left+621,766),outline='#7865AC',width=2)
            d.text((left,785),caption,font=face(17,True),fill='#F3E8FF')
    else:
        box_w = 620
        positions = {}
        for index,item in enumerate(raw['items']):
            col,row = index%2,index//2
            x,y = 78+col*660,278+row*188
            positions[item['id']] = (x+box_w//2,y+76)
            d.rounded_rectangle((x,y,x+box_w,y+164),radius=18,fill='#222349',outline='#5A5289',width=2)
            state = item['state']
            d.ellipse((x+21,y+23,x+38,y+40),fill=COLORS[state])
            label = item['title']
            d.text((x+54,y+15),label,font=fit_text(d,label,box_w-90,26,True),fill='#FFF6FF')
            d.text((x+23,y+63),state.replace('_',' '),font=face(14,True),fill=COLORS[state])
            lines=wrap(d,item['summary'],face(16),box_w-50,3)
            for k,line in enumerate(lines):
                d.text((x+23,y+98+22*k),line,font=face(16),fill='#CBD1ED')
        # Connectors are intentionally summarized separately; edges are declared relationships, not runtime proof.
        if raw['edges']:
            edges_text=f"{len(raw['edges'])} DECLARED EDGES  •  NOT VERIFIED RUNTIME CONNECTIONS"
            d.text((78,H-105),edges_text,font=face(18,True),fill='#C4A6FF')
    note='SOURCE LABELS FROM SUPPLIED MANIFEST · NO LIVE GITHUB OR PLAYBACK VERIFICATION · NO RELEASE AUTHORITY'
    d.text((78,H-73),note,font=fit_text(d,note,W-160,15),fill='#F4C97C')
    output.parent.mkdir(parents=True,exist_ok=True)
    receipt.parent.mkdir(parents=True,exist_ok=True)
    try:
        img.save(output, format='PNG', optimize=True)
        with Image.open(output) as check:
            check.verify()
        with Image.open(output) as check:
            if check.format!='PNG' or check.size!=(W,H):
                raise ValueError('Output verification failed')
        result = {
        'schema': 'makeimage/visual-experience-receipt/v1',
        'state': 'VERIFIED_LOCAL_RENDER',
        'kind': raw['kind'],
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'input': {'manifest_sha256': digest(manifest_path), 'before_sha256': digest(before) if before else None, 'after_sha256': digest(after) if after else None},
        'output': {'sha256': digest(output), 'path': str(output), 'width': W, 'height': H, 'format': 'PNG'},
        'claims': {'github_verified': False, 'runtime_verified': False, 'publish_approved': False},
        'limitations': ['Supplied manifest source states have not been independently authenticated', 'Static PNG cannot reproduce interactive behavior', 'Source screenshots and rights require independent review'],
    }
        receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    except Exception:
        # Neither an invalid image nor an unreceipted image may remain as a claimed proof.
        output.unlink(missing_ok=True)
        receipt.unlink(missing_ok=True)
        raise
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--before',type=Path)
    p.add_argument('--after',type=Path)
    args=p.parse_args()
    try:
        result=render_manifest(args.manifest,args.output,args.receipt,before=args.before,after=args.after)
        print(json.dumps({'state':result['state'],'output':result['output'],'receipt':str(args.receipt)},indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        p.exit(2,f'Visual experience blocked: {exc}\n')

if __name__ == '__main__':
    raise SystemExit(main())