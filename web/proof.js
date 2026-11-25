// Local byte/pixel integrity only. A receipt is not a signed rights or release grant.
const MAX_BYTES = 8 * 1024 * 1024;
const SHA = /^[a-f0-9]{64}$/;
export async function sha256Hex(bytes) {
  if (!globalThis.crypto?.subtle) throw new Error('Secure browser crypto is required.');
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2, '0')).join('');
}
export async function receiptFromDecodedPng(bytes, rgba, width, height, referenceSha256 = null) {
  if (!(bytes instanceof Uint8Array) || bytes.length < 24 || bytes.length > MAX_BYTES ||
      ![137,80,78,71,13,10,26,10].every((v,i) => bytes[i] === v) ||
      String.fromCharCode(...bytes.subarray(12,16)) !== 'IHDR') throw new Error('Invalid bounded PNG.');
  const header = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (!Number.isSafeInteger(width) || !Number.isSafeInteger(height) || width < 1 || height < 1 ||
      width > 8192 || height > 8192 || width * height > 20_000_000 ||
      header.getUint32(16) !== width || header.getUint32(20) !== height ||
      !(rgba instanceof Uint8ClampedArray) || rgba.length !== width * height * 4 ||
      (referenceSha256 !== null && (typeof referenceSha256 !== 'string' || !SHA.test(referenceSha256)))) throw new Error('Invalid image evidence.');
  const rgb = new Uint8Array(width * height * 3);
  for (let i = 0, j = 0; i < rgba.length; i += 4, j += 3) {
    if (rgba[i + 3] !== 255) throw new Error('Composite must be opaque.');
    rgb.set(rgba.subarray(i,i+3),j);
  }
  const [sha256,pixel_sha256] = await Promise.all([sha256Hex(bytes),sha256Hex(rgb)]);
  const continuity_fingerprint = await sha256Hex(new TextEncoder().encode(JSON.stringify({method:'browser-canvas-v1',sha256,pixel_sha256,width,height,referenceSha256})));
  return {schema:'makeimage/local-composite/v1',state:'UNVERIFIED_DECODE_INPUT',generated_at_utc:new Date().toISOString(),source_method:'local Canvas 2D composite, not AI inference',reference:referenceSha256?{sha256:referenceSha256}:null,continuity_fingerprint,continuity_cookie:{parent:continuity_fingerprint.slice(0,16),release_authority:false,publish_authority:false},output:{format:'PNG',width,height,bytes:bytes.length,sha256,pixel_sha256,full_decode:false,ai_inference_verified:false},limitations:['Local integrity receipt, not an authenticated producer or rights grant.','No AI inference, upload or publication.']};
}
export async function createCompositeReceipt(blob, width, height, referenceSha256 = null, doc = document) {
  if (!(blob instanceof Blob) || blob.type !== 'image/png' || blob.size < 24 || blob.size > MAX_BYTES) throw new Error('Invalid PNG export size.');
  if (!Number.isSafeInteger(width) || !Number.isSafeInteger(height) || width < 1 || height < 1 || width > 8192 || height > 8192 || width * height > 20_000_000) throw new Error('Invalid expected dimensions.');
  const bytes = new Uint8Array(await blob.arrayBuffer());
  const bitmap = await createImageBitmap(blob, {colorSpaceConversion:'none',premultiplyAlpha:'none'});
  try {
    if (bitmap.width !== width || bitmap.height !== height) throw new Error('Decoded PNG dimensions differ.');
    const canvas = doc.createElement('canvas'); canvas.width = width; canvas.height = height;
    const ctx = canvas.getContext('2d', {willReadFrequently:true});
    if (!ctx) throw new Error('Canvas decode unavailable.');
    ctx.drawImage(bitmap,0,0);
    const receipt = await receiptFromDecodedPng(bytes,ctx.getImageData(0,0,width,height).data,width,height,referenceSha256);
    receipt.output.full_decode = true;
    receipt.state = 'VERIFIED_LOCAL_RENDER';
    return receipt;
  } finally { bitmap.close(); }
}
