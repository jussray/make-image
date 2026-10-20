import json
import tempfile
import unittest
from pathlib import Path
import sys
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from demo import ImageFlowError,render,sha256

class ImageProductionTest(unittest.TestCase):
    def test_output_is_real_png_with_provenance(self):
        with tempfile.TemporaryDirectory() as work:
            root=Path(work)
            png, receipt=root/'image.png',root/'receipt.json'
            result=render(png,receipt,title='Cinematic proof',subtitle='Local image',width=640,height=360)
            with Image.open(png) as image:
                self.assertEqual(image.size,(640,360))
                self.assertEqual(image.format,'PNG')
                self.assertNotEqual(image.getpixel((20,20)),image.getpixel((400,120)))
            self.assertEqual(result['output']['sha256'],sha256(png))
            self.assertEqual(result['state'],'VERIFIED_LOCAL_RENDER')
            self.assertFalse(json.loads(receipt.read_text())['continuity_cookie']['publish_authority'])
            with self.assertRaises(ImageFlowError):render(png,receipt,title='Other',subtitle='Other',width=640,height=360)

    def test_reference_never_mutated_and_bad_paths_fail_closed(self):
        with tempfile.TemporaryDirectory() as work:
            root=Path(work)
            source=root/'source.png'
            Image.new('RGB',(120,90),(200,60,90)).save(source)
            checksum=sha256(source)
            result=render(root/'output.png',root/'receipt.json',reference=source,title='Verified photo',subtitle='',width=640,height=360)
            self.assertEqual(sha256(source),checksum)
            self.assertEqual(result['reference']['sha256'],checksum)
            with self.assertRaises(ImageFlowError):render(source,root/'new.json',reference=source,title='Bad',subtitle='',width=640,height=360)

if __name__=='__main__':unittest.main()