"""Local image composition and evidence flow; not an AI generation claim."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return 'sha256:' + h.hexdigest()

def font(size):
    for candidate in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                      '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()

def render(output, *, source=None, licensed_source=False, title='MAKEIMAGE',
           subtitle='Original composition | Juss & Co.', width=1280, height=720):
    if width < 320 or height < 240 or width > 4096 or height > 4096:
        raise ValueError('Unsupported output dimensions')
    if not title.strip() or len(title) > 80 or len(subtitle) > 180:
        raise ValueError('Title or subtitle invalid')
    output = Path(output)
    if source is not None:
        source = Path(source)
        if not source.is_file():
            raise FileNotFoundError(source)
        if not licensed_source:
            raise PermissionError('Source usage requires explicit rights confirmation')
    output.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new('RGB', (width, height))
    pixels = im.load()
    for y in range(height):
        for x in range(width):
            glow = max(0, 1 - ((x-width*.77)**2/(width*.72)**2 + (y-height*.29)**2/(height*.88)**2))
            pixels[x, y] = (int(12+40*glow), int(10+16*glow), int(26+94*glow))
    if source:
        with Image.open(source) as src:
            src = ImageOps.exif_transpose(src).convert('RGB')
            fitted = ImageOps.fit(src, (int(width*.48), int(height*.64)), method=Image.Resampling.LANCZOS)
        pos = (int(width*.48), int(height*.15))
        im.paste(fitted, pos)
    else:
        halo = Image.new('RGBA', (width, height))
        painter = ImageDraw.Draw(halo)
        painter.ellipse((int(width*.57), int(height*.13), int(width*.88), int(height*.69)),
                        fill=(149, 86, 255, 230))
        halo = halo.filter(ImageFilter.GaussianBlur(radius=55))
        im = Image.alpha_composite(im.convert('RGBA'), halo).convert('RGB')
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((int(width*.065), int(height*.11), int(width*.46), int(height*.86)),
                         radius=25, fill=(12, 11, 31), outline=(91, 68, 157), width=3)
    dr.text((int(width*.105), int(height*.25)), title, font=font(max(20, int(width*.037))),
            fill=(245, 238, 255), stroke_width=0)
    dr.text((int(width*.105), int(height*.48)), subtitle[:75], font=font(max(12, int(width*.017))), fill=(199, 189, 232))
    dr.text((int(width*.105), int(height*.71)), 'ILLUSTRATIVE COMPOSITION',
            font=font(max(11, int(width*.013))), fill=(166, 154, 226))
    im.save(output, format='PNG', optimize=True)
    with Image.open(output) as check:
        check.verify()
    receipt = {'status':'RENDERED_NOT_APPROVED', 'created_at':datetime.now(timezone.utc).isoformat(),
               'file':output.name, 'sha256':digest(output),'width':width,'height':height,
               'truth_class':'ILLUSTRATIVE', 'source_sha256':digest(source) if source else None,
               'source_rights_confirmed_by_user':bool(source and licensed_source),
               'render_engine':'local/Pillow-composition', 'not_ai_generated':True,
               'identity_verified':False, 'authority_granted':False}
    receipt_path = output.with_suffix('.receipt.json')
    receipt_path.write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf8')
    return output, receipt_path
