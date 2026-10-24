// MakeImage local-only browser compositor. No network endpoints or uploads.
export const FORMATS = Object.freeze({
  '16:9': [1280, 720],
  '9:16': [720, 1280],
  '1:1': [960, 960]
});
export const MAX_FILE_SIZE = 8 * 1024 * 1024;
export const MAX_PIXELS = 20_000_000;
const ALLOWED_TYPES = new Set(['image/png', 'image/jpeg', 'image/webp']);

export function validateReference(file) {
  if (!file || !ALLOWED_TYPES.has(file.type)) {
    throw new Error('Choose a PNG, JPEG or WebP image.');
  }
  if (!Number.isFinite(file.size) || file.size <= 0 || file.size > MAX_FILE_SIZE) {
    throw new Error('Reference must be between 1 byte and 8 MB.');
  }
}

export function validateDimensions(width, height) {
  if (!Number.isSafeInteger(width) || !Number.isSafeInteger(height) ||
      width <= 0 || height <= 0 || width > 8192 || height > 8192 ||
      width * height > MAX_PIXELS) {
    throw new Error('Reference exceeds the 20 MP / 8192 px safety limit.');
  }
}

export function canvasSize(format) {
  if (!Object.hasOwn(FORMATS, format)) {
    throw new Error('Unsupported canvas format.');
  }
  return [...FORMATS[format]];
}

export function safeText(value, max) {
  const text = String(value ?? '').trim().replace(/\s+/g, ' ');
  if (text.length > max) throw new Error('Text is too long for this canvas.');
  return text;
}

function fitText(ctx, text, maxWidth, initial, minimum) {
  let fontSize = initial;
  do {
    ctx.font = '700 ' + fontSize + 'px system-ui, sans-serif';
    if (ctx.measureText(text).width <= maxWidth) return fontSize;
    fontSize -= 2;
  } while (fontSize >= minimum);
  throw new Error('Headline cannot fit this canvas. Shorten the text.');
}

function drawBackdrop(ctx, width, height, seed = 73) {
  const gradient = ctx.createLinearGradient(0, 0, width, height);
  gradient.addColorStop(0, '#0c0927');
  gradient.addColorStop(0.57, '#422778');
  gradient.addColorStop(1, '#09091e');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);
  const scale = Math.min(width, height);
  for (let i = 0; i < 6; i++) {
    const x = width * (0.13 + 0.14 * i);
    const y = height * (0.28 + 0.07 * Math.sin(i * 1.4));
    const glow = ctx.createRadialGradient(x, y, 0, x, y, scale * 0.34);
    glow.addColorStop(0, 'rgba(153,91,255,.31)');
    glow.addColorStop(1, 'rgba(153,91,255,0)');
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, width, height);
  }
  let v = seed;
  for (let i = 0; i < 54; i++) {
    v = (Math.imul(v, 1664525) + 1013904223) >>> 0;
    const x = (v / 4294967296) * width;
    v = (Math.imul(v, 1664525) + 1013904223) >>> 0;
    const y = (v / 4294967296) * height;
    ctx.fillStyle = 'rgba(240,222,255,.44)';
    ctx.beginPath();
    ctx.arc(x, y, Math.max(0.7, scale / 900), 0, Math.PI * 2);
    ctx.fill();
  }
}

