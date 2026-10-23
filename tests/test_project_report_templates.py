"""Validate the public report templates without office/TeX dependencies in CI."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('report_templates', ROOT / 'scripts/build_report_templates.py')
templates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(templates)
NS = {'w': templates.W}


class ReportTemplateTests(unittest.TestCase):
    def test_downloads_match_reproducible_generator(self):
        with TemporaryDirectory() as temporary:
            templates.build(Path(temporary))
            for name in ('report-template.tex', 'report-template.docx'):
                self.assertEqual((templates.DESTINATION / name).read_bytes(),
                                 (Path(temporary) / name).read_bytes())

    def test_word_structure_contributions_and_matching_sections(self):
        with ZipFile(templates.DESTINATION / 'report-template.docx') as archive:
            for name in archive.namelist():
                ET.fromstring(archive.read(name))
            root = ET.fromstring(archive.read('word/document.xml'))
            styles = ET.fromstring(archive.read('word/styles.xml'))
        body = root.find('w:body', NS)
        elements = list(body)
        table_index = next(i for i, element in enumerate(elements) if element.tag == f'{{{templates.W}}}tbl')
        rows = elements[table_index].findall('w:tr', NS)

        def text(node):
            return ''.join(node.itertext())

        self.assertEqual([text(cell) for cell in rows[0].findall('w:tc', NS)], list(templates.HEADERS))
        shares = [int(text(row.findall('w:tc', NS)[3]).rstrip('%')) for row in rows[1:-1]]
        self.assertEqual(len(shares), 5)
        self.assertEqual(sum(shares), 100)
        self.assertEqual(text(rows[-1].findall('w:tc', NS)[3]), '100%')
        self.assertIn('Percentages must total exactly 100%.', text(root))
        self.assertIn('four-person group', text(root))

        for index, (title, _) in enumerate(templates.SECTIONS, start=1):
            heading_index = next(i for i, element in enumerate(elements) if text(element) == f'{index}. {title}')
            self.assertGreater(heading_index, table_index)
        self.assertEqual(styles.find('.//w:rFonts', NS).get(f'{{{templates.W}}}ascii'), 'Times New Roman')
        self.assertEqual(styles.find('.//w:sz', NS).get(f'{{{templates.W}}}val'), '22')
        self.assertEqual(root.find('.//w:pgSz', NS).get(f'{{{templates.W}}}w'), '11906')
        margins = root.find('.//w:pgMar', NS)
        for edge in ('top', 'bottom', 'left', 'right'):
            self.assertEqual(margins.get(f'{{{templates.W}}}{edge}'), '1417')

    def test_latex_layout_and_contribution_table_precede_report_sections(self):
        source = (templates.DESTINATION / 'report-template.tex').read_text()
        self.assertIn(r'\documentclass[11pt,a4paper]{article}', source)
        self.assertIn(r'\usepackage[margin=25mm]{geometry}', source)
        self.assertIn(r'Percentages must total exactly 100\%.', source)
        self.assertEqual(source.count(r'20\%'), 5)
        self.assertEqual(source.count(r'\url{[HKU-email]}'), 5)
        self.assertIn(r'\urlstyle{same}', source)
        end = source.index(r'\end{tabularx}')
        for title, _ in templates.SECTIONS:
            self.assertGreater(source.index(f'\\section{{{title}}}'), end)


if __name__ == '__main__':
    unittest.main()
