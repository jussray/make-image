"""Regression coverage for MakeImage -> MakeVideo local-only asset handoff."""
import json
from pathlib import Path
import tempfile
import unittest

from demo import render, sha256
from export_makevideo import HandoffError, export_storyboard


class MakeVideoHandoffTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.image = self.root / "image.png"
        self.receipt = self.root / "receipt.json"
        self.out = self.root / "storyboard.json"
        render(self.image, self.receipt, title="Original work", subtitle="Local composite",
               width=640, height=360)
        self.source_digest = sha256(self.image)

    def test_exports_portable_storyboard_without_modifying_inputs(self):
        result = export_storyboard(self.image, self.receipt, self.out,
                                   title="Juss scene", aspect="9:16")
        self.assertEqual(result["schema"], "makevideo/storyboard/v1")
        self.assertFalse(result["publication_authorized"])
        doc = json.loads(self.out.read_text())
        self.assertEqual(doc["format"], "9:16")
        self.assertEqual(doc["title"], "Juss scene")
        self.assertEqual(len(doc["shots"]), 1)
        self.assertTrue(doc["shots"][0]["imageData"].startswith("data:image/jpeg;base64,"))
        self.assertLessEqual(len(doc["shots"][0]["imageData"]), 105_000)
        self.assertIn(self.source_digest, doc["shots"][0]["continuity"])
        self.assertNotIn(str(self.root), self.out.read_text())
        self.assertEqual(self.source_digest, sha256(self.image))

    def test_rejects_modified_png_and_preserves_target(self):
        with self.image.open("ab") as target:
            target.write(b"modified")
        with self.assertRaisesRegex(HandoffError, "do not match"):
            export_storyboard(self.image, self.receipt, self.out)
        self.assertFalse(self.out.exists())

    def test_rejects_unsupported_proof_and_missing_authority_boundary(self):
        receipt = json.loads(self.receipt.read_text())
        receipt["state"] = "PUBLISHED"
        self.receipt.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(HandoffError, "unverified"):
            export_storyboard(self.image, self.receipt, self.out)
        self.assertFalse(self.out.exists())

    def test_never_overwrites_existing_file_or_inputs(self):
        self.out.write_text("keep this", encoding="utf-8")
        with self.assertRaisesRegex(HandoffError, "overwrite"):
            export_storyboard(self.image, self.receipt, self.out)
        self.assertEqual(self.out.read_text(), "keep this")
        with self.assertRaisesRegex(HandoffError, "distinct"):
            export_storyboard(self.image, self.receipt, self.receipt)

    def test_rejects_wrong_dimensions_and_invalid_titles(self):
        receipt = json.loads(self.receipt.read_text())
        receipt["output"]["width"] = 999
        self.receipt.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(HandoffError, "dimensions"):
            export_storyboard(self.image, self.receipt, self.out)
        with self.assertRaisesRegex(HandoffError, "title"):
            export_storyboard(self.image, self.receipt, self.out, title="")


if __name__ == "__main__":
    unittest.main()
