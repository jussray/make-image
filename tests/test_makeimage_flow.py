import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from src.makeimage_flow import render, digest

class MakeImageFlowTest(unittest.TestCase):
    def test_renders_true_png_and_byte_bound_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'actual.png'
            image, receipt=render(out,title='REAL OUTPUT')
            with Image.open(image) as im:
                self.assertEqual(im.format,'PNG')
                self.assertEqual(im.size,(1280,720))
            data=json.loads(receipt.read_text())
            self.assertEqual(data['sha256'],digest(out))
            self.assertEqual(data['truth_class'],'ILLUSTRATIVE')
            self.assertFalse(data['authority_granted'])
            self.assertTrue(data['not_ai_generated'])

    def test_unlicensed_sources_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'photo.png'
            Image.new('RGB',(40,40),'blue').save(source)
            with self.assertRaises(PermissionError):
                render(Path(directory)/'out.png',source=source)

    def test_licensed_photo_composites_and_records_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'photo.png'
            Image.new('RGB',(40,40),'blue').save(source)
            out,receipt=render(Path(directory)/'out.png',source=source,licensed_source=True)
            self.assertEqual(json.loads(receipt.read_text())['source_sha256'],digest(source))
            self.assertTrue(out.exists())

    def test_refuses_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            render('invalid.png',width=10)
