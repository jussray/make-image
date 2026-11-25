---
name: cinematic-image-to-code
description: "Implement approved original cinematic imagery into the existing Juss & Co image, video and game pipeline; render, compare, correct and verify with source-linked receipts."
---

# Cinematic image-to-code: source → implementation → proof

Use for /image2code, /makeskill, visual-to-production, new graphic assets, screenshot parity or cinematic game/video upgrades. This skill routes into THIS repository's existing production modules; **never** spin up a replacement studio, video engine, game, or control room.

## Fixed contract

1. Observe **current main HEAD**, working branch exact head and merge-base; name source asset, owner, rights/approval, route and existing tests. Reject stale evidence.
2. **Generate/reference → inspect → implement → render → compare → correct → verify.** Build in the existing renderer. Preserve the actual gameplay, scene timing, source work and approved visual fingerprint.
3. Keep **reference art**, **local generated composite**, **motion video**, **live software screenshot**, and **hardware 3D evidence** separate; do not mislabel a poster/background as GPU-rendered gameplay or a video as a recorded product demo.
4. Produce SHA-256/provenance/continuity evidence where the current pipeline supports it. Byte matching proves matching bytes, **not** copyright permission, a trusted creator, live motion, GPU performance, or publishing authority.
5. Verify the focused tests first; for interactive surfaces, run real desktop + mobile Playwright, inspect uncaught JS/console errors, asset loading, readable controls and a gameplay/shot flow. If hardware WebGL is unavailable, mark it BLOCKED and identify fallback proof independently.
6. Never silently merge/deploy/publish, incur paid model charges, override approved graphics, invent current performance or create duplicate PRs. Existing approvals do not replace fresh exact-head release gates.

## Reality/provenance receipt

Return **REALITY / FIX / PROOF / RISK / ROLLBACK / NEXT GATE** with main SHA, branch SHA, changed paths, asset hashes, actual screenshots and unresolved release gates. Source image ≠ runtime evidence.

## This repository: IMAGE producer

- `demo.py` creates local PNG composites and `makeimage/local-composite/v1` receipts, optionally using approved creator-owned reference images. This is not a hosted generative-image service.
- `export_makevideo.py` (current handoff branch) verifies PNG size/dimensions/SHA-256 and the `VERIFIED_LOCAL_RENDER` receipt, then writes a standalone `makevideo/storyboard/v1` JSON. It does not overwrite inputs or authorize publishing.
- Workflow: inspect reference → render PNG+receipt → SHA-check → export storyboard → import downstream through MakeVideo's existing verifier → preview/render proof. Do not rename schemas or invent rights metadata.
- Focused proof: `python -m unittest discover -s tests -v`. Review `tests/test_demo.py` and `tests/test_handoff.py` before touching exports.
- Camera framing, depth, light and palette are acceptance criteria, not claims that a still image is animated 3D.
