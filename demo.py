#!/usr/bin/env python3
"""MakeImage local image-composition proof, with optional creator-owned reference.

Usage: python3 demo.py --title "A new world" --output out/keyframe.png
       python3 demo.py --reference my-photo.jpg --title "Scene 1" --output out/scene-1.png

Creates REAL PNG pixels and a provenance receipt; it is not a generative-AI
integration. No network, third-party generation, facial recognition or publish.
"""
from __future__ import annotations

import argparse
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


def render(output: Path, receipt: Path, *, title: str, subtitle: str, width: int, height: int, seed: int = 73, reference: Path | None = None) -> dict:
    if not 640 <= width <= 4096 or not 360 <= height <= 4096 or width*height > 10_000_000:
        raise ImageFlowError('Canvas must be 640–4096 wide, 360–4096 high, max 10 MP.')
    if len(title)>100 or len(subtitle)>180:
        raise ImageFlowError('Title/subtitle are too long for a legible image.')
    if not 0 <= seed <= 2**32-1:
        raise ImageFlowError('Seed must be between zero and 2^32-1.')
    output,receipt=output.expanduser().resolve(),receipt.expanduser().resolve()
    ref=reference.expanduser().resolve(strict=True) if reference else None
    if output==receipt or (ref and (output==ref or receipt==ref)):
        raise ImageFlowError('Output paths must not overwrite the original reference.')
    if output.suffix.lower()!='.png' or receipt.suffix.lower()!='.json':
        raise ImageFlowError('Output must be PNG; receipt must be JSON.')
    if output.exists() or receipt.exists():
        raise ImageFlowError('Existing outputs are protected. Choose new filenames.')
    base=source_image(ref,width,height) if ref else original_background(width,height,seed)
    overlay=Image.new('RGBA',(width,height),(0,0,0,0))
    d=ImageDraw.Draw(overlay,'RGBA')
    left=int(width*.065)
    d.rounded_rectangle((left,int(height*.665),int(width*.91),int(height*.90)),radius=22,fill=(8,8,29,175),outline=(165,107,253,100),width=2)
    d.text((left+int(width*.035),int(height*.69)),title or 'Untitled image',font=font(max(22,width//27)),fill=(248,240,255,255),stroke_width=0)
    if subtitle:
        d.text((left+int(width*.035),int(height*.79)),subtitle,font=font(max(16,width//52)),fill=(203,192,238,255))
    d.text((left,int(height*.068)), 'MAKEIMAGE / LOCAL COMPOSITE',font=font(max(13,width//80)),fill=(203,179,255,235))
    image=Image.alpha_composite(base.convert('RGBA'),overlay).convert('RGB')
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
    fingerprint=hashlib.sha256(json.dumps({"reference":ref_info,"title":title,"subtitle":subtitle,"seed":seed,"width":width,"height":height},sort_keys=True).encode()).hexdigest()
    proof={
        "schema":"makeimage/local-composite/v1","state":"VERIFIED_LOCAL_RENDER","generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "continuity_fingerprint":fingerprint,"continuity_cookie":{"parent":fingerprint[:16],"release_authority":False,"publish_authority":False},
        "reference":ref_info,"source_method":"local Pillow composition, not AI generation",
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
    args=parser.parse_args()
    try:
        result=render(args.output,args.receipt,title=args.title,subtitle=args.subtitle,width=args.width,height=args.height,seed=args.seed,reference=args.reference)
        print(json.dumps({"result":result['state'],"output":result['output'],"receipt":str(args.receipt)},indent=2))
        return 0
    except (ImageFlowError,FileNotFoundError) as e:
        print('MakeImage render blocked: '+str(e),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())