export function paint(ctx, width, height, title, subtitle, reference = null) {
  validateDimensions(width, height);
  const heading = safeText(title || 'Untitled image', 100);
  const supporting = safeText(subtitle, 180);
  const horizontal = width < height ? 0.08 : 0.07;
  const left = width * horizontal;
  const maximum = width * (1 - 2 * horizontal);
  const base = Math.min(width, height);
  ctx.clearRect(0, 0, width, height);
  drawBackdrop(ctx, width, height);
  if (reference) {
    validateDimensions(reference.naturalWidth, reference.naturalHeight);
    const iw = reference.naturalWidth, ih = reference.naturalHeight;
    const scale = Math.max(width / iw, height / ih);
    ctx.drawImage(reference, (iw - width / scale) / 2, (ih - height / scale) / 2,
                  width / scale, height / scale, 0, 0, width, height);
  }
  const boxHeight = height * 0.31;
  const boxTop = height - boxHeight - height * 0.045;
  ctx.fillStyle = 'rgba(12,8,31,.83)';
  ctx.fillRect(left * .60, boxTop, width - left * 1.2, boxHeight);
  ctx.fillStyle = '#a77dff';
  ctx.fillRect(left * .60, boxTop, Math.max(3, width / 300), boxHeight);
  const titleSize = fitText(ctx, heading, maximum, Math.round(base * 0.068),
                            Math.max(15, Math.floor(base * 0.025)));
  ctx.fillStyle = '#fffaff';
  ctx.font = '700 ' + titleSize + 'px system-ui, sans-serif';
  ctx.fillText(heading, left, boxTop + boxHeight * .41);
  if (supporting) {
    const subtitleSize = fitText(ctx, supporting, maximum, Math.round(base * .032),
                                 Math.max(12, Math.floor(base * .019)));
    ctx.fillStyle = '#d6c7ff';
    ctx.font = '500 ' + subtitleSize + 'px system-ui, sans-serif';
    ctx.fillText(supporting, left, boxTop + boxHeight * .72);
  }
  ctx.fillStyle = 'rgba(244,234,255,.85)';
  ctx.font = '600 ' + Math.max(12, Math.round(base * .018)) + 'px system-ui, sans-serif';
  ctx.fillText('MAKEIMAGE  /  JUSS & CO.', left, height * .08);
}

async function decodeReference(file) {
  const url = URL.createObjectURL(file);
  const image = new Image();
  try {
    image.src = url;
    await image.decode();
    validateDimensions(image.naturalWidth, image.naturalHeight);
    return image;
  } catch (error) {
    if (error instanceof Error && /safety limit/.test(error.message)) throw error;
    throw new Error('Reference image cannot be safely decoded.');
  } finally {
    URL.revokeObjectURL(url);
  }
}

export function mountStudio(doc) {
  const el = id => doc.getElementById(id);
  const canvas = el('canvas');
  const ctx = canvas.getContext('2d');
  const status = el('status');
  const source = el('source');
  let reference = null;
  let importOrdinal = 0;
  if (!ctx) {
    status.textContent = 'This browser cannot create a 2D canvas.';
    el('download').disabled = true;
    return;
  }
  const setStatus = message => { status.textContent = message; };
  const refresh = () => {
    const [width, height] = canvasSize(el('format').value);
    const title = safeText(el('title').value, 100);
    const subtitle = safeText(el('subtitle').value, 180);
    // Compose to a separate canvas. Invalid text must not damage the last
    // preview or produce an incomplete export.
    const pending = doc.createElement('canvas');
    pending.width = width;
    pending.height = height;
    paint(pending.getContext('2d'), width, height, title, subtitle, reference);
    canvas.width = width;
    canvas.height = height;
    ctx.drawImage(pending, 0, 0);
    setStatus('Ready: ' + width + '×' + height + ' PNG. No files uploaded.');
  };
  source.addEventListener('change', async () => {
    const file = source.files?.[0];
    const ordinal = ++importOrdinal;
    if (!file) {
      reference = null;
      try { refresh(); } catch (error) { setStatus(error.message); }
      return;
    }
    try {
      validateReference(file);
      const next = await decodeReference(file);
      if (ordinal !== importOrdinal) return;
      reference = next;
      refresh();
    } catch (error) {
      if (ordinal === importOrdinal) setStatus('Reference rejected: ' + error.message);
    }
  });
  const tryRefresh = () => {
    try { refresh(); } catch (error) { setStatus('Preview blocked: ' + error.message); }
  };
  el('render').addEventListener('click', tryRefresh);
  for (const key of ['title', 'subtitle', 'format']) el(key).addEventListener('change', tryRefresh);
  el('download').addEventListener('click', () => {
    try {
      refresh();
      canvas.toBlob(blob => {
        if (!blob) {
          setStatus('PNG could not be encoded on this device.');
          return;
        }
        const url = URL.createObjectURL(blob);
        const anchor = doc.createElement('a');
        anchor.href = url;
        anchor.download = 'jussco-makeimage.png';
        doc.body.append(anchor);
        anchor.click();
        anchor.remove();
        setTimeout(() => URL.revokeObjectURL(url), 30000);
        setStatus('PNG saved locally. Review artwork and usage rights before sharing.');
      }, 'image/png');
    } catch (error) {
      setStatus('Save blocked: ' + error.message);
    }
  });
  tryRefresh();
}

if (typeof document !== 'undefined') {
  mountStudio(document);
}
