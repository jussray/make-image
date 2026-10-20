#!/usr/bin/env python3
"""MakeImage local image-composition proof, with optional creator-owned reference.

Usage: python3 demo.py --title "A new world" --output out/keyframe.png
       python3 demo.py --reference my-photo.jpg --title "Scene 1" --output out/scene-1.png

Creates REAL PNG pixels and a provenance receipt; it is not a generative-AI
integration. No network, third-party generation, facial recognition or publish.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import io
import re
import hashlib
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, UnidentifiedImageError

MAX_SOURCE_BYTES = 16 * 1024 * 1024
MAX_SOURCE_PIXELS = 24_000_000
SUPPORTED = {'.png', '.jpg', '.jpeg', '.webp'}
BRAND_DESTINATION = 'https://www.jussco.company/'
BRAND_QR_PATH = Path(__file__).resolve().parent / 'assets/qr/jussco-company.svg'
MAX_STORYBOARD_BYTES = 3_200_000


class ImageFlowError(ValueError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def font(size: int) -> ImageFont.ImageFont:
    for family in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        if Path(family).exists():
            return ImageFont.truetype(family, size)
    return ImageFont.load_default()


def source_image(reference: Path, width: int, height: int) -> Image.Image:
    if reference.suffix.lower() not in SUPPORTED or not reference.is_file():
        raise ImageFlowError('Reference must be a local PNG, JPEG, or WebP image.')
    if reference.stat().st_size < 100 or reference.stat().st_size > MAX_SOURCE_BYTES:
        raise ImageFlowError('Reference image must be nonempty and at most 16 MiB.')
    try:
        with Image.open(reference) as source:
            if source.width * source.height > MAX_SOURCE_PIXELS:
                raise ImageFlowError('Reference image exceeds the pixel safety limit.')
            source.verify()
        with Image.open(reference) as source:
            return ImageOps.fit(ImageOps.exif_transpose(source).convert('RGB'), (width, height), method=Image.Resampling.LANCZOS)
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise ImageFlowError('Reference image could not be decoded safely.') from error


def load_brand_qr() -> tuple[Image.Image, str]:
    # The checked-in first-party SVG contains one deterministic 41x41 QR matrix.
    # Parse only its pixel-run path; never render arbitrary SVG or fetch a URL.
    try:
        raw = BRAND_QR_PATH.read_bytes()
        xml = raw.decode('utf-8')
    except (OSError, UnicodeDecodeError) as error:
        raise ImageFlowError('Local first-party QR asset is unavailable.') from error
    if 'viewBox="0 0 41 41"' not in xml or '<script' in xml or '<image' in xml:
        raise ImageFlowError('Unexpected first-party QR asset format.')
    modules = [(int(x), int(y)) for x, y in re.findall(r'M(\d+) (\d+)h1v1h-1z', xml)]
    if len(modules) < 180 or any(not (4 <= x < 37 and 4 <= y < 37) for x, y in modules):
        raise ImageFlowError('QR matrix failed structural verification.')
    out = Image.new('RGB', (41, 41), 'white')
    draw = ImageDraw.Draw(out)
    for x, y in modules:
        draw.point((x, y), fill=(16, 11, 40))
    return out, hashlib.sha256(raw).hexdigest()


def storyboard_frame(storyboard: Path, shot_index: int) -> tuple[dict, Image.Image | None]:
    # Import exactly MakeVideo's v1 portable storyboard; never contact a server.
    try:
        source = storyboard.expanduser().resolve(strict=True)
        if not 1 <= source.stat().st_size <= MAX_STORYBOARD_BYTES:
            raise ImageFlowError('Storyboard exceeds the 3.2 MB input limit.')
        data = json.loads(source.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ImageFlowError('Storyboard JSON could not be read safely.') from error
    if not isinstance(data, dict) or data.get('schema') != 'makevideo/storyboard/v1':
        raise ImageFlowError('Only MakeVideo storyboard v1 JSON can be imported.')
    shots = data.get('shots')
    if not isinstance(shots, list) or not 1 <= len(shots) <= 24 or not 1 <= shot_index <= len(shots):
        raise ImageFlowError('Storyboard has an invalid shot count or shot index.')
    shot = shots[shot_index - 1]
    if not isinstance(shot, dict):
        raise ImageFlowError('Selected storyboard shot is invalid.')
    encoded = shot.get('imageData') or ''
    embedded = None
    image_digest = None
    if encoded:
        if not isinstance(encoded, str) or len(encoded) > 105_000 or not re.fullmatch(r'data:image/jpeg;base64,[A-Za-z0-9+/]+=*', encoded):
            raise ImageFlowError('Storyboard embedded shot image is not a bounded JPEG.')
        try:
            payload = base64.b64decode(encoded.partition(',')[2], validate=True)
            if len(payload) > 100_000:
                raise ImageFlowError('Storyboard shot image exceeds the size limit.')
            with Image.open(io.BytesIO(payload)) as image:
                if image.format != 'JPEG' or image.width * image.height > MAX_SOURCE_PIXELS:
                    raise ImageFlowError('Storyboard shot image is not a safe JPEG.')
                embedded = ImageOps.exif_transpose(image).convert('RGB')
            image_digest = hashlib.sha256(payload).hexdigest()
        except (UnidentifiedImageError, OSError, ValueError, binascii.Error) as error:
            raise ImageFlowError('Storyboard embedded JPEG could not be decoded.') from error
    title = str(shot.get('caption') or shot.get('title') or 'Untitled shot')[:100]
    project_title = str(data.get('title') or 'MakeVideo storyboard')[:180]
    metadata = {'path': str(source), 'sha256': sha256(source), 'shot_index': shot_index,
                'source_schema': 'makevideo/storyboard/v1', 'title': title,
                'subtitle': project_title, 'embedded_image_sha256': image_digest}
    return metadata, embedded


def original_background(width: int, height: int, seed: int) -> Image.Image:
    # An original deterministic visual, not synthetic footage or a claimed model output.
    rng = random.Random(seed)
    rows = []
    for y in range(height):
        p=y / max(height-1,1)
        rows.extend([(int(12+15*p), int(11+7*p), int(37+38*p))] * width)
    img=Image.new('RGB', (width,height))
    img.putdata(rows)
    aurora=Image.new('RGBA', (width,height), (0,0,0,0))
    d=ImageDraw.Draw(aurora, 'RGBA')
    for i in range(18):
        x=int(width * (.14 + .68 * i/18))
        y=int(height * (.24 + .15*math.sin(i*.46)))
        radius=int(width*(.13+.07*rng.random()))
        c=(104+int(rng.random()*70),49,230,34)
        d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=c)
    aurora=aurora.filter(ImageFilter.GaussianBlur(max(4,width//38)))
    img=Image.alpha_composite(img.convert('RGBA'), aurora)
    d=ImageDraw.Draw(img, 'RGBA')
    for i in range(13):
        xx=width*(i/13)
        yy=height*(.45+.12*math.sin(i*.41))
        d.arc((xx-width*.36,yy-height*.42,xx+width*.47,yy+height*.4),15,170,fill=(167,108,255,38),width=max(1,width//320))
    for i in range(min(150, (width*height)//4000)):
        x=rng.randrange(width)
        y=rng.randrange(height)
        r=rng.choice((1,1,2))
        d.ellipse((x-r,y-r,x+r,y+r),fill=(220,203,255,rng.randrange(50,140)))
    return img.convert('RGB')


def render(output: Path, receipt: Path, *, title: str, subtitle: str, width: int, height: int, seed: int = 73, reference: Path | None = None, watermark: bool = False, qr: bool = False, storyboard: dict | None = None, embedded_image: Image.Image | None = None) -> dict:
    if not 640 <= width <= 4096 or not 360 <= height <= 4096 or width*height > 10_000_000:
        raise ImageFlowError('Canvas must be 640–4096 wide, 360–4096 high, max 10 MP.')
    if len(title)>100 or len(subtitle)>180:
        raise ImageFlowError('Title/subtitle are too long for a legible image.')
    if not 0 <= seed <= 2**32-1:
        raise ImageFlowError('Seed must be between zero and 2^32-1.')
    output,receipt=output.expanduser().resolve(),receipt.expanduser().resolve()
    ref=reference.expanduser().resolve(strict=True) if reference else None
    if reference and embedded_image is not None:
        raise ImageFlowError('Choose one visual reference source, not two.')
    if storyboard and (output == Path(storyboard['path']) or receipt == Path(storyboard['path'])):
        raise ImageFlowError('Source storyboard must never be overwritten.')
    if output==receipt or (ref and (output==ref or receipt==ref)):
        raise ImageFlowError('Output paths must not overwrite the original reference.')
    if output.suffix.lower()!='.png' or receipt.suffix.lower()!='.json':
        raise ImageFlowError('Output must be PNG; receipt must be JSON.')
    if output.exists() or receipt.exists():
        raise ImageFlowError('Existing outputs are protected. Choose new filenames.')
    qr_pixels, qr_sha = load_brand_qr() if qr else (None, None)
    base = (source_image(ref, width, height) if ref else
            ImageOps.fit(embedded_image, (width, height), method=Image.Resampling.LANCZOS)
            if embedded_image is not None else original_background(width, height, seed))
    overlay=Image.new('RGBA',(width,height),(0,0,0,0))
    d=ImageDraw.Draw(overlay,'RGBA')
    left=int(width*.065)
    d.rounded_rectangle((left,int(height*.665),int(width*.91),int(height*.90)),radius=22,fill=(8,8,29,175),outline=(165,107,253,100),width=2)
    title_text = title or 'Untitled image'
    available_width = int(width * .91) - left - int(width * .075)
    def fitted_font(text, initial):
        # Never silently clip a factual or brand claim.
        for px in range(initial, 13, -1):
            candidate = font(px)
            if d.textbbox((0, 0), text, font=candidate)[2] <= available_width:
                return candidate
        raise ImageFlowError('Text cannot fit safely on the canvas; shorten the title or subtitle.')
    title_font = fitted_font(title_text, max(22, width//27))
    subtitle_font = fitted_font(subtitle, max(16, width//52)) if subtitle else None
    d.text((left+int(width*.035),int(height*.69)),title_text,font=title_font,fill=(248,240,255,255),stroke_width=0)
    if subtitle:
        d.text((left+int(width*.035),int(height*.79)),subtitle,font=subtitle_font,fill=(203,192,238,255))
    d.text((left,int(height*.068)), 'MAKEIMAGE / LOCAL COMPOSITE',font=font(max(13,width//80)),fill=(203,179,255,235))
    if watermark:
        mark = 'JUSS & CO.'
        mark_font = font(max(14, width // 75))
        mark_x, mark_y = left, int(height * .945)
        box = d.textbbox((mark_x, mark_y), mark, font=mark_font)
        d.rounded_rectangle((box[0]-8, box[1]-5, box[2]+8, box[3]+6), radius=5, fill=(8, 8, 29, 220))
        d.text((mark_x, mark_y), mark, font=mark_font, fill=(250, 245, 255, 255))
    image=Image.alpha_composite(base.convert('RGBA'),overlay).convert('RGB')
    if qr_pixels is not None:
        # Preserve 4-cell white quiet zone from approved company QR data.
        # At least 136 output pixels yields >3 physical pixels per QR cell.
        side = max(136, min(width // 5, height // 3))
        side = min(side, width - 2*left, int(height * .57))
        if side < 123:
            raise ImageFlowError('Canvas is too small for a readable company QR.')
        resized = qr_pixels.resize((side, side), resample=Image.Resampling.NEAREST)
        image.paste(resized, (width - side - left, int(height * .055)))
    output.parent.mkdir(parents=True,exist_ok=True)
    receipt.parent.mkdir(parents=True,exist_ok=True)
    image.save(output,format='PNG',optimize=True)
    with Image.open(output) as check:
        check.verify()
    with Image.open(output) as check:
        if check.format!='PNG' or check.size!=(width,height):
            output.unlink(missing_ok=True)
            raise ImageFlowError('Pixel verification failed.')
    ref_info={"path":str(ref),"sha256":sha256(ref)} if ref else None
    branding = {"watermark": bool(watermark), "qr": bool(qr),
                "destination": BRAND_DESTINATION if qr else None,
                "qr_asset_sha256": qr_sha}
    source_storyboard = {k: v for k, v in storyboard.items() if k != 'title' and k != 'subtitle'} if storyboard else None
    fingerprint=hashlib.sha256(json.dumps({"reference":ref_info,"storyboard":source_storyboard,"branding":branding,"title":title,"subtitle":subtitle,"seed":seed,"width":width,"height":height},sort_keys=True).encode()).hexdigest()
    proof={
        "schema":"makeimage/local-composite/v1","state":"VERIFIED_LOCAL_RENDER","generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "continuity_fingerprint":fingerprint,"continuity_cookie":{"parent":fingerprint[:16],"release_authority":False,"publish_authority":False},
        "reference":ref_info,"storyboard":source_storyboard,"branding":branding,
        "source_method":"local Pillow composition, not AI generation",
        "output":{"path":str(output),"sha256":sha256(output),"width":width,"height":height,"format":"PNG"},
        "limitations":["Does not invoke an external image-generation model","No identity/rights checks for user-supplied reference","No publishing or external upload"],
    }
    receipt.write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return proof


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,help='Optional local creator-owned photo/art used as visual source')
    parser.add_argument('--title',default='From idea to image')
    parser.add_argument('--subtitle',default='A traceable, locally rendered creative keyframe')
    parser.add_argument('--output',type=Path,default=Path('out/makeimage-demo.png'))
    parser.add_argument('--receipt',type=Path,default=Path('out/makeimage-demo.receipt.json'))
    parser.add_argument('--width',type=int,default=1280)
    parser.add_argument('--height',type=int,default=720)
    parser.add_argument('--seed',type=int,default=73)
    parser.add_argument('--brand-watermark',action='store_true',help='Overlay Juss & Co. mark on exported PNG')
    parser.add_argument('--brand-qr',action='store_true',help='Overlay first-party QR for https://www.jussco.company/')
    parser.add_argument('--storyboard-json',type=Path,help='Optional MakeVideo v1 JSON, for a source-backed shot keyframe')
    parser.add_argument('--shot-index',type=int,default=1,help='One-based shot index in --storyboard-json')
    args=parser.parse_args()
    try:
        if args.storyboard_json and args.reference:
            raise ImageFlowError('Choose either a storyboard shot or a local reference image.')
        if not args.storyboard_json and args.shot_index != 1:
            raise ImageFlowError('--shot-index requires --storyboard-json.')
        storyboard, embedded = storyboard_frame(args.storyboard_json, args.shot_index) if args.storyboard_json else (None, None)
        output_width, output_height = args.width, args.height
        if storyboard and (args.width, args.height) == (1280, 720):
            # MakeVideo's default storyboard format can differ from image CLI default.
            raw = json.loads(Path(storyboard['path']).read_text(encoding='utf-8'))
            output_width, output_height = {'9:16': (720, 1280), '1:1': (1024, 1024)}.get(raw.get('format'), (1280, 720))
        result=render(args.output,args.receipt,title=storyboard['title'] if storyboard else args.title,
                      subtitle=storyboard['subtitle'] if storyboard else args.subtitle,
                      width=output_width,height=output_height,seed=args.seed,reference=args.reference,
                      watermark=args.brand_watermark,qr=args.brand_qr,
                      storyboard=storyboard,embedded_image=embedded)
        print(json.dumps({"result":result['state'],"output":result['output'],"receipt":str(args.receipt)},indent=2))
        return 0
    except (ImageFlowError,FileNotFoundError) as e:
        print('MakeImage render blocked: '+str(e),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())