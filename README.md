# make-image

## Local working image flow (feature branch)

The source in `src/makeimage_flow.py` creates an **actual 1280×720 PNG** using Pillow, with an image SHA-256 and JSON receipt. This is deterministic visual composition, **not an AI image-generation service**. Model providers and production delivery remain separate, unverified integrations.

```sh
python -m pip install -r requirements.txt
python demo.py --output output/makeimage-demo.png
# Optional source-photo composition: confirm you have usage rights
python demo.py --input own-photo.png --licensed-source --output output/photo-card.png
python -m unittest discover -s tests -v
node --experimental-strip-types --test src/character-reference.test.ts
```

The source-photo flow requires `--licensed-source` and records a source hash. Consent evidence references are mandatory in the TypeScript character selector for adult likeness assets, but **only their presence** is checked, not authenticity. Composed examples carry `ILLUSTRATIVE` truth state; generated media never grants approval or publishing authority. Branch changes are pending independent review and CI readback.
