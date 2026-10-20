import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from visual_experience import render_manifest, validate, digest

FIXTURE = {
  'schema': 'jussco/visual-experience/v1',
  'kind': 'architecture',
  'title': 'Juss & Co product boundaries',
  'items': [
    {'id': 'fcr', 'title': 'Founder Control Room', 'summary': 'Independent evidence and approval authority; source inspected, runtime separate.', 'state': 'VERIFIED_SOURCE'},
    {'id': 'sol', 'title': 'SolContinuity', 'summary': 'Independent continuity and recovery provider.', 'state': 'UNKNOWN'},
  ],
  'edges': [{'from': 'fcr', 'to': 'sol', 'label': 'Declared bounded evidence handoff'}]
}

class VisualExperienceTest(unittest.TestCase):
    def test_architecture_emits_real_png_and_non_authorizing_receipt(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            manifest=root/'experience.json'
            manifest.write_text(json.dumps(FIXTURE))
            png=root/'map.png'
            receipt=root/'proof.json'
            proof=render_manifest(manifest,png,receipt)
            self.assertEqual(proof['output']['sha256'],digest(png))
            with Image.open(png) as image:
                self.assertEqual(image.format,'PNG')
                self.assertEqual(image.size[0],1440)
                self.assertNotEqual(image.getpixel((100,300)),image.getpixel((720,800)))
            self.assertFalse(json.loads(receipt.read_text())['claims']['publish_approved'])
            self.assertFalse(json.loads(receipt.read_text())['claims']['github_verified'])
            with self.assertRaisesRegex(ValueError,'Existing output'):
                render_manifest(manifest,png,receipt)

    def test_rejects_fake_evidence_and_bad_edges(self):
        bad=json.loads(json.dumps(FIXTURE))
        bad['items'][0]['state']='PRODUCTION_VERIFIED'
        with self.assertRaisesRegex(ValueError,'evidence state'):
            validate(bad)
        bad=json.loads(json.dumps(FIXTURE))
        bad['edges'][0]['to']='missing'
        with self.assertRaisesRegex(ValueError,'Edge endpoints'):
            validate(bad)

    def test_canon_requires_real_screenshots_and_preserves_sources(self):
        with tempfile.TemporaryDirectory() as dirname:
            root=Path(dirname)
            m=json.loads(json.dumps(FIXTURE));m['kind']='canon';m['title']='Source screenshot parity'
            manifest=root/'canon.json';manifest.write_text(json.dumps(m))
            old, new=root/'before.png',root/'after.png'
            Image.new('RGB',(400,300),(10,25,70)).save(old)
            Image.new('RGB',(400,300),(20,70,80)).save(new)
            before_hash,after_hash=digest(old),digest(new)
            with self.assertRaisesRegex(ValueError,'requires explicit'):
                render_manifest(manifest,root/'missing.png',root/'missing.json')
            proof=render_manifest(manifest,root/'compare.png',root/'compare.json',before=old,after=new)
            self.assertEqual(proof['input']['before_sha256'],before_hash)
            self.assertEqual(digest(old),before_hash)
            self.assertEqual(digest(new),after_hash)

    def test_playtest_labels_do_not_assert_real_play(self):
        with tempfile.TemporaryDirectory() as dirname:
            root=Path(dirname)
            m=json.loads(json.dumps(FIXTURE));m['kind']='playtest';m['title']='Actual code flow, untested runtime'
            path=root/'flow.json';path.write_text(json.dumps(m))
            proof=render_manifest(path,root/'flow.png',root/'flow.receipt.json')
            self.assertFalse(proof['claims']['runtime_verified'])

if __name__=='__main__':unittest.main()