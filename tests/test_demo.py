import json
import base64
import io
import tempfile
import unittest
from pathlib import Path
import sys
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from demo import ImageFlowError,render,sha256,load_brand_qr,storyboard_frame,BRAND_DESTINATION

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

    def test_oversized_brand_claim_fails_closed_without_clipping(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            png, receipt = root/'image.png', root/'receipt.json'
            with self.assertRaisesRegex(ImageFlowError, 'cannot fit safely'):
                render(png,receipt,title='W'*100,subtitle='',width=640,height=360)
            self.assertFalse(png.exists())
            self.assertFalse(receipt.exists())

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


    def test_first_party_branding_is_real_png_pixels_and_source_bound(self):
        with tempfile.TemporaryDirectory() as work:
            root=Path(work)
            output, receipt=root/'brand.png',root/'brand.json'
            result=render(output,receipt,title='Branded',subtitle='Real pixels',
                          width=640,height=360,watermark=True,qr=True)
            qr, digest=load_brand_qr()
            self.assertEqual(qr.size,(41,41))
            self.assertEqual(result['branding']['qr_asset_sha256'],digest)
            self.assertEqual(result['branding']['destination'],BRAND_DESTINATION)
            self.assertTrue(result['branding']['watermark'])
            self.assertFalse(result['continuity_cookie']['publish_authority'])
            with Image.open(output) as image:
                self.assertEqual(image.getpixel((464,21)),(255,255,255))  # quiet zone
                self.assertEqual(image.getpixel((477,34)),(16,11,40))  # known QR module
            with self.assertRaises(ImageFlowError):
                render(output,receipt,title='Cannot overwrite',subtitle='',
                       width=640,height=360,watermark=True,qr=True)

    def test_makevideo_storyboard_shot_becomes_original_image_keyframe(self):
        with tempfile.TemporaryDirectory() as work:
            root=Path(work)
            reference=Image.new('RGB',(200,150),(245,32,50))
            memory=io.BytesIO()
            reference.save(memory,format='JPEG')
            storyboard=root/'creator-storyboard.json'
            storyboard.write_text(json.dumps({
                'schema':'makevideo/storyboard/v1','title':'Creator project',
                'format':'16:9',
                'shots':[{'title':'First shot','caption':'Story in motion',
                          'imageData':'data:image/jpeg;base64,'+
                              base64.b64encode(memory.getvalue()).decode('ascii')}] }))
            original_sha=sha256(storyboard)
            info, embedded=storyboard_frame(storyboard,1)
            self.assertEqual(info['title'],'Story in motion')
            self.assertIsNotNone(embedded)
            output,receipt=root/'keyframe.png',root/'keyframe.json'
            result=render(output,receipt,title=info['title'],subtitle=info['subtitle'],
                          width=640,height=360,qr=True,storyboard=info,embedded_image=embedded)
            self.assertEqual(result['storyboard']['sha256'],original_sha)
            self.assertEqual(sha256(storyboard),original_sha)
            with Image.open(output) as image:
                self.assertGreater(image.getpixel((10,200))[0],200)
                self.assertLess(image.getpixel((10,200))[1],80)
            with self.assertRaisesRegex(ImageFlowError,'shot count or shot index'):
                storyboard_frame(storyboard,2)
            with self.assertRaisesRegex(ImageFlowError,'Source storyboard'):
                render(storyboard,root/'different.json',title='Bad',subtitle='Bad',
                       width=640,height=360,storyboard=info)

if __name__=='__main__':unittest.main()