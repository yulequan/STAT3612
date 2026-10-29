"""Publication checks for the Tutorial 07 midterm-review deck."""
import json
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from package_student import package

FOLDER = ROOT / 'src/tutorials/tutorial07'
DECK = FOLDER / 'midterm_review_slides.pdf'


def inflated_streams(pdf):
    """Yield every Flate-compressed stream, including compressed object streams."""
    for match in re.finditer(rb'stream\r?\n', pdf):
        end = pdf.find(b'endstream', match.end())
        try:
            yield zlib.decompress(pdf[match.end():end].rstrip(b'\r\n'))
        except zlib.error:
            continue


class Tutorial07MaterialsTests(unittest.TestCase):
    def test_assets_and_complete_student_package(self):
        manifest = json.loads((FOLDER / 'tutorial.json').read_text())
        self.assertEqual(manifest['python_packages'], [])
        self.assertEqual(manifest['web_assets'], ['midterm_review_slides.pdf'])
        self.assertEqual(set(manifest['student_files']), {'midterm_review_slides.pdf', 'README.md'})
        self.assertTrue(DECK.read_bytes().startswith(b'%PDF-'))
        with ZipFile(package(FOLDER)) as archive:
            self.assertEqual(set(archive.namelist()), set(manifest['student_files']))
            for name in manifest['student_files']:
                self.assertEqual(archive.read(name), (FOLDER / name).read_bytes())
            readme = archive.read('README.md').decode()
            self.assertIn('33 slides', readme)
            self.assertIn('no speaker notes', readme)

    def test_publishes_the_slide_only_widescreen_build(self):
        streams = list(inflated_streams(DECK.read_bytes()))
        # 33 numbered slides reveal their answers one page at a time. The tutor's
        # presenter copy doubles every page with a script page; this build does not.
        pages = sum(len(re.findall(rb'/Type\s*/Page\b(?!s)', stream)) for stream in streams)
        self.assertEqual(pages, 69)
        boxes = {box for stream in streams for box in re.findall(rb'/MediaBox \[([^\]]+)\]', stream)}
        self.assertEqual(boxes, {b'0 0 453.543 255.118'})
        width, height = (float(value) for value in boxes.pop().split()[-2:])
        self.assertAlmostEqual(width / height, 16 / 9, places=2)


if __name__ == '__main__':
    unittest.main()
