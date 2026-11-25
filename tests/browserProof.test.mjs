import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { receiptFromDecodedPng } from '../web/proof.js';

const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADUlEQVR4nGNgYGAAAAAEAAH2FzhVAAAAAElFTkSuQmCC', 'base64');
const rgba = new Uint8ClampedArray([0, 0, 0, 255]);
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
test('receipt binds supplied decoded pixels and encoded bytes without granting authority', async () => {
  const r = await receiptFromDecodedPng(png, rgba, 1, 1);
  assert.equal(r.output.sha256, digest(png));
  assert.equal(r.output.pixel_sha256, digest(Buffer.from([0,0,0])));
  assert.equal(r.output.bytes, png.length);
  assert.equal(r.state, 'UNVERIFIED_DECODE_INPUT');
  assert.equal(r.output.full_decode, false);
  assert.equal(r.continuity_cookie.publish_authority, false);
  assert.equal(r.output.ai_inference_verified, false);
});
test('invalid dimensions, pixels, PNG and source digests fail closed', async () => {
  await assert.rejects(receiptFromDecodedPng(png, rgba, 2, 1));
  await assert.rejects(receiptFromDecodedPng(png, new Uint8ClampedArray([0,0,0,0]), 1, 1));
  await assert.rejects(receiptFromDecodedPng(new Uint8Array(24), rgba, 1, 1));
  await assert.rejects(receiptFromDecodedPng(png, rgba, 1, 1, 'invalid'));
});
