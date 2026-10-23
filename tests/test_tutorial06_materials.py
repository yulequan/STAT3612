"""Publication checks for the self-contained Tutorial 06 teaching assets."""
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from package_student import package

FOLDER = ROOT / 'src/tutorials/tutorial06'


class Tutorial06MaterialsTests(unittest.TestCase):
    def test_assets_and_complete_student_package(self):
        manifest = json.loads((FOLDER / 'tutorial.json').read_text())
        self.assertEqual(manifest['python_packages'], [])
        self.assertEqual(manifest['web_assets'], ['time_series_slides.pdf'])
        self.assertEqual(set(manifest['student_files']), {
            'time_series_slides.pdf', 'time_series_tutorial.ipynb', 'requirements.txt', 'README.md',
        })
        self.assertTrue((FOLDER / 'time_series_slides.pdf').read_bytes().startswith(b'%PDF-'))
        with ZipFile(package(FOLDER)) as archive:
            self.assertEqual(set(archive.namelist()), set(manifest['student_files']))
            for name in manifest['student_files']:
                self.assertEqual(archive.read(name), (FOLDER / name).read_bytes())
            self.assertIn('statsmodels', archive.read('requirements.txt').decode())
            self.assertIn('python -m pip install -r requirements.txt',
                          archive.read('README.md').decode())

    def test_notebook_preserves_readable_outputs(self):
        notebook = json.loads((FOLDER / 'time_series_tutorial.ipynb').read_text())
        self.assertEqual(notebook['nbformat'], 4)
        cells = [cell for cell in notebook['cells'] if cell['cell_type'] == 'code']
        self.assertEqual(len(cells), 33)
        self.assertTrue(all(isinstance(cell['execution_count'], int) for cell in cells))
        outputs = [output for cell in cells for output in cell['outputs']]
        self.assertFalse(any(output['output_type'] == 'error' for output in outputs))
        self.assertEqual(sum('image/png' in output.get('data', {}) for output in outputs), 14)


if __name__ == '__main__':
    unittest.main()
